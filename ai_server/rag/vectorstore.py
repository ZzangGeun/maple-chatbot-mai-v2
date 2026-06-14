# ai_server/rag/vectorstore.py
"""
pgvector 기반 벡터 저장소

pgvector를 사용하여 문서 임베딩을 저장하고 유사도 검색을 수행합니다.
"""

import logging

from langchain_postgres import PGEngine, PGVectorStore

# 절대경로 import: 상대경로의 try/except 분기를 제거하고 단일 경로로 통일합니다.
from ai_server.rag.embeddings import QwenEmbeddings
from ai_server.rag.document_loader import DocumentLoader
from ai_server.config import settings

logger = logging.getLogger(__name__)

DB_CONNECTION = settings.db.connection
COLLECTION_NAME = settings.db.collection_name

# PGEngine 및 PGVectorStore의 전역 싱글톤 인스턴스
_pg_engine_instance = None
_vectorstore_instance = None


def get_pg_engine() -> PGEngine:
    """비동기 DB 풀 관리를 위한 PGEngine 인스턴스를 싱글톤으로 반환합니다.

    Returns:
        PGEngine: 초기화된 비동기 DB 엔진 인스턴스.
    """
    global _pg_engine_instance
    if _pg_engine_instance is None:
        async_connection_string = DB_CONNECTION
        # psycopg 드라이버 형식을 비동기 처리가 가능한 asyncpg 형식으로 변환
        if "postgresql+psycopg://" in async_connection_string:
            async_connection_string = async_connection_string.replace(
                "postgresql+psycopg://", "postgresql+asyncpg://"
            )
        elif "postgresql://" in async_connection_string:
            async_connection_string = async_connection_string.replace(
                "postgresql://", "postgresql+asyncpg://"
            )
        
        logger.info("비동기 데이터베이스 엔진(PGEngine)을 초기화합니다.")
        _pg_engine_instance = PGEngine.from_connection_string(
            connection_string=async_connection_string,
        )
    return _pg_engine_instance


def get_vectorstore() -> PGVectorStore:
    """pgvector 저장소 객체를 생성하여 반환합니다. (싱글톤)

    기존 레거시 테이블 스키마(langchain_pg_embedding)와 컬럼 매핑 정보를 명시적으로 지정하여
    새로운 테이블 생성 없이 기존 데이터를 비동기로 안전하게 조회할 수 있도록 연동합니다.

    Returns:
        PGVectorStore: 초기화된 벡터 저장소 인스턴스.
    """
    global _vectorstore_instance
    if _vectorstore_instance is None:
        embedding_model = QwenEmbeddings()
        engine = get_pg_engine()
        
        # langchain_postgres 0.0.14+ API 사양에 맞추어 기존 테이블 구조 및 컬럼 매핑
        _vectorstore_instance = PGVectorStore.create_sync(
            engine=engine,
            embedding_service=embedding_model,
            table_name="langchain_pg_embedding",
            id_column="id",
            content_column="document",
            embedding_column="embedding",
            metadata_json_column="cmetadata",
        )
    return _vectorstore_instance


def build_database() -> None:
    """JSON 파일과 Redis에서 데이터를 읽어 pgvector에 저장합니다.
    RAG 데이터베이스 초기 구축 시 사용합니다.

    Raises:
        ValueError: 로드된 문서가 없는 경우 예외를 유발합니다.
    """
    document_loader = DocumentLoader()
    
    # 1. 로컬 파일에서 로드 (캐릭터 데이터 등)
    file_docs = document_loader.load_json_file()
    
    # 2. Redis에서 로드 (공지사항, 랭킹 등)
    redis_docs = document_loader.load_from_redis()
    
    all_docs = file_docs + redis_docs

    if not all_docs:
        raise ValueError("로드된 문서가 없습니다.")

    vectorstore = get_vectorstore()
    vectorstore.add_documents(all_docs)
    logger.info(f"데이터베이스 구축 완료 (총 {len(all_docs)}개 문서 청크)")


def get_retriever(k: int = 3):
    """pgvector retriever를 반환합니다.

    Args:
        k (int, optional): 반환할 문서 개수. 기본값은 3.

    Returns:
        VectorStoreRetriever: 벡터 검색을 위한 리트리버 객체.
    """
    vectorstore = get_vectorstore()
    return vectorstore.as_retriever(search_kwargs={"k": k})


if __name__ == "__main__":
    build_database()
