# ai_server/graph/nodes/route_nodes.py
"""
메인 그래프에서 서브 그래프로 라우팅을 담당하는 노드 모음.
Gemini LLM의 구조화 출력(with_structured_output)으로 안정적인 분류를 수행합니다.
"""

import logging
from typing import Literal

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel, Field

from ai_server.graph.state.main_state import MainState
from ai_server.llm.gemini_loader import get_gemini_llm
from ai_server.prompts import PromptTemplate, get_prompt

logger = logging.getLogger("RouteNodes")

# 라우팅 프롬프트에 포함할 최근 대화 메시지 수.
# 후속 질문("그 캐릭터 장비는?")을 맥락으로 판단할 수 있도록 합니다.
_ROUTE_CONTEXT_WINDOW = 6


class RouteDecision(BaseModel):
    """라우팅 분류 결과를 구조화 출력으로 받기 위한 스키마.

    Literal 타입으로 허용 값을 제한하여 문자열 부분일치 파싱을 제거합니다.
    """

    route: Literal["character", "search", "chat"] = Field(
        description=(
            "질문 분류 결과. "
            "'character': 특정 캐릭터의 레벨/직업/스탯 등 개인 정보 조회, "
            "'search': 메이플스토리 공략/아이템/보스/이벤트 등 게임 정보 검색, "
            "'chat': 인사/잡담 등 일반 대화"
        )
    )


async def gemini_route_node(state: MainState, config: RunnableConfig | None = None) -> str:
    """Gemini 구조화 출력을 사용한 라우팅 노드.

    - 최근 대화 맥락(_ROUTE_CONTEXT_WINDOW개)을 함께 전달해 후속 질문 오분류를 줄입니다.
    - temperature=0.0으로 결정적 분류를 수행합니다.
    - 분류 실패 시 chat_node로 폴백하여 요청 전체가 실패하지 않도록 방어합니다.
    """
    question = state["messages"][-1].content

    try:
        llm = get_gemini_llm(temperature=0.0)
        structured_llm = llm.with_structured_output(RouteDecision)

        # 최근 대화 맥락을 포함해 후속 질문도 올바르게 분류합니다.
        recent_messages = state["messages"][-_ROUTE_CONTEXT_WINDOW:]

        prompt = ChatPromptTemplate.from_messages([
            ("system", get_prompt(PromptTemplate.ROUTE_SYSTEM, model="gemini")),
            MessagesPlaceholder(variable_name="messages"),
        ])

        chain = prompt | structured_llm
        result = await chain.ainvoke({"messages": recent_messages}, config=config)
        if not isinstance(result, RouteDecision):
            raise TypeError(f"예상치 못한 라우팅 응답 타입: {type(result)}")
        decision = result.route
    except Exception as e:
        # 라우팅 실패가 요청 전체의 500 에러로 이어지지 않도록 chat으로 폴백합니다.
        logger.error(f"[GeminiRoute] 분류 실패, chat_node로 폴백: {e}")
        return "chat_node"

    logger.info(f"[GeminiRoute] 분류 결과: '{decision}' | 질문: {question[:50]}...")

    # 서브 그래프로 라우팅 (리턴값은 Conditional Edge의 맵핑 키로 사용됨)
    route_map = {
        "character": "nexon_graph",
        "search": "rag_graph",
        "chat": "chat_node",
    }
    return route_map[decision]
