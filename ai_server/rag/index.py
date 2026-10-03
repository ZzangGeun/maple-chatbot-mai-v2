# ai_server/rag/index.py
"""
청크 저장소(인덱스)

수집 파이프라인과 검색기는 ChunkIndex 인터페이스만 사용합니다.
  - PGVectorIndex: 운영용. langchain_postgres PGVector 테이블에 청크와 임베딩을 저장합니다.
  - InMemoryIndex: 테스트·오프라인 평가용. 임베딩 없이도 키워드 검색 평가가 가능합니다.

청크 메타데이터의 doc_id·content_hash로 문서 단위 증분 적재를 합니다.
doc_id가 없는 청크는 이전 방식으로 적재된 데이터(캐릭터 정보, 예전 공지 JSON)입니다.
"""

import logging
import math
from typing import Protocol

import psycopg
from langchain_core.embeddings import Embeddings

from ai_server.rag.documents import Chunk

logger = logging.getLogger(__name__)

_ADD_BATCH_SIZE = 64


class ChunkIndex(Protocol):
    def doc_hashes(self) -> dict[str, str]:
        """적재된 문서 ID → 내용 해시."""

    def delete_docs(self, doc_ids: list[str]) -> None:
        """문서의 모든 청크를 지웁니다."""

    def delete_legacy(self) -> int:
        """doc_id 없이 예전 방식으로 적재된 청크를 지우고 개수를 반환합니다."""

    def add_chunks(self, chunks: list[Chunk]) -> None:
        """청크를 임베딩해 저장합니다. 같은 ID가 있으면 덮어씁니다."""

    def all_chunks(self) -> list[Chunk]:
        """키워드 검색 인덱스를 만들기 위해 모든 청크를 반환합니다."""

    def vector_search(self, query: str, k: int) -> list[Chunk]:
        """질의와 의미가 가까운 순으로 청크를 반환합니다."""


class InMemoryIndex:
    """메모리에 청크를 두는 인덱스. embeddings가 없으면 벡터 검색은 빈 결과를 돌려줍니다."""

    def __init__(self, embeddings: Embeddings | None = None) -> None:
        self._embeddings = embeddings
        self._chunks: dict[str, Chunk] = {}
        self._vectors: dict[str, list[float]] = {}
        self.legacy_count = 0

    def doc_hashes(self) -> dict[str, str]:
        return {c.doc_id: c.metadata.get("content_hash", "") for c in self._chunks.values()}

    def delete_docs(self, doc_ids: list[str]) -> None:
        targets = set(doc_ids)
        for chunk_id in [cid for cid, c in self._chunks.items() if c.doc_id in targets]:
            self._chunks.pop(chunk_id)
            self._vectors.pop(chunk_id, None)

    def delete_legacy(self) -> int:
        removed, self.legacy_count = self.legacy_count, 0
        return removed

    def add_chunks(self, chunks: list[Chunk]) -> None:
        vectors = self._embeddings.embed_documents([c.text for c in chunks]) if self._embeddings else []
        for i, chunk in enumerate(chunks):
            self._chunks[chunk.chunk_id] = chunk
            if vectors:
                self._vectors[chunk.chunk_id] = vectors[i]

    def all_chunks(self) -> list[Chunk]:
        return list(self._chunks.values())

    def vector_search(self, query: str, k: int) -> list[Chunk]:
        if not self._embeddings or not self._vectors:
            return []
        query_vector = self._embeddings.embed_query(query)

        def cosine(vector: list[float]) -> float:
            dot = sum(a * b for a, b in zip(query_vector, vector))
            norm = math.sqrt(sum(a * a for a in query_vector)) * math.sqrt(sum(b * b for b in vector))
            return dot / norm if norm else 0.0

        ranked = sorted(self._vectors, key=lambda cid: cosine(self._vectors[cid]), reverse=True)
        return [self._chunks[cid] for cid in ranked[:k]]


class PGVectorIndex:
    """PGVector(langchain_postgres) 테이블을 쓰는 운영용 인덱스."""

    def __init__(self, store, connection: str, collection_name: str) -> None:
        """
        Args:
            store: langchain_postgres.PGVector 인스턴스 (임베딩·벡터 검색 담당)
            connection: PostgreSQL 접속 문자열 (postgresql+psycopg://... 형식도 허용)
            collection_name: PGVector 컬렉션 이름
        """
        self._store = store
        self._conninfo = connection.replace("postgresql+psycopg://", "postgresql://")
        self._collection = collection_name

    def _execute(self, sql: str, params: tuple) -> list[tuple]:
        with psycopg.connect(self._conninfo) as conn, conn.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall() if cur.description else []
            conn.commit()
            return rows

    _IN_COLLECTION = (
        "collection_id = (SELECT uuid FROM langchain_pg_collection WHERE name = %s)"
    )

    def doc_hashes(self) -> dict[str, str]:
        rows = self._execute(
            "SELECT DISTINCT cmetadata->>'doc_id', cmetadata->>'content_hash' "
            f"FROM langchain_pg_embedding WHERE {self._IN_COLLECTION} AND cmetadata ? 'doc_id'",
            (self._collection,),
        )
        return {doc_id: content_hash for doc_id, content_hash in rows}

    def delete_docs(self, doc_ids: list[str]) -> None:
        if doc_ids:
            self._execute(
                f"DELETE FROM langchain_pg_embedding WHERE {self._IN_COLLECTION} "
                "AND cmetadata->>'doc_id' = ANY(%s)",
                (self._collection, list(doc_ids)),
            )

    def delete_legacy(self) -> int:
        rows = self._execute(
            f"DELETE FROM langchain_pg_embedding WHERE {self._IN_COLLECTION} "
            "AND NOT (cmetadata ? 'doc_id') RETURNING id",
            (self._collection,),
        )
        return len(rows)

    def add_chunks(self, chunks: list[Chunk]) -> None:
        for start in range(0, len(chunks), _ADD_BATCH_SIZE):
            batch = chunks[start : start + _ADD_BATCH_SIZE]
            self._store.add_texts(
                [c.text for c in batch],
                metadatas=[c.metadata for c in batch],
                ids=[c.chunk_id for c in batch],
            )

    def all_chunks(self) -> list[Chunk]:
        rows = self._execute(
            "SELECT id, document, cmetadata FROM langchain_pg_embedding "
            f"WHERE {self._IN_COLLECTION} AND cmetadata ? 'doc_id'",
            (self._collection,),
        )
        return [Chunk(chunk_id=str(cid), text=text or "", metadata=meta or {}) for cid, text, meta in rows]

    def vector_search(self, query: str, k: int) -> list[Chunk]:
        results = self._store.similarity_search_with_score(query, k=k)
        return [
            Chunk(chunk_id=str(doc.id), text=doc.page_content, metadata=doc.metadata or {})
            for doc, _distance in results
            # 예전 방식으로 적재된 청크는 출처 정보가 없어 사용하지 않습니다.
            if (doc.metadata or {}).get("doc_id")
        ]
