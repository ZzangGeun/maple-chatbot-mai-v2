# ai_server/rag/vectorstore.py
"""
pgvector 기반 운영용 청크 인덱스 생성

PGVector 객체는 생성 시 DB 테이블·확장을 확인하므로 프로세스당 한 번만 만듭니다.
"""

import logging
import threading

from ai_server.config import settings
from ai_server.rag.embeddings import QwenEmbeddings
from ai_server.rag.index import PGVectorIndex

logger = logging.getLogger(__name__)

_index: PGVectorIndex | None = None
_lock = threading.Lock()


def get_index() -> PGVectorIndex:
    """운영용 청크 인덱스(PGVector) 싱글턴을 반환합니다. DB에 연결할 수 없으면 예외가 발생합니다."""
    global _index
    with _lock:
        if _index is None:
            from langchain_postgres import PGVector

            store = PGVector(
                embeddings=QwenEmbeddings(),
                collection_name=settings.db.collection_name,
                connection=settings.db.connection,
                use_jsonb=True,
            )
            _index = PGVectorIndex(store, settings.db.connection, settings.db.collection_name)
            logger.info(f"pgvector 인덱스 연결 완료 (컬렉션: {settings.db.collection_name})")
    return _index
