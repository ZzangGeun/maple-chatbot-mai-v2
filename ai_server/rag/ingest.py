# ai_server/rag/ingest.py
"""
RAG 지식 베이스 수집·적재 파이프라인

    python -m ai_server.rag.ingest                          # 공략 문서 + 넥슨 공지
    python -m ai_server.rag.ingest --sources guides         # 공략 문서만
    python -m ai_server.rag.ingest --include-drafts         # 검토 전 공략 문서도 적재 (개발용)
    python -m ai_server.rag.ingest --dry-run                # DB 없이 문서·청크 수만 확인

문서마다 내용 해시를 비교해 바뀐 문서만 다시 임베딩합니다.
  - 공략 문서·JSON 자료: 폴더에서 사라진 문서는 인덱스에서도 지웁니다.
  - 공지: 새 공지만 추가하고, 목록에서 밀려난 공지는 그대로 둡니다.
doc_id 없이 예전 방식으로 적재된 청크(캐릭터 정보, 예전 공지 JSON)는 실행할 때마다 지웁니다.
"""

import argparse
import asyncio
import logging
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from ai_server.config import BASE_DIR, settings
from ai_server.rag.documents import SourceDocument, split_document
from ai_server.rag.index import ChunkIndex, InMemoryIndex
from ai_server.rag.sources import fetch_notices, load_guides, load_json_files
from common.nexon import NexonClient

logger = logging.getLogger(__name__)

SOURCES = ("guides", "notices", "json")
DEFAULT_SOURCES = ("guides", "notices")
JSON_DIR = BASE_DIR / "data" / "rag_documents"


@dataclass
class IngestReport:
    added: int = 0
    updated: int = 0
    unchanged: int = 0
    deleted: int = 0
    legacy_removed: int = 0
    chunks: int = 0

    def __str__(self) -> str:
        return (
            f"추가 {self.added} · 갱신 {self.updated} · 변경 없음 {self.unchanged} · 삭제 {self.deleted} "
            f"· 예전 청크 삭제 {self.legacy_removed} · 적재한 청크 {self.chunks}"
        )


def sync_documents(
    index: ChunkIndex,
    documents: Iterable[SourceDocument],
    *,
    prune_prefix: str | None = None,
    report: IngestReport | None = None,
) -> IngestReport:
    """문서를 인덱스에 반영합니다.

    prune_prefix를 주면 그 접두사의 문서 중 이번 목록에 없는 문서를 인덱스에서 지웁니다.
    """
    report = report or IngestReport()
    existing = index.doc_hashes()
    current_ids: set[str] = set()

    for doc in documents:
        if doc.doc_id in current_ids:
            logger.warning(f"중복된 문서 ID를 건너뜁니다: {doc.doc_id}")
            continue
        current_ids.add(doc.doc_id)

        previous_hash = existing.get(doc.doc_id)
        if previous_hash == doc.content_hash:
            report.unchanged += 1
            continue

        if previous_hash is None:
            report.added += 1
        else:
            # 청크 수가 줄었을 때 남는 청크가 없도록 문서 단위로 지우고 다시 넣습니다.
            index.delete_docs([doc.doc_id])
            report.updated += 1

        chunks = split_document(doc)
        if chunks:
            index.add_chunks(chunks)
            report.chunks += len(chunks)

    if prune_prefix:
        stale = [doc_id for doc_id in existing if doc_id.startswith(prune_prefix) and doc_id not in current_ids]
        index.delete_docs(stale)
        report.deleted += len(stale)

    return report


async def run_ingestion(
    index: ChunkIndex,
    sources: Iterable[str] = DEFAULT_SOURCES,
    *,
    include_drafts: bool | None = None,
    nexon_client: NexonClient | None = None,
) -> IngestReport:
    """선택한 소스를 수집해 인덱스에 반영합니다. (임베딩·DB 작업은 스레드에서 실행)"""
    sources = set(sources)
    unknown = sources - set(SOURCES)
    if unknown:
        raise ValueError(f"알 수 없는 소스: {sorted(unknown)} (사용 가능: {', '.join(SOURCES)})")
    if include_drafts is None:
        include_drafts = settings.rag.include_draft_guides

    report = IngestReport()
    report.legacy_removed = await asyncio.to_thread(index.delete_legacy)

    if "guides" in sources:
        guides = load_guides(Path(settings.rag.guides_dir), include_drafts=include_drafts)
        await asyncio.to_thread(sync_documents, index, guides, prune_prefix="guide:", report=report)

    if "json" in sources:
        json_docs = load_json_files(JSON_DIR)
        await asyncio.to_thread(sync_documents, index, json_docs, prune_prefix="json:", report=report)

    if "notices" in sources:
        client = nexon_client or NexonClient(settings.api.nexon_api_key)
        known = set(await asyncio.to_thread(index.doc_hashes))
        notices = await fetch_notices(client, settings.rag.notice_limit, known_doc_ids=known)
        await asyncio.to_thread(sync_documents, index, notices, report=report)

    logger.info(f"지식 베이스 적재 완료: {report}")
    return report


async def run_scheduled_ingestion() -> None:
    """주기 작업용: 운영 인덱스에 공략 문서와 공지를 반영합니다. 실패해도 예외를 밖으로 내지 않습니다."""
    from ai_server.rag.vectorstore import get_index

    try:
        await run_ingestion(get_index())
    except Exception:
        logger.exception("지식 베이스 정기 적재 실패")


def main() -> None:
    parser = argparse.ArgumentParser(description="RAG 지식 베이스 수집·적재")
    parser.add_argument(
        "--sources",
        default=",".join(DEFAULT_SOURCES),
        help=f"적재할 소스 (쉼표 구분, 사용 가능: {', '.join(SOURCES)})",
    )
    parser.add_argument("--include-drafts", action="store_true", help="검토 전(draft) 공략 문서도 적재")
    parser.add_argument("--dry-run", action="store_true", help="DB·API 없이 공략 문서와 JSON 자료의 문서·청크 수만 확인")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    sources = [s.strip() for s in args.sources.split(",") if s.strip()]

    if args.dry_run:
        offline = [s for s in sources if s != "notices"]
        if "notices" in sources:
            logger.info("--dry-run에서는 넥슨 API를 호출하지 않으므로 공지는 건너뜁니다.")
        report = asyncio.run(run_ingestion(InMemoryIndex(), offline, include_drafts=args.include_drafts))
    else:
        from ai_server.rag.vectorstore import get_index

        report = asyncio.run(run_ingestion(get_index(), sources, include_drafts=args.include_drafts))

    print(report)


if __name__ == "__main__":
    main()
