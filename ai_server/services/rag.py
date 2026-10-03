import logging

from ai_server.graph.nodes.rag_nodes import format_documents, search_documents
from ai_server.llm.factory import get_answer_llm
from ai_server.prompts.templates import RAG_SINGLE_QUERY_PROMPT
from ai_server.schemas.rag import RAGQueryResponse, ReferencedDocument
from ai_server.services.chat import build_langchain_config

logger = logging.getLogger(__name__)


async def process_single_rag_query(query: str, top_k: int) -> RAGQueryResponse:
    """단일 질의에 대한 RAG 처리 및 답변을 생성합니다."""
    config = build_langchain_config()
    runnable_config = (
        {"callbacks": config["callbacks"]} if "callbacks" in config else None
    )

    # 1. 하이브리드 검색으로 관련 문서 찾기 (대화 그래프와 같은 검색기 사용)
    chunks = (await search_documents(query, runnable_config))[:top_k]
    context, sources = format_documents(chunks)

    # 2. 메이플스토리 전용 프롬프트 빌드
    prompt = RAG_SINGLE_QUERY_PROMPT.format(context=context, query=query)

    # 3. LLM 비동기 추론 실행
    llm = get_answer_llm()
    response = await llm.ainvoke(prompt, config=runnable_config)

    # 4. 참조 문서 리스트 구성
    referenced_docs = [
        ReferencedDocument(title=source["title"], source=source["url"] or source["category"])
        for source in sources
    ]

    return RAGQueryResponse(
        answer=response.text.strip(),
        referenced_documents=referenced_docs,
    )
