# ai_server/rag/documents.py
"""
RAG 지식 베이스의 문서·청크 데이터 모델과 청킹(분할) 로직

수집 소스(sources.py)가 SourceDocument를 만들고, split_document()가 검색 단위인 Chunk로 나눕니다.
청크 ID는 '{문서 ID}#{순번}'으로 정해 같은 문서를 다시 적재하면 덮어쓰도록 합니다.
"""

import hashlib
import json
import re
from dataclasses import dataclass, field
from typing import Any

from langchain_text_splitters import RecursiveCharacterTextSplitter

CHUNK_SIZE = 700
CHUNK_OVERLAP = 100

_splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
    separators=["\n\n", "\n", ". ", " ", ""],
)

# 마크다운 섹션 제목 (## 또는 ###)
_HEADING = re.compile(r"^(#{2,3})\s+(.+?)\s*$")


@dataclass
class SourceDocument:
    """수집한 원본 문서 하나 (공략 문서, 공지사항 등)."""

    doc_id: str  # 안정적인 고유 ID (예: "guide:starforce", "notice:event:149196")
    title: str
    content: str  # 마크다운 또는 일반 텍스트
    category: str  # guide / notice / event / update / cashshop / json
    source_type: str  # guide / nexon_notice / json
    url: str = ""
    date: str = ""  # 게시일 또는 마지막 확인일 (YYYY-MM-DD...)
    extra: dict[str, Any] = field(default_factory=dict)  # event_start, event_end, status, aliases 등

    @property
    def content_hash(self) -> str:
        """내용이 바뀌었는지 판단하는 해시. 메타데이터가 바뀌어도 다시 적재합니다."""
        payload = json.dumps(
            [self.title, self.content, self.category, self.url, self.date, self.extra],
            ensure_ascii=False,
            sort_keys=True,
            default=str,
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass
class Chunk:
    """검색 단위. text는 문서 제목·섹션 머리말을 포함한 본문입니다."""

    chunk_id: str
    text: str
    metadata: dict[str, Any]

    @property
    def doc_id(self) -> str:
        return self.metadata.get("doc_id", "")


def _sections(content: str) -> list[tuple[str, str]]:
    """마크다운을 (섹션 제목, 본문) 목록으로 나눕니다. 제목 앞의 글은 제목 없는 섹션이 됩니다."""
    sections: list[tuple[str, list[str]]] = [("", [])]
    for line in content.splitlines():
        match = _HEADING.match(line)
        if match:
            sections.append((match.group(2), []))
        else:
            sections[-1][1].append(line)
    return [
        (title, "\n".join(lines).strip())
        for title, lines in sections
        if "\n".join(lines).strip()
    ]


def split_document(doc: SourceDocument) -> list[Chunk]:
    """문서를 섹션 단위로 나누고, 긴 섹션은 다시 잘라 청크로 만듭니다.

    각 청크 본문 앞에 '[문서 제목 > 섹션]' 머리말과 동의어를 붙여, 섹션만 떼어 봐도
    무엇에 대한 내용인지 검색·답변 모델이 알 수 있게 합니다.
    """
    aliases = doc.extra.get("aliases") or []
    alias_line = f"(관련어: {', '.join(aliases)})\n" if aliases else ""

    chunks: list[Chunk] = []
    for section, body in _sections(doc.content):
        header = f"[{doc.title} > {section}]" if section else f"[{doc.title}]"
        for piece in _splitter.split_text(body):
            index = len(chunks)
            chunks.append(
                Chunk(
                    chunk_id=f"{doc.doc_id}#{index}",
                    text=f"{header}\n{alias_line}{piece}",
                    metadata={
                        "doc_id": doc.doc_id,
                        "chunk_index": index,
                        "title": doc.title,
                        "section": section,
                        "category": doc.category,
                        "source_type": doc.source_type,
                        "url": doc.url,
                        "date": doc.date,
                        "content_hash": doc.content_hash,
                        **{k: v for k, v in doc.extra.items() if k != "aliases"},
                    },
                )
            )
    return chunks
