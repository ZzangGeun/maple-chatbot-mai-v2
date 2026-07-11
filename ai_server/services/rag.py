import logging

from ai_server.llm.factory import get_llm
from ai_server.prompts.templates import RAG_SINGLE_QUERY_PROMPT
from ai_server.rag.retriever import Retriever
from ai_server.schemas.rag import RAGQueryResponse, ReferencedDocument
from ai_server.services.chat import build_langchain_config

logger = logging.getLogger(__name__)


async def process_single_rag_query(query: str, top_k: int) -> RAGQueryResponse:
    """단일 질의에 대한 RAG 처리 및 답변을 생성합니다."""
    retriever = Retriever(k=top_k)
    config = build_langchain_config()
    runnable_config = (
        {"callbacks": config["callbacks"]} if "callbacks" in config else None
    )

    docs = retriever.retrieve(query, config=runnable_config)

    # 1. 검색 문서들로부터 컨텍스트 추출
    context = "\n\n".join([doc.page_content for doc in docs])

    # 2. 메이플스토리 전용 프롬프트 빌드
    prompt = RAG_SINGLE_QUERY_PROMPT.format(context=context, query=query)

    # 3. LLM 비동기 추론 실행
    llm = get_llm()
    response = await llm.ainvoke(prompt, config=runnable_config)

    answer = response.content if hasattr(response, "content") else str(response)

    # 4. 참조 문서 리스트 구성
    referenced_docs = [
        ReferencedDocument(
            title=doc.metadata.get("title", "제목 없음"),
            source=doc.metadata.get("source", "알 수 없음"),
            score=doc.metadata.get("score", 1.0),
        )
        for doc in docs
    ]

    return RAGQueryResponse(
        answer=answer.strip(),
        referenced_documents=referenced_docs,
    )
