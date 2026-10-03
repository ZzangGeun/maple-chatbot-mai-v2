# tests/test_rag_pipeline.py
"""
RAG 지식 베이스 파이프라인 테스트 (LLM·DB·외부 API 호출 없음)

- 공략 문서 읽기, 청킹, 증분 적재(추가·갱신·삭제)
- 넥슨 공지 수집(가짜 클라이언트)과 HTML 정제
- 하이브리드 검색(RRF), 시점 질문 처리, 키워드 검색 품질 기준선
"""

from datetime import date
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai_server.graph.nodes.rag_nodes import format_documents
from ai_server.rag.documents import Chunk, SourceDocument, split_document
from ai_server.rag.evaluation.retrieval_eval import build_memory_retriever, evaluate, load_testset
from ai_server.rag.index import InMemoryIndex
from ai_server.rag.ingest import run_ingestion, sync_documents
from ai_server.rag.retriever import HybridRetriever, is_time_sensitive
from ai_server.rag.sources import fetch_notices, html_to_text, load_guides, load_json_files
from ai_server.rag.tokenizer import tokenize
from common.exceptions.nexon import NexonApiError

GUIDE = """---
id: sample
title: 샘플 가이드
category: guide
status: {status}
updated: 2026-10-01
aliases: [샘플, 예시]
sources:
  - https://example.com/guide
---

도입 문단입니다.

## 첫 번째 섹션
첫 번째 섹션 본문입니다.

## 두 번째 섹션
두 번째 섹션 본문입니다.
"""


def _write_guide(directory: Path, name: str, status: str = "reviewed", body: str = GUIDE) -> Path:
    path = directory / f"{name}.md"
    path.write_text(body.format(status=status).replace("id: sample", f"id: {name}"), encoding="utf-8")
    return path


def _doc(doc_id: str, content: str = "본문", **kwargs) -> SourceDocument:
    return SourceDocument(
        doc_id=doc_id,
        title=kwargs.pop("title", doc_id),
        content=content,
        category=kwargs.pop("category", "guide"),
        source_type="guide",
        **kwargs,
    )


# ---------------------------------------------------------------------------
# 공략 문서와 청킹
# ---------------------------------------------------------------------------


def test_load_guides_skips_drafts_unless_requested(tmp_path: Path) -> None:
    _write_guide(tmp_path, "reviewed-doc")
    _write_guide(tmp_path, "draft-doc", status="draft")
    (tmp_path / "README.md").write_text("# 머리말 없는 문서", encoding="utf-8")

    reviewed = load_guides(tmp_path)
    everything = load_guides(tmp_path, include_drafts=True)

    assert [d.doc_id for d in reviewed] == ["guide:reviewed-doc"]
    assert sorted(d.doc_id for d in everything) == ["guide:draft-doc", "guide:reviewed-doc"]
    doc = reviewed[0]
    assert doc.title == "샘플 가이드"
    assert doc.url == "https://example.com/guide"
    assert doc.date == "2026-10-01"
    assert doc.extra["aliases"] == ["샘플", "예시"]


def test_split_document_keeps_section_context() -> None:
    doc = SourceDocument(
        doc_id="guide:sample",
        title="샘플 가이드",
        content="도입 문단입니다.\n\n## 첫 번째 섹션\n첫 본문\n\n## 두 번째 섹션\n" + "긴 본문. " * 200,
        category="guide",
        source_type="guide",
        extra={"aliases": ["샘플"], "status": "reviewed"},
    )

    chunks = split_document(doc)

    assert chunks[0].chunk_id == "guide:sample#0"
    assert chunks[0].text.startswith("[샘플 가이드]\n(관련어: 샘플)")
    assert chunks[1].text.startswith("[샘플 가이드 > 첫 번째 섹션]")
    # 긴 섹션은 여러 청크로 나뉘지만 모두 섹션 머리말을 가집니다.
    long_section = [c for c in chunks if c.metadata["section"] == "두 번째 섹션"]
    assert len(long_section) > 1
    assert all(c.text.startswith("[샘플 가이드 > 두 번째 섹션]") for c in long_section)
    assert [c.metadata["chunk_index"] for c in chunks] == list(range(len(chunks)))
    assert chunks[0].metadata["content_hash"] == doc.content_hash
    assert "aliases" not in chunks[0].metadata


