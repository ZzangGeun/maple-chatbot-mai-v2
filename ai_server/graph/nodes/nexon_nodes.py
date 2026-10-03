# ai_server/graph/nodes/nexon_nodes.py
"""
넥슨 API 서브 그래프 전용 노드 모음.

extract_character(조회 대상·필요 정보 파악) → fetch_character(넥슨 Open API 조회·요약) 순으로 실행되며,
답변 생성은 메인 그래프의 generate 노드가 담당합니다.
"""

import logging
from typing import Any

from langchain_core.messages import BaseMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel, Field

from ai_server.config import settings
from ai_server.graph.state.nexon_state import NexonState
from ai_server.graph.tools import character_context as cc
from ai_server.llm.factory import get_utility_llm
from ai_server.prompts import PromptTemplate, get_prompt
from common.exceptions.base import AppException
from common.exceptions.nexon import ApiRateLimitExceeded, CharacterNotFound
from common.nexon import NexonCache, NexonClient

logger = logging.getLogger("NexonNodes")

# 후속 질문("그 캐릭터 장비는?")에서도 캐릭터명을 찾을 수 있도록 최근 대화를 함께 봅니다.
_EXTRACT_CONTEXT_WINDOW = 6
# 한 질문에서 조회할 최대 정보 종류 수 (넥슨 API 호출 수 제한)
MAX_ASPECTS = 6

# Django와 같은 Redis 캐시를 쓰므로, 웹에서 검색한 캐릭터는 챗봇에서 다시 조회하지 않습니다.
_nexon_client = NexonClient(settings.api.nexon_api_key, cache=NexonCache(settings.redis_url))


class CharacterQuery(BaseModel):
    """캐릭터 질문 분석 결과를 구조화 출력으로 받기 위한 스키마."""

    character_name: str | None = Field(
        default=None,
        description="조회할 캐릭터 이름. 마지막 질문에 없으면 직전 대화에서 이어지는 캐릭터 이름, 없으면 null",
    )
    refers_to_self: bool = Field(
        default=False,
        description="'내 캐릭터', '내 스펙', '나'처럼 사용자 본인의 캐릭터를 묻는지 여부",
    )
    aspects: list[cc.CharacterAspect] = Field(
        default_factory=list,
        description="답변에 필요한 캐릭터 정보 종류 (여러 개 가능)",
    )


async def extract_character_query(
    messages: list[BaseMessage], config: RunnableConfig | None = None
) -> dict[str, Any]:
    """최근 대화를 보고 조회할 캐릭터와 필요한 정보 종류를 추출합니다."""
    prompt = ChatPromptTemplate.from_messages([
        ("system", get_prompt(PromptTemplate.INTENT_EXTRACT_SYSTEM, model="gemini")),
        MessagesPlaceholder(variable_name="messages"),
    ])
    chain = prompt | get_utility_llm().with_structured_output(CharacterQuery)
    result: CharacterQuery = await chain.ainvoke(
        {"messages": messages[-_EXTRACT_CONTEXT_WINDOW:]}, config=config
    )
    return result.model_dump()


def resolve_target(
    query: dict[str, Any], user_context: dict[str, Any] | None
) -> tuple[str, str, bool] | None:
    """조회할 캐릭터를 정합니다.

    Returns:
        (캐릭터명, OCID(모르면 빈 문자열), 대표 캐릭터 여부). 정할 수 없으면 None.
        질문에 다른 캐릭터명이 있으면 그 캐릭터를, 없거나 대표 캐릭터와 같으면 대표 캐릭터를 조회합니다.
    """
    main = (user_context or {}).get("main_character") or {}
    main_name = (main.get("character_name") or "").strip()
    name = (query.get("character_name") or "").strip()

    if name and name.lower() != main_name.lower():
        return name, "", False
    if main_name:
        return main_name, main.get("ocid") or "", True
    return None


def select_aspects(query: dict[str, Any], route: str) -> list[str]:
    """조회할 정보 종류를 고릅니다. 질문에서 고르지 못했으면 경로별 기본값을 사용합니다."""
    aspects = [
        aspect
        for aspect in dict.fromkeys(query.get("aspects") or [])
        if aspect in cc.ASPECT_PATHS
    ]
    if not aspects:
        aspects = cc.DEFAULT_ASPECTS.get(route, ["stat"])
    return aspects[:MAX_ASPECTS]


async def extract_character_node(
    state: NexonState, config: RunnableConfig | None = None
) -> dict:
    """질문에서 조회할 캐릭터와 필요한 정보 종류를 추출하는 노드."""
    try:
        query = await extract_character_query(state["messages"], config)
    except Exception as e:
        # 추출에 실패하면 캐릭터명을 비워 둡니다.
        # (대표 캐릭터가 있으면 대표 캐릭터를, 없으면 '캐릭터명을 알려 달라'는 안내 경로를 탑니다.)
        logger.error(f"[ExtractCharacter] 질문 분석 실패: {e}")
        query = {"character_name": None, "refers_to_self": False, "aspects": []}

    logger.info(f"[ExtractCharacter] 분석 결과: {query}")
    return {"character_query": query}


async def fetch_character_node(state: NexonState) -> dict:
    """넥슨 Open API로 필요한 정보만 조회해 답변 모델용 참고 자료로 요약하는 노드."""
    query = state.get("character_query") or {}
    target = resolve_target(query, state.get("user_context"))
    if target is None:
        return {"character_context": cc.describe_missing_target(bool(query.get("refers_to_self")))}

    name, ocid, is_main = target
    aspects = select_aspects(query, state.get("route", "character"))
    logger.info(f"[FetchCharacter] '{name}' 조회 (대표 캐릭터: {is_main}) | 정보: {aspects}")

    try:
        result = await _nexon_client.fetch_character(
            cc.paths_for(aspects), character_name=name, ocid=ocid
        )
    except CharacterNotFound:
        return {"character_context": cc.describe_not_found(name)}
    except ApiRateLimitExceeded:
        return {"character_context": cc.describe_api_error(name, rate_limited=True)}
    except AppException as e:
        logger.error(f"[FetchCharacter] '{name}' 조회 실패: {e.message}")
        return {"character_context": cc.describe_api_error(name)}

    if result.failed:
        logger.warning(f"[FetchCharacter] 일부 정보 조회 실패: {list(result.failed)}")

    try:
        context = cc.build_character_context(name, result, aspects, is_main_character=is_main)
    except Exception:
        # 응답 형식이 예상과 달라 요약에 실패해도 답변 전체가 실패하지 않도록 합니다.
        logger.exception(f"[FetchCharacter] '{name}' 정보 요약 실패")
        context = cc.describe_api_error(name)

    return {"character_context": context}
