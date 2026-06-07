# ai_server/rag/retriever.py
"""
문서 검색 서비스

Vector Store(의미 검색)와 BM25(키워드 검색)를 결합한 Hybrid Search를 구현합니다.
"""

import logging
from typing import List, Optional

from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever

# 절대경로 import: sys.path 조작 없이 ai_server 패키지를 직접 참조합니다.
from ai_server.rag.vectorstore import get_vectorstore
from ai_server.rag.document_loader import DocumentLoader

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class Retriever:
    """
    하이브리드 검색기 (Vector + BM25).

    초기화 우선순위:
      1. BM25 Retriever (pgvector에서 전체 문서를 로드하여 인덱스 生成)
      2. BM25 실패 시 → Vector Search Fallback
    """

    def __init__(self, k: int = 5) -> None:
        self.k = k
        self.vectorstore = get_vectorstore()
        self.retriever: Optional[BaseRetriever] = None
        self._initialize_hybrid_retriever()

    def _initialize_hybrid_retriever(self) -> None:
        """BM25 Retriever 초기화 (실패 시 Vector Search로 대체)."""
        try:
            self.retriever = self._create_bm25_retriever()

            if self.retriever:
                logger.info("✅ BM25 검색기 초기화 완료")
            else:
                logger.warning("⚠️ BM25 초기화 실패로 Vector Search를 Fallback으로 사용합니다.")
                self.retriever = self.vectorstore.as_retriever(
                    search_type="similarity", search_kwargs={"k": self.k}
                )

        except Exception as e:
            logger.error(f"❌ 검색기 초기화 중 오류 발생: {e}")
            self.retriever = self.vectorstore.as_retriever(search_kwargs={"k": self.k})

    def _create_bm25_retriever(self) -> Optional[BM25Retriever]:
        """PostgreSQL에서 문서를 로드하여 BM25 인덱스 생성."""
        try:
            docs = self._load_documents_from_vectorstore()

            if not docs:
                logger.warning("BM25 생성을 위한 문서 데이터가 없습니다.")
                return None

            bm25 = BM25Retriever.from_documents(docs)
            bm25.k = self.k
            logger.info(f"✅ BM25 Retriever 초기화 완료 (문서 수: {len(docs)})")
            return bm25

        except ImportError:
            logger.error("❌ 'rank_bm25' 패키지가 설치되지 않았습니다. 'pip install rank_bm25'를 실행하세요.")
            return None
        except Exception as e:
            logger.error(f"BM25 생성 중 오류: {e}")
            return None

    def _load_documents_from_vectorstore(self) -> List[Document]:
        """
        pgvector에서 전체 문서를 로드합니다.

        pgvector는 get() 메서드를 지원하지 않으므로,
        빈 쿼리로 충분히 큰 k 값을 사용해 전체 문서를 가져옵니다.
        """
        try:
            docs = self.vectorstore.similarity_search(query="", k=10000)
            if docs:
                logger.info(f"PostgreSQL에서 {len(docs)}개 문서 로드 완료")
            return docs

        except Exception as e:
            logger.error(f"PostgreSQL에서 문서 로드 실패: {e}")
            # Fallback: JSON 파일에서 로드 시도
            try:
                logger.info("Fallback: JSON 파일에서 문서 로드 시도")
                loader = DocumentLoader()
                return loader.load_json_file()
            except Exception as fallback_error:
                logger.error(f"Fallback 로드도 실패: {fallback_error}")
                return []

    def retrieve(self, query: str, config: Optional[dict] = None) -> List[Document]:
        """
        문서 검색을 실행합니다.

        Args:
            query: 검색할 질문 문자열.
            config: 선택적 LangChain 설정 (콜백 등).

        Returns:
            검색된 Document 리스트.
        """
        if not self.retriever:
            logger.error("검색기가 초기화되지 않았습니다.")
            return []

        logger.info(f"🔍 검색 요청 (Hybrid): {query}")
        try:
            docs = self.retriever.invoke(query, config=config)
            for i, doc in enumerate(docs):
                source = doc.metadata.get("source", "unknown")
                title = doc.metadata.get("title", "No Title")
                logger.info(f"  [Doc {i + 1}] {source} | {title}")

            if not docs:
                logger.warning("검색 결과 없음")

            return docs

        except Exception as e:
            logger.error(f"검색 실행 오류: {e}")
            return []


# --- 테스트 실행 코드 ---
if __name__ == "__main__":
    test_query = "메이플스토리 크리스마스 이벤트"
    print(f"\n🚀 테스트 시작: {test_query}")

    try:
        retriever = Retriever(k=3)
        results = retriever.retrieve(test_query)

        print("\n📊 검색 결과:")
        for i, doc in enumerate(results):
            print(f"[{i + 1}] {doc.metadata.get('title', '제목없음')} : {doc.page_content[:100]}...")

    except Exception as e:
        print(f"오류 발생: {e}")
