# ai_server/rag/sources.py
"""
RAG 지식 베이스 수집 소스

  - 공략 문서  : knowledge/guides/*.md (YAML 머리말 + 마크다운, 검토된 문서만 기본 적재)
  - 넥슨 공지  : 넥슨 Open API의 공지·업데이트·이벤트·캐시샵 공지 본문 (HTML → 텍스트)
  - JSON 자료  : data/rag_documents의 보스·직업 목록 같은 로컬 JSON (있을 때만)

랭킹처럼 자주 바뀌는 데이터와 캐릭터 정보는 지식 베이스에 넣지 않습니다.
(캐릭터 정보는 질문할 때 넥슨 API에서 실시간으로 조회합니다)
"""

import json
import logging
import re
from pathlib import Path
from typing import Any

import yaml
from bs4 import BeautifulSoup

from ai_server.rag.documents import SourceDocument
from common.exceptions.base import AppException
from common.nexon import NexonClient

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 공략 문서
# ---------------------------------------------------------------------------

_FRONT_MATTER = re.compile(r"\A---\s*\n(.*?)\n---\s*\n(.*)\Z", re.DOTALL)


def parse_guide(path: Path) -> SourceDocument | None:
    """머리말이 있는 마크다운 공략 문서를 읽습니다. 머리말이 없으면 None."""
    match = _FRONT_MATTER.match(path.read_text(encoding="utf-8"))
    if not match:
        return None

    meta: dict[str, Any] = yaml.safe_load(match.group(1)) or {}
    guide_id = meta.get("id") or path.stem
    sources = meta.get("sources") or []
    return SourceDocument(
        doc_id=f"guide:{guide_id}",
        title=meta.get("title") or path.stem,
        content=match.group(2).strip(),
        category=meta.get("category") or "guide",
        source_type="guide",
        url=sources[0] if sources else "",
        date=str(meta.get("updated") or ""),
        extra={
            "status": meta.get("status") or "draft",
            "aliases": list(meta.get("aliases") or []),
        },
    )


def load_guides(directory: Path, include_drafts: bool = False) -> list[SourceDocument]:
    """공략 문서를 모두 읽습니다. include_drafts=False면 검토 완료(reviewed) 문서만 반환합니다."""
    documents = []
    for path in sorted(directory.glob("*.md")):
        doc = parse_guide(path)
        if doc is None:
            continue
        if doc.extra["status"] != "reviewed" and not include_drafts:
            logger.info(f"검토 전 문서는 적재하지 않습니다: {path.name}")
            continue
        documents.append(doc)
    return documents


# ---------------------------------------------------------------------------
# 넥슨 공지사항
# ---------------------------------------------------------------------------

# 종류 → (목록 경로, 목록 응답 키, 상세 경로, 기간 시작 키, 기간 종료 키)
NOTICE_KINDS: dict[str, tuple[str, str, str, str, str]] = {
    "notice": ("/notice", "notice", "/notice/detail", "", ""),
    "update": ("/notice-update", "update_notice", "/notice-update/detail", "", ""),
    "event": ("/notice-event", "event_notice", "/notice-event/detail", "date_event_start", "date_event_end"),
    "cashshop": ("/notice-cashshop", "cashshop_notice", "/notice-cashshop/detail", "date_sale_start", "date_sale_end"),
}


def html_to_text(html: str) -> str:
    """공지 본문 HTML을 검색용 텍스트로 바꿉니다. 표는 '칸 | 칸' 형식의 줄로 남깁니다."""
    soup = BeautifulSoup(html or "", "html.parser")
    for tag in soup(["script", "style"]):
        tag.decompose()

    for table in soup.find_all("table"):
        rows = []
        for tr in table.find_all("tr"):
            cells = [cell.get_text(" ", strip=True) for cell in tr.find_all(["th", "td"])]
            if any(cells):
                rows.append(" | ".join(cells))
        table.replace_with("\n" + "\n".join(rows) + "\n")

    for br in soup.find_all("br"):
        br.replace_with("\n")

    lines = [re.sub(r"[ \t\xa0]+", " ", line).strip() for line in soup.get_text("\n").splitlines()]
    text = "\n".join(lines)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def notice_doc_id(kind: str, notice_id: Any) -> str:
    return f"notice:{kind}:{notice_id}"


