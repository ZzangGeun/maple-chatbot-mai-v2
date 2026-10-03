# tests/test_ai_chat_graph.py
"""
AI 서버 대화 그래프 및 챗 API 테스트

외부 호출(Gemini, 벡터 검색, 넥슨 API)은 모두 가짜로 대체하고,
네 가지 경로(chat/knowledge/character/character_knowledge)가 답변을 스트리밍하는지 검증합니다.
"""

import json
from typing import Any
from unittest.mock import AsyncMock

import httpx
import pytest
from fastapi import FastAPI
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.messages import AIMessage, HumanMessage

from ai_server.api.router import api_router
from ai_server.graph.builder.main_builder import build_main_graph
from ai_server.graph.nodes import generate_nodes, nexon_nodes, rag_nodes, route_nodes
from ai_server.rag.documents import Chunk
from ai_server.schemas.chat import QueryRequest
from ai_server.services import chat as chat_service
from common.nexon import CharacterFetchResult

ANSWER = "반갑담! 답변이담."

KNOWLEDGE_DOC = Chunk(
    chunk_id="notice:event:1#0",
    text="썬데이 메이플 이벤트 내용",
    metadata={
        "doc_id": "notice:event:1",
        "title": "썬데이 메이플",
        "category": "event",
        "url": "https://maplestory.nexon.com/News/Event/1",
        "date": "2026-10-04",
    },
)

CHARACTER_RESULT = CharacterFetchResult(
    ocid="test-ocid",
    responses={
        "/character/basic": {
            "character_name": "테스트캐릭터",
            "character_level": 285,
            "character_class": "아델",
            "world_name": "스카니아",
        },
        "/character/stat": {"final_stat": [{"stat_name": "전투력", "stat_value": "12345678"}]},
    },
)


@pytest.fixture
def fakes(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    """그래프가 호출하는 외부 의존성을 가짜로 바꾸고, 답변 노드가 받은 상태를 기록합니다."""
    recorded: dict[str, Any] = {"route": "chat", "generate_states": []}

    async def fake_classify(messages, config=None):
        return recorded["route"]

    real_build_references = generate_nodes.build_references

    def spy_build_references(state):
        recorded["generate_states"].append(state)
        return real_build_references(state)

    recorded["search"] = AsyncMock(return_value=[KNOWLEDGE_DOC])
    recorded["fetch"] = AsyncMock(return_value=CHARACTER_RESULT)

    monkeypatch.setattr(route_nodes, "classify_route", fake_classify)
    monkeypatch.setattr(rag_nodes, "rewrite_query", AsyncMock(return_value="재작성된 질문"))
    monkeypatch.setattr(rag_nodes, "search_documents", recorded["search"])
    monkeypatch.setattr(
        nexon_nodes,
        "extract_character_query",
        AsyncMock(return_value={"character_name": "테스트캐릭터", "aspects": ["stat"]}),
    )
    monkeypatch.setattr(nexon_nodes._nexon_client, "fetch_character", recorded["fetch"])
    monkeypatch.setattr(
        generate_nodes, "get_answer_llm", lambda: FakeListChatModel(responses=[ANSWER])
    )
    monkeypatch.setattr(generate_nodes, "build_references", spy_build_references)
    return recorded


def _make_app() -> FastAPI:
    app = FastAPI()
    app.include_router(api_router)
    app.state.graph = build_main_graph()
    return app


async def _post(path: str, body: dict) -> httpx.Response:
    transport = httpx.ASGITransport(app=_make_app())
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.post(path, json=body)


def _parse_sse(text: str) -> list[Any]:
    events = []
    for block in text.split("\n\n"):
        block = block.strip()
        if not block.startswith("data: "):
            continue
        data = block[len("data: "):]
        events.append(data if data == "[DONE]" else json.loads(data))
    return events


def _of_type(events: list[Any], event_type: str) -> list[dict]:
    return [e for e in events if isinstance(e, dict) and e.get("type") == event_type]


REQUEST_BODY = {
    "session_id": "session-1",
    "message": "질문입니다",
    "history": [
        {"role": "user", "content": "이전 질문"},
        {"role": "assistant", "content": "이전 답변"},
    ],
    "user_context": {"main_character": {"character_name": "테스트캐릭터", "world_name": "스카니아"}},
}


# ---------------------------------------------------------------------------
# /stream: 네 가지 경로 모두 답변이 스트리밍되어야 합니다.
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("route", "expects_knowledge", "expects_character"),
    [
        ("chat", False, False),
        ("knowledge", True, False),
        ("character", False, True),
        ("character_knowledge", True, True),
    ],
)
async def test_stream_answers_for_every_route(
    fakes: dict[str, Any], route: str, expects_knowledge: bool, expects_character: bool
) -> None:
    fakes["route"] = route

    response = await _post("/stream", REQUEST_BODY)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    events = _parse_sse(response.text)

    # 답변 토큰을 이어 붙이면 전체 답변이 되어야 합니다.
    tokens = _of_type(events, "token")
    assert "".join(t["content"] for t in tokens) == ANSWER
    assert _of_type(events, "route") == [{"type": "route", "route": route}]
    assert not _of_type(events, "error")
    assert events[-1] == "[DONE]"

    # 진행 상태는 분기에 맞게 전송됩니다.
    statuses = [e["content"] for e in _of_type(events, "status")]
    assert chat_service.STATUS_MESSAGES["generate"] in statuses
    assert (chat_service.STATUS_MESSAGES["retrieve"] in statuses) is expects_knowledge
    assert (chat_service.STATUS_MESSAGES["fetch_character"] in statuses) is expects_character

    # 병렬 분기여도 답변 노드는 한 번만 실행되고, 두 분기의 결과를 모두 받습니다.
    assert len(fakes["generate_states"]) == 1
    state = fakes["generate_states"][0]
    assert bool(state.get("knowledge_context")) is expects_knowledge
    assert bool(state.get("character_context")) is expects_character
    if expects_character:
        # 원본 JSON 대신 요약된 참고 자료가 전달되어야 합니다.
        assert "사용자의 대표 캐릭터: 테스트캐릭터" in state["character_context"]
        assert "전투력: 12,345,678" in state["character_context"]

    # 근거 문서는 지식 검색을 거친 경우에만 답변 뒤에 전송됩니다.
    sources = _of_type(events, "sources")
    if expects_knowledge:
        assert sources[0]["sources"][0]["title"] == "썬데이 메이플"
        assert events.index(sources[0]) > events.index(tokens[-1])
    else:
        assert not sources


