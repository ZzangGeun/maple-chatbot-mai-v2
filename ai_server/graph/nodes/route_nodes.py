# ai_server/graph/nodes/route_nodes.py
"""
메인 그래프에서 서브 그래프로 라우팅을 담당하는 노드 모음.
Gemini LLM을 사용하여 초고속 분류를 수행합니다.
"""

import logging

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig

from ai_server.graph.state.main_state import MainState
from ai_server.llm.gemini_loader import get_gemini_llm
from ai_server.prompts import PromptTemplate, get_prompt

logger = logging.getLogger("RouteNodes")


async def gemini_route_node(state: MainState, config: RunnableConfig = None) -> str:
    """Gemini를 사용한 초고속 라우팅 노드"""
    llm = get_gemini_llm()
    question = state["messages"][-1].content

    prompt = ChatPromptTemplate.from_messages([
        ("system", get_prompt(PromptTemplate.ROUTE_SYSTEM, model="gemini")),
        ("human", "{question}")
    ])

    chain = prompt | llm | StrOutputParser()
    decision = await chain.ainvoke({"question": question}, config=config)
    decision = decision.strip().lower()

    logger.info(f"[GeminiRoute] 분류 결과: '{decision}' | 질문: {question[:50]}...")

    # 서브 그래프로 라우팅 (리턴값은 Conditional Edge의 맵핑 키로 사용됨)
    if "character" in decision:
        return "nexon_graph"
    if "search" in decision:
        return "rag_graph"
    return "chat_node"
