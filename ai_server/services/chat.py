"""
챗 API 비즈니스 로직

요청을 그래프 입력으로 변환하고, 그래프 실행 결과를 동기 응답 또는 SSE 이벤트로 변환합니다.

SSE 이벤트 규격 (모든 줄은 "data: <JSON>\\n\\n" 형식):
  {"type": "status", "content": "..."}     노드 진행 상태 (예: "관련 문서를 찾고 있어요")
  {"type": "route", "route": "..."}        질문 분류 결과 (chat/knowledge/character/character_knowledge)
  {"type": "token", "content": "..."}      답변 토큰 (generate 노드 출력만)
  {"type": "sources", "sources": [...]}    답변 근거 문서 (있을 때만, 답변 뒤에 1회)
  {"type": "error", "content": "..."}      처리 실패
  data: [DONE]                             스트림 종료 (항상 마지막에 1회)
"""

import json
import logging
from collections.abc import AsyncIterator
from typing import Any

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

from ai_server.common.observability import get_langfuse_callback
from ai_server.config import settings
from ai_server.schemas.chat import ChatResponse, QueryRequest

logger = logging.getLogger(__name__)

# 노드가 시작될 때 클라이언트에 보낼 진행 상태 문구 (노드 이름 → 문구)
STATUS_MESSAGES: dict[str, str] = {
    "route": "질문을 살펴보고 있어요",
    "rewrite": "검색어를 정리하고 있어요",
    "retrieve": "관련 문서를 찾고 있어요",
    "extract_character": "어떤 캐릭터인지 확인하고 있어요",
    "fetch_character": "캐릭터 정보를 조회하고 있어요",
    "generate": "답변을 작성하고 있어요",
}

# 사용자에게 토큰을 스트리밍하는 노드 (다른 노드의 LLM 출력은 내부용이므로 숨깁니다)
ANSWER_NODE = "generate"

STREAM_ERROR_MESSAGE = "내부 서버 오류가 발생했습니다."


def build_langchain_config(session_id: str | None = None) -> dict:
    """Langchain 호출 시 공통 설정을 생성합니다."""
    config: dict[str, Any] = {}
    if session_id:
        config["metadata"] = {"langfuse_session_id": session_id}

    callbacks = []
    langfuse_handler = get_langfuse_callback()
    if langfuse_handler:
        callbacks.append(langfuse_handler)

    if callbacks:
        config["callbacks"] = callbacks

    return config


def build_graph_input(request: QueryRequest) -> dict[str, Any]:
    """요청의 이전 대화와 현재 질문을 그래프 입력 상태로 변환합니다.

    이전 대화는 최근 history_max_messages개만 사용하고,
    메시지마다 history_message_max_chars까지만 잘라 토큰 사용량을 제한합니다.
    """
    max_messages = settings.chat.history_max_messages
    max_chars = settings.chat.history_message_max_chars
    history = request.history[-max_messages:] if max_messages > 0 else []

    messages: list[BaseMessage] = []
    for item in history:
        content = item.content[:max_chars]
        if not content.strip():
            continue
        message_cls = HumanMessage if item.role == "user" else AIMessage
        messages.append(message_cls(content=content))
    messages.append(HumanMessage(content=request.message))

    user_context = (
        request.user_context.model_dump(exclude_none=True)
        if request.user_context
        else {}
    )
    return {"messages": messages, "user_context": user_context}


def format_sse(payload: dict[str, Any] | str) -> str:
    """SSE data 라인을 생성합니다."""
    data = payload if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False)
    return f"data: {data}\n\n"


async def generate_chat_response(graph: Any, request: QueryRequest) -> ChatResponse:
    """그래프를 끝까지 실행해 최종 답변을 반환합니다."""
    output = await graph.ainvoke(
        build_graph_input(request),
        config=build_langchain_config(request.session_id),
    )
    return ChatResponse(
        response=output["messages"][-1].text.strip(),
        route=output.get("route", ""),
        sources=output.get("sources") or [],
    )


async def stream_chat_events(graph: Any, request: QueryRequest) -> AsyncIterator[str]:
    """그래프 실행 이벤트를 SSE 문자열로 변환해 전달합니다."""
    sources: list[dict[str, Any]] = []

    try:
        async for event in graph.astream_events(
            build_graph_input(request),
            config=build_langchain_config(request.session_id),
            version="v2",
        ):
            kind = event["event"]
            name = event.get("name", "")
            node = event.get("metadata", {}).get("langgraph_node", "")

            # 노드 자체의 시작/종료 이벤트만 사용합니다. (노드 내부 체인 이벤트는 name이 다릅니다)
            if kind == "on_chain_start" and name == node and name in STATUS_MESSAGES:
                yield format_sse({"type": "status", "content": STATUS_MESSAGES[name]})

            elif kind == "on_chain_end" and name == node == "route":
                route = (event["data"].get("output") or {}).get("route", "")
                yield format_sse({"type": "route", "route": route})

            elif kind == "on_chat_model_stream" and node == ANSWER_NODE:
                text = event["data"]["chunk"].text
                if text:
                    yield format_sse({"type": "token", "content": text})

            # 부모 실행이 없는 종료 이벤트 = 그래프 전체 종료. 최종 상태에서 근거 문서를 꺼냅니다.
            elif kind == "on_chain_end" and not event.get("parent_ids"):
                final_state = event["data"].get("output") or {}
                sources = final_state.get("sources") or []

        if sources:
            yield format_sse({"type": "sources", "sources": sources})

    except Exception as e:
        logger.error(f"스트리밍 중 에러: {e}", exc_info=True)
        yield format_sse({"type": "error", "content": STREAM_ERROR_MESSAGE})

    yield format_sse("[DONE]")