@pytest.mark.asyncio
async def test_stream_passes_history_and_user_context_to_generate(fakes: dict[str, Any]) -> None:
    await _post("/stream", REQUEST_BODY)

    state = fakes["generate_states"][0]
    contents = [m.text for m in state["messages"]]
    assert contents == ["이전 질문", "이전 답변", "질문입니다"]
    assert state["user_context"]["main_character"]["character_name"] == "테스트캐릭터"


@pytest.mark.asyncio
async def test_stream_sends_error_then_done_when_generation_fails(
    fakes: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    def broken_llm():
        raise RuntimeError("LLM 장애")

    monkeypatch.setattr(generate_nodes, "get_answer_llm", broken_llm)

    response = await _post("/stream", REQUEST_BODY)

    events = _parse_sse(response.text)
    assert _of_type(events, "error")
    assert not _of_type(events, "token")
    assert events[-1] == "[DONE]"


@pytest.mark.asyncio
async def test_stream_falls_back_to_chat_when_routing_fails(
    fakes: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    async def broken_classify(messages, config=None):
        raise RuntimeError("분류 실패")

    monkeypatch.setattr(route_nodes, "classify_route", broken_classify)

    response = await _post("/stream", REQUEST_BODY)

    events = _parse_sse(response.text)
    assert _of_type(events, "route") == [{"type": "route", "route": "chat"}]
    assert "".join(t["content"] for t in _of_type(events, "token")) == ANSWER


@pytest.mark.asyncio
async def test_knowledge_route_answers_without_documents_when_search_fails(
    fakes: dict[str, Any],
) -> None:
    fakes["route"] = "knowledge"
    fakes["search"].side_effect = RuntimeError("DB 연결 실패")

    response = await _post("/stream", REQUEST_BODY)

    events = _parse_sse(response.text)
    assert "".join(t["content"] for t in _of_type(events, "token")) == ANSWER
    assert not _of_type(events, "sources")
    assert not fakes["generate_states"][0].get("knowledge_context")


# ---------------------------------------------------------------------------
# /generate
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_generate_returns_answer_route_and_sources(fakes: dict[str, Any]) -> None:
    fakes["route"] = "knowledge"

    response = await _post("/generate", REQUEST_BODY)

    assert response.status_code == 200
    data = response.json()
    assert data["response"] == ANSWER
    assert data["route"] == "knowledge"
    assert data["sources"][0]["url"] == "https://maplestory.nexon.com/News/Event/1"


# ---------------------------------------------------------------------------
# 입력 변환 / 문서 포맷팅
# ---------------------------------------------------------------------------


def test_build_graph_input_trims_history(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(chat_service.settings.chat, "history_max_messages", 2)
    monkeypatch.setattr(chat_service.settings.chat, "history_message_max_chars", 5)
    request = QueryRequest(
        session_id="s",
        message="현재 질문",
        history=[
            {"role": "user", "content": "오래된 질문"},
            {"role": "assistant", "content": "  "},
            {"role": "assistant", "content": "아주 긴 이전 답변입니다"},
        ],
    )

    graph_input = chat_service.build_graph_input(request)

    messages = graph_input["messages"]
    # 최근 2개만 사용하고, 빈 메시지는 빼고, 메시지마다 5자까지 자릅니다.
    assert [type(m) for m in messages] == [AIMessage, HumanMessage]
    assert messages[0].content == "아주 긴 "
    assert messages[1].content == "현재 질문"
    assert graph_input["user_context"] == {}


def test_build_graph_input_without_history(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(chat_service.settings.chat, "history_max_messages", 0)
    request = QueryRequest(
        session_id="s",
        message="현재 질문",
        history=[{"role": "user", "content": "이전 질문"}],
    )

    graph_input = chat_service.build_graph_input(request)

    assert [m.content for m in graph_input["messages"]] == ["현재 질문"]