async def fetch_notices(
    client: NexonClient,
    limit_per_kind: int = 20,
    known_doc_ids: set[str] | None = None,
) -> list[SourceDocument]:
    """종류별 최신 공지를 가져옵니다. 이미 적재한 공지(known_doc_ids)는 본문을 다시 받지 않습니다.

    한 종류의 목록 조회가 실패해도 나머지 종류는 계속 수집합니다.
    """
    known = known_doc_ids or set()
    documents: list[SourceDocument] = []

    for kind, (list_path, list_key, detail_path, start_key, end_key) in NOTICE_KINDS.items():
        try:
            items = (await client.get_json(list_path)).get(list_key) or []
        except AppException as e:
            logger.error(f"{kind} 공지 목록 조회 실패: {e.message}")
            continue

        for item in items[:limit_per_kind]:
            notice_id = item.get("notice_id")
            if not notice_id or notice_doc_id(kind, notice_id) in known:
                continue
            try:
                detail = await client.get_json(detail_path, {"notice_id": notice_id})
            except AppException as e:
                logger.warning(f"{kind} 공지 {notice_id} 본문 조회 실패: {e.message}")
                continue

            content = html_to_text(detail.get("contents", ""))
            if not content:
                continue

            extra = {}
            if start_key and (detail.get(start_key) or item.get(start_key)):
                extra["period_start"] = detail.get(start_key) or item.get(start_key)
                extra["period_end"] = detail.get(end_key) or item.get(end_key) or ""

            documents.append(
                SourceDocument(
                    doc_id=notice_doc_id(kind, notice_id),
                    title=detail.get("title") or item.get("title") or "제목 없음",
                    content=content,
                    category=kind,
                    source_type="nexon_notice",
                    url=detail.get("url") or item.get("url") or "",
                    date=detail.get("date") or item.get("date") or "",
                    extra=extra,
                )
            )

    logger.info(f"새 공지 {len(documents)}건 수집")
    return documents


# ---------------------------------------------------------------------------
# 로컬 JSON 자료
# ---------------------------------------------------------------------------


def _json_to_markdown(data: Any, level: int = 2) -> str:
    """JSON을 마크다운으로 바꿉니다. 아이콘·이미지 URL과 빈 값은 뺍니다."""
    lines: list[str] = []
    if isinstance(data, dict):
        for key, value in data.items():
            if value in (None, "", [], {}) or "icon" in key or "image" in key:
                continue
            label = key.replace("_", " ")
            if isinstance(value, (dict, list)):
                lines.append(f"{'#' * min(level, 6)} {label}")
                lines.append(_json_to_markdown(value, level + 1))
            else:
                lines.append(f"- {label}: {value}")
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, (dict, list)):
                lines.append(_json_to_markdown(item, level))
                lines.append("")
            elif item not in (None, ""):
                lines.append(f"- {item}")
    else:
        lines.append(str(data))
    return "\n".join(line for line in lines if line is not None)


def load_json_files(directory: Path) -> list[SourceDocument]:
    """디렉터리의 JSON 자료를 문서로 읽습니다. 하위 폴더 이름이 카테고리가 됩니다."""
    if not directory.exists():
        return []

    documents = []
    for path in sorted(directory.rglob("*.json")):
        relative = path.relative_to(directory).as_posix()
        # 캐릭터·랭킹 데이터는 실시간 조회 대상이라 지식 베이스에 넣지 않습니다.
        if relative.split("/")[0] in {"character", "rankings", "notices"}:
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            logger.error(f"JSON 자료를 읽지 못했습니다 ({relative}): {e}")
            continue
        documents.append(
            SourceDocument(
                doc_id=f"json:{relative}",
                title=path.stem.replace("_", " "),
                content=_json_to_markdown(data),
                category=path.parent.name,
                source_type="json",
            )
        )
    return documents
