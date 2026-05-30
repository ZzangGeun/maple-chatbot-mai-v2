# ai_server/rag/vectorstore.py
"""
pgvector 기반 벡터 저장소

pgvector를 사용하여 문서 임베딩을 저장하고 유사도 검색을 수행합니다.
"""

import logging
import os

import dotenv
from langchain_postgres import PGVector

# 절대경로 import: 상대경로의 try/except 분기를 제거하고 단일 경로로 통일합니다.
from ai_server.rag.embeddings import QwenEmbeddings
from ai_server.rag.document_loader import DocumentLoader

dotenv.load_dotenv()

logger = logging.getLogger(__name__)

DB_CONNECTION = os.getenv("DB_CONNECTION")
COLLECTION_NAME = os.getenv("COLLECTION_NAME")


def get_vectorstore() -> PGVector:
    """
    pgvector 저장소 객체를 생성하여 반환합니다.

    Returns:
        PGVector 인스턴스.
    """
    embedding_model = QwenEmbeddings()
    vectorstore = PGVector(
        embeddings=embedding_model,
        collection_name=COLLECTION_NAME,
        connection=DB_CONNECTION,
        use_jsonb=True,
    )
    return vectorstore


def build_database() -> None:
    """
    JSON 파일과 Redis에서 데이터를 읽어 pgvector에 저장합니다.
    RAG 데이터베이스 초기 구축 시 사용합니다.
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
    """
    pgvector retriever를 반환합니다.

    Args:
        k: 반환할 문서 수.

    Returns:
        VectorStoreRetriever 인스턴스.
    """
    vectorstore = get_vectorstore()
    return vectorstore.as_retriever({"k": k})


if __name__ == "__main__":
    build_database()
