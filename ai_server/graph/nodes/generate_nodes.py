# ai_server/graph/nodes/generate_nodes.py
"""
최종 답변 생성 노드.

모든 경로(잡담/지식/캐릭터/지식+캐릭터)가 이 노드 하나로 모입니다.
분기에서 수집한 참고 자료(지식 문서, 캐릭터 정보)를 시스템 프롬프트에 넣고
답변용 채팅 모델(ANSWER_LLM_PROVIDER, 비우면 LLM_PROVIDER)로 답변을 생성합니다.

채팅 모델을 사용하므로 토큰이 on_chat_model_stream 이벤트로 스트리밍됩니다.
스트리밍 중 재시도하면 같은 토큰이 다시 전송되므로 이 노드에는 RetryPolicy를 걸지 않습니다.
"""

import logging
from typing import Any

from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableConfig

from ai_server.config import settings
from ai_server.graph.state.main_state import MainState
from ai_server.llm.factory import get_answer_llm
from ai_server.prompts import PromptTemplate, get_prompt

logger = logging.getLogger("GenerateNodes")

NO_REFERENCES = "(이번 질문에 대한 참고 자료 없음)"


def build_user_profile(user_context: dict[str, Any] | None) -> str:
    """사용자 정보를 프롬프트용 문자열로 변환합니다."""
    main_character = (user_context or {}).get("main_character") or {}
    name = main_character.get("character_name")
    if not name:
        return "연동된 대표 캐릭터 없음"

    world = main_character.get("world_name")
    return f"대표 캐릭터: {name}" + (f" ({world})" if world else "")


def build_references(state: MainState) -> str:
    """분기에서 수집한 캐릭터 정보와 검색 문서를 하나의 참고 자료로 합칩니다."""
    sections = []
    if character_context := state.get("character_context"):
        sections.append(f"## 캐릭터 정보 (넥슨 Open API)\n{character_context}")
    if knowledge_context := state.get("knowledge_context"):
        sections.append(f"## 검색된 문서\n{knowledge_context}")
    return "\n\n".join(sections) or NO_REFERENCES


async def generate_node(state: MainState, config: RunnableConfig | None = None) -> dict:
    """참고 자료와 대화 맥락을 바탕으로 최종 답변을 생성합니다."""
    prompt_model = "local" if settings.model.answer_provider == "local" else "gemini"
    prompt = ChatPromptTemplate.from_messages([
        ("system", get_prompt(PromptTemplate.GENERATE_SYSTEM, model=prompt_model)),
        MessagesPlaceholder(variable_name="messages"),
    ])

    references = build_references(state)
    logger.info(
        f"[Generate] 답변 생성 시작 | route: {state.get('route', '')} "
        f"| 참고 자료: {len(references)}자"
    )

    chain = prompt | get_answer_llm()
    response = await chain.ainvoke(
        {
            "user_profile": build_user_profile(state.get("user_context")),
            "references": references,
            "messages": state["messages"],
        },
        config=config,
    )
    return {"messages": [AIMessage(content=response.text)]}