def test_content_hash_changes_with_metadata() -> None:
    assert _doc("a").content_hash == _doc("a").content_hash
    assert _doc("a").content_hash != _doc("a", content="바뀐 본문").content_hash
    assert _doc("a").content_hash != _doc("a", url="https://new").content_hash


# ---------------------------------------------------------------------------
# 증분 적재
# ---------------------------------------------------------------------------


def test_sync_documents_adds_updates_skips_and_prunes() -> None:
    index = InMemoryIndex()
    first = sync_documents(index, [_doc("guide:a"), _doc("guide:b"), _doc("notice:event:1")], prune_prefix="guide:")
    assert (first.added, first.chunks) == (3, 3)

    index.add_chunks = MagicMock(wraps=index.add_chunks)
    second = sync_documents(index, [_doc("guide:a"), _doc("guide:b", content="바뀐 본문")], prune_prefix="guide:")

    assert (second.added, second.updated, second.unchanged, second.deleted) == (0, 1, 1, 0)
    # 바뀐 문서만 다시 임베딩합니다.
    assert [c.doc_id for c in index.add_chunks.call_args.args[0]] == ["guide:b"]

    third = sync_documents(index, [_doc("guide:a")], prune_prefix="guide:")
    assert third.deleted == 1
    # 접두사가 다른 문서(공지)는 지우지 않습니다.
    assert set(index.doc_hashes()) == {"guide:a", "notice:event:1"}


def test_updated_document_does_not_leave_stale_chunks() -> None:
    index = InMemoryIndex()
    sync_documents(index, [_doc("guide:a", content="## 하나\n가\n## 둘\n나\n## 셋\n다")])
    assert len(index.all_chunks()) == 3

    sync_documents(index, [_doc("guide:a", content="## 하나\n가")])

    assert [c.chunk_id for c in index.all_chunks()] == ["guide:a#0"]


@pytest.mark.asyncio
async def test_run_ingestion_removes_legacy_chunks_and_rejects_unknown_source(tmp_path: Path, monkeypatch) -> None:
    from ai_server.config import settings

    _write_guide(tmp_path, "one")
    monkeypatch.setattr(settings.rag, "guides_dir", str(tmp_path))
    index = InMemoryIndex()
    index.legacy_count = 7

    report = await run_ingestion(index, ["guides"], include_drafts=False)

    assert report.legacy_removed == 7
    assert report.added == 1
    with pytest.raises(ValueError):
        await run_ingestion(index, ["characters"])


# ---------------------------------------------------------------------------
# 넥슨 공지·JSON 자료
# ---------------------------------------------------------------------------


def test_html_to_text_keeps_tables_and_line_breaks() -> None:
    html = (
        "<div><p>이벤트 안내<br>기간: 10월</p><script>x()</script>"
        "<table><tr><th>단계</th><th>보상</th></tr><tr><td>1</td><td>경험치&nbsp;쿠폰</td></tr></table></div>"
    )

    lines = [line for line in html_to_text(html).splitlines() if line]

    assert lines == ["이벤트 안내", "기간: 10월", "단계 | 보상", "1 | 경험치 쿠폰"]


