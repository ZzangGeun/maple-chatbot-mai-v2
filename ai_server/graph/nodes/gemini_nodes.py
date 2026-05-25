# ai_server/graph/nodes/gemini_nodes.py
"""
Gemini LLM 전용 노드 모음 — 하이브리드 에이전트의 최종 답변 생성 파이프라인

역할:
  - gemini_generate_rag_node : 로컬 에이전트가 검색한 컨텍스트를 받아 고품질 RAG 답변을 생성합니다.
  - gemini_generate_chat_node: 검색 없이 일반 대화 답변을 생성합니다.

설계 의도:
  Gemini는 로컬 LLM이 준비한 컨텍스트(context, query)를 넘겨받아
  '최종 답변 생성'에만 집중합니다.
  이렇게 역할을 분리하면 Gemini API 호출 횟수를 최소화하면서도
  최고 품질의 답변을 유지할 수 있습니다.
"""

import logging

from langchain_core.messages import AIMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from ai_server.graph.state import GraphState
from ai_server.llm.gemini_loader import get_gemini_llm
from ai_server.prompts.gemini import (
    GEMINI_CHAT_SYSTEM,
    GEMINI_RAG_SYSTEM,
)

logger = logging.getLogger("GeminiNodes")


# ---------------------------------------------------------------------------
# 최종 답변 생성 노드들
# ---------------------------------------------------------------------------

def gemini_generate_rag_node(state: GraphState) -> dict:
    """
    로컬 에이전트가 검색한 컨텍스트를 바탕으로 Gemini가 최종 RAG 답변을 생성합니다.

    로컬 LLM이 메이플 도메인 지식으로 최적화한 검색 결과를
    Gemini의 강력한 언어 능력으로 자연스러운 답변으로 변환합니다.

    Args:
        state: 현재 그래프 상태 (state["context"], state["messages"] 사용).

    Returns:
        {"messages": [AIMessage(content=...)]}
    """
    llm = get_gemini_llm()
    context = state["context"]
    rewritten_query = state.get("query", "")

    logger.info(f"[GeminiRAG] 쿼리: '{rewritten_query}' | 컨텍스트 길이: {len(context)}자")

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", GEMINI_RAG_SYSTEM),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )

    chain = prompt | llm | StrOutputParser()
    response = chain.invoke({"context": context, "messages": state["messages"]})
    return {"messages": [AIMessage(content=response)]}


def gemini_generate_chat_node(state: GraphState) -> dict:
    """
    검색 없이 Gemini가 일반 대화 답변을 생성합니다.

    로컬 LLM 라우터가 '일반 대화'로 분류한 경우에만 호출됩니다.
    메이플 공략 지어내기 방지를 위해 별도의 chat 프롬프트를 사용합니다.

    Args:
        state: 현재 그래프 상태 (state["messages"] 사용).

    Returns:
        {"messages": [AIMessage(content=...)]}
    """
    llm = get_gemini_llm()
    logger.info("[GeminiChat] 일반 대화 답변 생성 시작")

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", GEMINI_CHAT_SYSTEM),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )

    chain = prompt | llm | StrOutputParser()
    response = chain.invoke({"messages": state["messages"]})
    return {"messages": [AIMessage(content=response)]}
