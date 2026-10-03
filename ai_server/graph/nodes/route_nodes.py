# ai_server/graph/nodes/route_nodes.py
"""
메인 그래프의 질문 분류(라우팅) 노드 모음.
보조 LLM의 구조화 출력(with_structured_output)으로 안정적인 분류를 수행합니다.
"""

import logging

from langchain_core.messages import BaseMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel, Field

from ai_server.graph.state.main_state import MainState, Route
from ai_server.llm.factory import get_utility_llm
from ai_server.prompts import PromptTemplate, get_prompt

logger = logging.getLogger("RouteNodes")

# 라우팅 프롬프트에 포함할 최근 대화 메시지 수.
# 후속 질문("그 캐릭터 장비는?")을 맥락으로 판단할 수 있도록 합니다.
_ROUTE_CONTEXT_WINDOW = 6

# 분류 결과 → 다음에 실행할 노드 목록.
# character_knowledge는 두 서브 그래프를 병렬로 실행한 뒤 generate에서 합칩니다.
ROUTE_BRANCHES: dict[str, list[str]] = {
    "chat": ["generate"],
    "knowledge": ["knowledge"],
    "character": ["character"],
    "character_knowledge": ["knowledge", "character"],
}


class RouteDecision(BaseModel):
    """라우팅 분류 결과를 구조화 출력으로 받기 위한 스키마.

    Literal 타입으로 허용 값을 제한하여 문자열 부분일치 파싱을 제거합니다.
    """

    route: Route = Field(
        description=(
            "질문 분류 결과. "
            "'character': 특정 캐릭터의 레벨/직업/스탯/장비 등 캐릭터 정보 조회, "
            "'knowledge': 메이플스토리 공략/아이템/보스/이벤트/공지 등 게임 정보 검색, "
            "'character_knowledge': 캐릭터 정보를 바탕으로 한 공략/추천/비교, "
            "'chat': 인사/잡담 등 일반 대화"
        )
    )


async def classify_route(
    messages: list[BaseMessage], config: RunnableConfig | None = None
) -> Route:
    """최근 대화 맥락을 포함해 사용자의 마지막 질문을 분류합니다.

    보조 모델(temperature 0)의 구조화 출력으로 결정적 분류를 수행합니다.
    """
    structured_llm = get_utility_llm().with_structured_output(RouteDecision)

    prompt = ChatPromptTemplate.from_messages([
        ("system", get_prompt(PromptTemplate.ROUTE_SYSTEM, model="gemini")),
        MessagesPlaceholder(variable_name="messages"),
    ])

    chain = prompt | structured_llm
    result = await chain.ainvoke(
        {"messages": messages[-_ROUTE_CONTEXT_WINDOW:]}, config=config
    )
    if not isinstance(result, RouteDecision):
        raise TypeError(f"예상치 못한 라우팅 응답 타입: {type(result)}")
    return result.route


async def route_node(state: MainState, config: RunnableConfig | None = None) -> dict:
    """질문을 분류해 state["route"]에 기록합니다.

    분류 실패 시 chat으로 폴백하여 요청 전체가 실패하지 않도록 방어합니다.
    """
    question = state["messages"][-1].text

    try:
        route = await classify_route(state["messages"], config)
    except Exception as e:
        logger.error(f"[Route] 분류 실패, chat으로 폴백: {e}")
        route = "chat"

    logger.info(f"[Route] 분류 결과: '{route}' | 질문: {question[:50]}...")
    return {"route": route}


def select_branches(state: MainState) -> list[str]:
    """분류 결과에 따라 다음에 실행할 노드 목록을 반환합니다. (Conditional Edge)"""
    return ROUTE_BRANCHES.get(state.get("route", "chat"), ["generate"])
