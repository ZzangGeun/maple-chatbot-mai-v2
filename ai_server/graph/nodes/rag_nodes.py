# ai_server/graph/nodes/rag_nodes.py
"""
RAG 서브 그래프 전용 노드 모음.
"""

import logging

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableConfig

from ai_server.graph.state.rag_state import RagState
from ai_server.llm.gemini_loader import get_gemini_llm
from ai_server.prompts.templates import PromptTemplate
from ai_server.rag.retriever import Retriever

logger = logging.getLogger("RagNodes")

# 모듈 레벨 초기화
_retriever_instance = Retriever()
MAX_DOC_CHARS = 1200
MAX_CONTEXT_CHARS = 4000


async def gemini_rewrite_node(state: RagState, config: RunnableConfig = None) -> dict:
    """Gemini를 사용한 초고속 쿼리 재작성 노드"""
    llm = get_gemini_llm()
    messages = state["messages"]

    prompt = ChatPromptTemplate.from_messages([
        ("system", PromptTemplate.GEMINI_REWRITE_SYSTEM.value),
        MessagesPlaceholder(variable_name="messages"),
    ])

    chain = prompt | llm | StrOutputParser()
    new_query = await chain.ainvoke({"messages": messages}, config=config)
    new_query = new_query.strip()

    logger.info(f"[GeminiRewrite] 재작성된 쿼리: {new_query}")
    return {"query": new_query}


async def local_retrieve_node(state: RagState, config: RunnableConfig = None) -> dict:
    """재작성된 쿼리로 RAG 벡터스토어에서 관련 문서를 검색합니다."""
    query = state["query"]
    docs = await _retriever_instance.retriever.ainvoke(query, config=config)

    context_parts = []
    for i, doc in enumerate(docs, 1):
        metadata = doc.metadata
        title = metadata.get("title", "제목 없음")
        source = metadata.get("source", "출처 정보 없음")
        category = metadata.get("category", "기타")
        url = (
            metadata.get("notice_url")
            or metadata.get("thumbnail_url")
            or metadata.get("url", "")
        )

        url_line = f"- **참고 링크**: {url}" if url else ""

        context_part = "\n".join([
            f"## [문서 {i}] {title}",
            f"- **카테고리**: {category}",
            f"- **출처**: {source}",
            url_line,
            "",
            "**내용**:",
            doc.page_content[:MAX_DOC_CHARS],
            "",
            "---",
        ])
        context_parts.append(context_part)

    context_text = "\n".join(context_parts)[:MAX_CONTEXT_CHARS]
    logger.info(f"[LocalRetrieve] {len(docs)}개 문서 검색 완료 | 쿼리: '{query}'")
    if docs:
        logger.info(f"[LocalRetrieve] 첫 번째 문서 미리보기: {docs[0].page_content[:80]}...")

    return {"context": context_text}