@pytest.mark.asyncio
async def test_fetch_notices_skips_known_and_survives_failures() -> None:
    async def get_json(path: str, params: dict | None = None) -> dict:
        if path == "/notice":
            raise NexonApiError("점검 중")
        if path == "/notice-event":
            return {"event_notice": [{"notice_id": 1, "title": "새 이벤트"}, {"notice_id": 2, "title": "적재한 이벤트"}]}
        if path == "/notice-event/detail":
            return {
                "title": "새 이벤트",
                "url": "https://maplestory.nexon.com/News/Event/1",
                "contents": "<p>이벤트 본문</p>",
                "date": "2026-10-01T10:00+09:00",
                "date_event_start": "2026-10-01T10:00+09:00",
                "date_event_end": "2026-10-15T23:59+09:00",
            }
        return {}

    client = MagicMock()
    client.get_json = AsyncMock(side_effect=get_json)

    docs = await fetch_notices(client, known_doc_ids={"notice:event:2"})

    assert [d.doc_id for d in docs] == ["notice:event:1"]
    doc = docs[0]
    assert (doc.category, doc.content, doc.url) == ("event", "이벤트 본문", "https://maplestory.nexon.com/News/Event/1")
    assert doc.extra == {"period_start": "2026-10-01T10:00+09:00", "period_end": "2026-10-15T23:59+09:00"}
    # 이미 적재한 공지의 본문은 다시 요청하지 않습니다.
    detail_calls = [call for call in client.get_json.await_args_list if call.args[0].endswith("/detail")]
    assert len(detail_calls) == 1


def test_load_json_files_skips_character_and_ranking_data(tmp_path: Path) -> None:
    (tmp_path / "boss").mkdir()
    (tmp_path / "boss" / "index.json").write_text('{"boss_monsters": [{"name": "루시드", "icon": "x"}]}', encoding="utf-8")
    (tmp_path / "character").mkdir()
    (tmp_path / "character" / "someone.json").write_text("{}", encoding="utf-8")

    docs = load_json_files(tmp_path)

    assert [d.doc_id for d in docs] == ["json:boss/index.json"]
    assert "루시드" in docs[0].content and "icon" not in docs[0].content


# ---------------------------------------------------------------------------
# 토크나이저와 하이브리드 검색
# ---------------------------------------------------------------------------


def test_tokenizer_keeps_game_terms() -> None:
    tokens = tokenize("아케인심볼 레벨업하고 추옵 보공 챙겼어")
    assert {"아케인심볼", "추옵", "보공"} <= set(tokens)
    assert "고" not in tokens  # 어미는 버립니다.


def _chunk(chunk_id: str, text: str, **meta) -> Chunk:
    return Chunk(chunk_id=chunk_id, text=text, metadata={"doc_id": chunk_id.split("#")[0], **meta})


class _FakeIndex:
    def __init__(self, chunks: list[Chunk], vector_results: list[Chunk] | Exception) -> None:
        self._chunks = chunks
        self._vector = vector_results
        self.all_chunks_calls = 0

    def all_chunks(self) -> list[Chunk]:
        self.all_chunks_calls += 1
        return list(self._chunks)

    def vector_search(self, query: str, k: int) -> list[Chunk]:
        if isinstance(self._vector, Exception):
            raise self._vector
        return self._vector[:k]


def test_hybrid_search_merges_vector_and_keyword_results() -> None:
    starforce = _chunk("guide:starforce#0", "스타포스 강화와 파괴 방지")
    potential = _chunk("guide:potential#0", "잠재능력 등급과 큐브")
    union = _chunk("guide:union#0", "유니온 공격대원")
    # 벡터 검색은 잠재능력을, 키워드 검색은 스타포스를 1위로 줍니다. 둘 다 나온 문서가 가장 위로 옵니다.
    index = _FakeIndex([starforce, potential, union], vector_results=[potential, starforce])

    results = HybridRetriever(index).search("스타포스 파괴 방지", k=3)

    assert [c.chunk_id for c in results][:2] == ["guide:starforce#0", "guide:potential#0"]
    assert union not in results


def test_hybrid_search_falls_back_to_keywords_when_vector_search_fails() -> None:
    index = _FakeIndex([_chunk("guide:symbols#0", "아케인심볼 최대 레벨")], vector_results=RuntimeError("DB 장애"))

    results = HybridRetriever(index).search("아케인심볼 레벨")

    assert [c.chunk_id for c in results] == ["guide:symbols#0"]


