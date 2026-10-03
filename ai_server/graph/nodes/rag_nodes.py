# ai_server/graph/nodes/rag_nodes.py
"""
RAG 서브 그래프 전용 노드 모음.

rewrite(질문 재작성) → retrieve(문서 검색) 순으로 실행되며,
답변 생성은 메인 그래프의 generate 노드가 담당합니다.
"""

import asyncio
import logging
from typing import Any

from langchain_core.messages import BaseMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableConfig

from ai_server.graph.state.rag_state import RagState
from ai_server.llm.factory import get_utility_llm
from ai_server.prompts import PromptTemplate, get_prompt
from ai_server.rag.documents import Chunk
from ai_server.rag.retriever import HybridRetriever

logger = logging.getLogger("RagNodes")

# 지연 초기화 싱글턴: 임포트 시점이 아닌 최초 사용 시점에 DB에 연결합니다.
_retriever_instance: HybridRetriever | None = None
SEARCH_K = 5
MAX_CHUNK_CHARS = 1200
MAX_CONTEXT_CHARS = 5000

CATEGORY_LABELS = {
    "guide": "공략",
    "notice": "공지사항",
    "update": "업데이트",
    "event": "이벤트",
    "cashshop": "캐시샵",
}


def _get_retriever() -> HybridRetriever:
    """하이브리드 검색기 싱글턴을 지연 생성하여 반환합니다."""
    global _retriever_instance
    if _retriever_instance is None:
        from ai_server.rag.vectorstore import get_index

        _retriever_instance = HybridRetriever(get_index())
    return _retriever_instance


async def rewrite_query(
    messages: list[BaseMessage], config: RunnableConfig | None = None
) -> str:
    """대화 맥락을 반영해 마지막 질문을 검색하기 좋은 문장으로 재작성합니다."""
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", get_prompt(PromptTemplate.REWRITE_SYSTEM, model="gemini")),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )

    chain = prompt | get_utility_llm() | StrOutputParser()
    new_query = await chain.ainvoke({"messages": messages}, config=config)
    return new_query.strip()


async def search_documents(
    query: str, config: RunnableConfig | None = None
) -> list[Chunk]:
    """지식 베이스에서 질의와 관련된 청크를 관련도 순으로 검색합니다."""
    # 최초 호출 시 DB 연결과 검색 인덱스를 준비하므로 이벤트 루프를 막지 않도록 스레드에서 생성합니다.
    retriever = await asyncio.to_thread(_get_retriever)
    return await retriever.asearch(query, k=SEARCH_K)


def format_documents(chunks: list[Chunk]) -> tuple[str, list[dict[str, Any]]]:
    """검색 청크를 문서별로 묶어 번호가 붙은 컨텍스트 문자열과 근거 문서 목록으로 변환합니다.

    같은 문서의 청크는 하나의 [n] 아래 모아, 답변의 출처 번호가 문서 단위가 되게 합니다.
    컨텍스트가 MAX_CONTEXT_CHARS를 넘지 않도록 관련도가 높은 문서부터 담고,
    근거 문서 목록에는 실제로 컨텍스트에 포함된 문서만 넣습니다.
    """
    groups: dict[str, list[Chunk]] = {}
    for chunk in chunks:
        groups.setdefault(chunk.doc_id or chunk.chunk_id, []).append(chunk)

    context_parts: list[str] = []
    sources: list[dict[str, Any]] = []
    remaining = MAX_CONTEXT_CHARS

    for i, doc_chunks in enumerate(groups.values(), 1):
        metadata = doc_chunks[0].metadata
        title = metadata.get("title") or "제목 없음"
        category = metadata.get("category", "기타")
        url = metadata.get("url") or ""
        date = str(metadata.get("date") or "")[:10]

        lines = [f"[{i}] {title}", f"- 분류: {CATEGORY_LABELS.get(category, category)}"]
        if date:
            lines.append(f"- 날짜: {date}")
        if metadata.get("period_start"):
            period_end = str(metadata.get("period_end") or "")[:10]
            lines.append(f"- 기간: {str(metadata['period_start'])[:10]} ~ {period_end}")
        if url:
            lines.append(f"- 참고 링크: {url}")
        lines.append("- 내용:")
        for chunk in sorted(doc_chunks, key=lambda c: c.metadata.get("chunk_index", 0)):
            lines.append(chunk.text[:MAX_CHUNK_CHARS])
        lines.append("")
        part = "\n".join(lines)

        if len(part) > remaining:
            if context_parts:
                break
            # 첫 문서는 잘라서라도 포함합니다.
            part = part[:remaining]

        context_parts.append(part)
        sources.append(
            {"index": i, "title": title, "url": url, "category": category, "date": date}
        )
        remaining -= len(part)

    return "\n".join(context_parts), sources


async def rewrite_node(state: RagState, config: RunnableConfig | None = None) -> dict:
    """검색용 질문을 재작성합니다. 실패하면 원래 질문으로 검색합니다."""
    question = state["messages"][-1].text
    try:
        query = await rewrite_query(state["messages"], config) or question
    except Exception as e:
        logger.warning(f"[Rewrite] 질문 재작성 실패, 원래 질문으로 검색합니다: {e}")
        query = question

    logger.info(f"[Rewrite] 검색 쿼리: {query}")
    return {"query": query}


async def retrieve_node(state: RagState, config: RunnableConfig | None = None) -> dict:
    """재작성된 쿼리로 관련 문서를 검색해 컨텍스트와 근거 문서 목록을 만듭니다.

    검색에 실패하면 빈 컨텍스트를 돌려주어, 답변 노드가 "알 수 없다"고 안내하도록 합니다.
    """
    query = state.get("query") or state["messages"][-1].text
    try:
        chunks = await search_documents(query, config)
    except Exception as e:
        logger.error(f"[Retrieve] 문서 검색 실패: {e}", exc_info=True)
        return {"knowledge_context": "", "sources": []}

    context, sources = format_documents(chunks)
    logger.info(
        f"[Retrieve] 청크 {len(chunks)}개 검색, 문서 {len(sources)}개 사용 | 쿼리: '{query}'"
    )
    return {"knowledge_context": context, "sources": sources}