def test_time_sensitive_query_drops_ended_events_and_boosts_recent() -> None:
    today = date(2026, 10, 10)
    ended = _chunk("notice:event:1#0", "이벤트 보상 안내", category="event", date="2026-08-01", period_start="2026-08-01", period_end="2026-08-31")
    ongoing = _chunk("notice:event:2#0", "이벤트 참여 방법", category="event", date="2026-09-01", period_start="2026-10-01", period_end="2026-10-30")
    old_guide = _chunk("guide:event-tips#0", "이벤트 보상 이벤트 보상 정리", category="guide", date="2025-01-01")
    index = _FakeIndex([ended, ongoing, old_guide], vector_results=[])
    retriever = HybridRetriever(index, today=lambda: today)

    assert is_time_sensitive("이번 이벤트 보상 뭐야?")
    current = retriever.search("이번 이벤트 보상 뭐야?")
    assert "notice:event:1#0" not in [c.chunk_id for c in current]
    assert current[0].chunk_id == "notice:event:2#0"

    # 시점을 묻지 않으면 끝난 이벤트도 검색됩니다.
    assert "notice:event:1#0" in [c.chunk_id for c in retriever.search("이벤트 보상")]


def test_keyword_index_refreshes_after_interval() -> None:
    index = _FakeIndex([_chunk("guide:a#0", "스타포스")], vector_results=[])
    retriever = HybridRetriever(index, refresh_seconds=3600)

    retriever.search("스타포스")
    retriever.search("스타포스")
    assert index.all_chunks_calls == 1

    index._chunks.append(_chunk("guide:b#0", "유니온"))
    retriever.refresh()
    assert [c.chunk_id for c in retriever.search("유니온")] == ["guide:b#0"]


def test_format_documents_groups_chunks_by_document() -> None:
    chunks = [
        _chunk("guide:starforce#2", "[스타포스 > 파괴 방지] 내용 B", title="스타포스 강화 가이드", category="guide", chunk_index=2, url="https://x"),
        _chunk("notice:event:9#0", "이벤트 본문", title="샤이닝 스타포스", category="event", date="2026-10-01T10:00+09:00", period_start="2026-10-01", period_end="2026-10-15"),
        _chunk("guide:starforce#0", "[스타포스 > 개요] 내용 A", title="스타포스 강화 가이드", category="guide", chunk_index=0, url="https://x"),
    ]

    context, sources = format_documents(chunks)

    assert [(s["index"], s["title"]) for s in sources] == [(1, "스타포스 강화 가이드"), (2, "샤이닝 스타포스")]
    # 같은 문서의 청크는 원래 순서대로 한 번호 아래 모읍니다.
    assert context.index("내용 A") < context.index("내용 B") < context.index("[2] 샤이닝 스타포스")
    assert "- 분류: 이벤트" in context
    assert "- 기간: 2026-10-01 ~ 2026-10-15" in context


def test_format_documents_keeps_context_within_budget(monkeypatch: pytest.MonkeyPatch) -> None:
    from ai_server.graph.nodes import rag_nodes

    monkeypatch.setattr(rag_nodes, "MAX_CONTEXT_CHARS", 300)
    chunks = [_chunk(f"guide:doc{i}#0", "가" * 200, title=f"문서{i}") for i in range(1, 4)]

    context, sources = format_documents(chunks)

    assert len(context) <= 300
    assert [s["title"] for s in sources] == ["문서1"]


# ---------------------------------------------------------------------------
# 검색 품질 기준선
# ---------------------------------------------------------------------------


def test_keyword_retrieval_quality_on_guides() -> None:
    """공략 문서와 평가셋으로 키워드 검색 품질을 확인합니다. (임베딩 없이 측정 가능한 하한선)"""
    result = evaluate(build_memory_retriever(), load_testset(), k=5)

    assert result.total >= 50
    assert result.hit_at_k >= 0.9, result.misses
    assert result.mrr >= 0.8
