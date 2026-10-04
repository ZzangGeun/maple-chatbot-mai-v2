# tests/test_chat_services.py
"""
chat 서비스 테스트

AI 서버로 보내는 요청 본문(이전 대화, 대표 캐릭터)과
SSE 스트림 중계·저장 동작을 검증합니다. AI 서버 통신은 가짜 aiohttp 세션으로 대체합니다.
"""

import json
from typing import Any

import pytest
from django.contrib.auth.models import AnonymousUser, User
from django.test import AsyncClient

from apps.auth.models import UserProfile
from apps.character.models import CharacterLink
from apps.chat import services
from apps.chat.models import ChatMessage, ChatSession, MessageMetadata

SOURCES = [{"index": 1, "title": "썬데이 메이플", "url": "https://example.com/1"}]


def _line(payload: dict | str) -> str:
    data = payload if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False)
    return f"data: {data}"


class _FakeResponse:
    def __init__(self, status: int, lines: list[str], body: dict | None = None) -> None:
        self.status = status
        self.content = self._iterate(lines)
        self._body = body or {}

    @staticmethod
    async def _iterate(lines: list[str]):
        for line in lines:
            yield (line + "\n").encode("utf-8")

    async def json(self) -> dict:
        return self._body

    async def text(self) -> str:
        return json.dumps(self._body)


class _FakeResponseContext:
    def __init__(self, response: _FakeResponse) -> None:
        self._response = response

    async def __aenter__(self) -> _FakeResponse:
        return self._response

    async def __aexit__(self, *exc: Any) -> bool:
        return False


class _FakeClientSession:
    def __init__(self, response: _FakeResponse, captured: dict) -> None:
        self._response = response
        self._captured = captured

    async def __aenter__(self) -> "_FakeClientSession":
        return self

    async def __aexit__(self, *exc: Any) -> bool:
        return False

    def post(self, url: str, json: dict, headers: dict | None = None) -> _FakeResponseContext:
        self._captured["url"] = url
        self._captured["json"] = json
        self._captured["headers"] = headers or {}
        return _FakeResponseContext(self._response)


@pytest.fixture
def fake_ai_server(monkeypatch: pytest.MonkeyPatch):
    """AI 서버 응답을 지정하고, 보낸 요청 본문을 기록하는 헬퍼를 반환합니다."""

    def install(status: int = 200, lines: list[str] | None = None, body: dict | None = None) -> dict:
        captured: dict = {}
        response = _FakeResponse(status, lines or [], body)
        monkeypatch.setattr(
            services.aiohttp,
            "ClientSession",
            lambda *args, **kwargs: _FakeClientSession(response, captured),
        )
        return captured

    return install


async def _collect(generator) -> list[Any]:
    """SSE 청크를 모아 이벤트 목록(JSON 또는 "[DONE]")으로 변환합니다."""
    events = []
    async for chunk in generator:
        assert chunk.endswith("\n\n")
        data = chunk.strip()[len("data: "):]
        events.append(data if data == "[DONE]" else json.loads(data))
    return events


def _of_type(events: list[Any], event_type: str) -> list[dict]:
    return [e for e in events if isinstance(e, dict) and e.get("type") == event_type]


@pytest.mark.django_db(transaction=True)
class TestAiPayload:
    """AI 서버에 보내는 이전 대화와 사용자 정보."""

    @pytest.fixture(autouse=True)
    def _setup(self, db) -> None:
        self.user = User.objects.create_user(username="payload_user", password="password123")
        self.session = ChatSession.objects.create(user=self.user)

    @pytest.mark.asyncio
    async def test_recent_history_is_oldest_first_and_skips_empty(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(services, "HISTORY_MAX_MESSAGES", 3)
        for role, content in [
            ("user", "q1"),
            ("assistant", "a1"),
            ("assistant", ""),  # 실패해 비어 있는 답변
            ("user", "q2"),
            ("assistant", "a2"),
        ]:
            await ChatMessage.objects.acreate(session=self.session, role=role, content=content)

        history = await services.get_recent_history(self.session)

        assert history == [
            {"role": "assistant", "content": "a1"},
            {"role": "user", "content": "q2"},
            {"role": "assistant", "content": "a2"},
        ]

    @pytest.mark.asyncio
    async def test_user_context_prefers_linked_main_character(self) -> None:
        await UserProfile.objects.acreate(user=self.user, maple_nickname="가입닉네임")
        await CharacterLink.objects.acreate(
            user=self.user,
            character_name="연동캐릭터",
            ocid="ocid-1",
            world_name="루나",
            is_main=True,
        )

        context = await services.get_user_context(self.user)

        assert context == {
            "main_character": {
                "character_name": "연동캐릭터",
                "world_name": "루나",
                "ocid": "ocid-1",
            }
        }

    @pytest.mark.asyncio
    async def test_user_context_falls_back_to_signup_nickname(self) -> None:
        await UserProfile.objects.acreate(user=self.user, maple_nickname="가입닉네임")

        context = await services.get_user_context(self.user)

        assert context == {"main_character": {"character_name": "가입닉네임"}}

    @pytest.mark.asyncio
    async def test_user_context_is_empty_for_anonymous(self) -> None:
        assert await services.get_user_context(AnonymousUser()) == {}
        assert await services.get_user_context(None) == {}


@pytest.mark.django_db(transaction=True)
class TestStreamMessageGenerator:
    """AI 서버 SSE 스트림 중계와 저장."""

    @pytest.fixture(autouse=True)
    def _setup(self, db) -> None:
        self.user = User.objects.create_user(username="stream_user", password="password123")
        UserProfile.objects.create(user=self.user, maple_nickname="스트림캐릭터")
        self.session = ChatSession.objects.create(user=self.user)
        ChatMessage.objects.create(session=self.session, role="user", content="이전 질문")
        ChatMessage.objects.create(session=self.session, role="assistant", content="이전 답변")

    async def _assistant_messages(self) -> list[ChatMessage]:
        return [
            m
            async for m in ChatMessage.objects.filter(
                session=self.session, role="assistant"
            ).order_by("created_at", "id")
        ]

    @pytest.mark.asyncio
    async def test_relays_events_and_saves_answer_with_metadata(self, fake_ai_server) -> None:
        captured = fake_ai_server(
            lines=[
                _line({"type": "status", "content": "관련 문서를 찾고 있어요"}),
                _line({"type": "route", "route": "knowledge"}),
                _line({"type": "token", "content": "안녕"}),
                "",
                _line({"type": "token", "content": "하담"}),
                _line({"type": "sources", "sources": SOURCES}),
                _line("[DONE]"),
            ]
        )

        events = await _collect(
            services.stream_message_generator(self.session, "새 질문", self.user)
        )

        # 받은 이벤트를 그대로 전달하고, 마지막에 [DONE]을 한 번 보냅니다.
        assert [t["content"] for t in _of_type(events, "token")] == ["안녕", "하담"]
        assert _of_type(events, "status") and _of_type(events, "route")
        assert _of_type(events, "sources")[0]["sources"] == SOURCES
        assert events.count("[DONE]") == 1 and events[-1] == "[DONE]"

        # 이전 대화와 대표 캐릭터를 함께 보내고, 현재 질문은 history에 넣지 않습니다.
        payload = captured["json"]
        assert payload["message"] == "새 질문"
        assert payload["history"] == [
            {"role": "user", "content": "이전 질문"},
            {"role": "assistant", "content": "이전 답변"},
        ]
        assert payload["user_context"] == {"main_character": {"character_name": "스트림캐릭터"}}

        # 사용자 질문과 답변, 메타데이터가 저장됩니다.
        assert await ChatMessage.objects.filter(
            session=self.session, role="user", content="새 질문"
        ).aexists()
        answer = (await self._assistant_messages())[-1]
        assert answer.content == "안녕하담"
        metadata = await MessageMetadata.objects.aget(message=answer)
        assert metadata.route == "knowledge"
        assert metadata.sources == SOURCES
        assert metadata.response_time_ms is not None

    @pytest.mark.asyncio
    async def test_server_error_sends_notice_and_saves_no_answer(self, fake_ai_server) -> None:
        fake_ai_server(status=500)

        events = await _collect(
            services.stream_message_generator(self.session, "새 질문", self.user)
        )

        assert _of_type(events, "error")
        # 현재 프론트는 error 이벤트를 표시하지 않으므로 안내 문구를 token으로도 보냅니다.
        assert [t["content"] for t in _of_type(events, "token")] == [services.FAILURE_NOTICE]
        assert events[-1] == "[DONE]"
        # 질문은 저장되지만, 빈 답변은 남기지 않습니다.
        assert await ChatMessage.objects.filter(session=self.session, content="새 질문").aexists()
        assert [m.content for m in await self._assistant_messages()] == ["이전 답변"]

    @pytest.mark.asyncio
    async def test_upstream_error_keeps_partial_answer_and_notices_once(self, fake_ai_server) -> None:
        fake_ai_server(
            lines=[
                _line({"type": "token", "content": "부분 답변"}),
                _line({"type": "error", "content": "내부 서버 오류가 발생했습니다."}),
                _line("[DONE]"),
            ]
        )

        events = await _collect(
            services.stream_message_generator(self.session, "새 질문", self.user)
        )

        assert len(_of_type(events, "error")) == 1
        tokens = [t["content"] for t in _of_type(events, "token")]
        assert tokens == ["부분 답변", f"\n\n({services.FAILURE_NOTICE})"]
        assert events[-1] == "[DONE]"
        # 안내 문구는 저장하지 않고 실제로 받은 답변만 저장합니다.
        assert (await self._assistant_messages())[-1].content == "부분 답변"

    @pytest.mark.asyncio
    async def test_stream_cut_without_done_is_reported(self, fake_ai_server) -> None:
        fake_ai_server(lines=[_line({"type": "token", "content": "부분 답변"})])

        events = await _collect(
            services.stream_message_generator(self.session, "새 질문", self.user)
        )

        assert len(_of_type(events, "error")) == 1
        assert _of_type(events, "token")[-1]["content"] == f"\n\n({services.FAILURE_NOTICE})"
        assert events.count("[DONE]") == 1 and events[-1] == "[DONE]"
        assert (await self._assistant_messages())[-1].content == "부분 답변"


@pytest.mark.django_db(transaction=True)
class TestSendMessageAndViews:
    """동기 전송 경로와 뷰 연동."""

    @pytest.fixture(autouse=True)
    def _setup(self, db) -> None:
        self.user = User.objects.create_user(username="sync_user", password="password123")
        UserProfile.objects.create(user=self.user, maple_nickname="동기캐릭터")
        self.session = ChatSession.objects.create(user=self.user)

    @pytest.mark.asyncio
    async def test_send_message_saves_route_and_sources(self, fake_ai_server) -> None:
        captured = fake_ai_server(
            body={"response": "답변이담", "route": "knowledge", "sources": SOURCES}
        )

        _, assistant_msg, _ = await services.send_message_async(
            self.session, "질문", self.user
        )

        assert captured["url"].endswith("/generate")
        assert assistant_msg.content == "답변이담"
        metadata = await MessageMetadata.objects.aget(message=assistant_msg)
        assert metadata.route == "knowledge"
        assert metadata.sources == SOURCES

    @pytest.mark.asyncio
    async def test_stream_view_sends_logged_in_users_character(self, fake_ai_server) -> None:
        captured = fake_ai_server(
            lines=[_line({"type": "token", "content": "답변"}), _line("[DONE]")]
        )
        client = AsyncClient()
        await client.alogin(username="sync_user", password="password123")

        response = await client.post(
            f"/api/v1/chat/rooms/{self.session.session_id}/stream/",
            data={"content": "질문"},
            content_type="application/json",
        )
        body = b"".join([chunk async for chunk in response.streaming_content]).decode("utf-8")

        assert response.status_code == 200
        assert response["X-Accel-Buffering"] == "no"
        assert "data: [DONE]" in body
        assert captured["json"]["user_context"] == {
            "main_character": {"character_name": "동기캐릭터"}
        }

    @pytest.mark.asyncio
    async def test_get_messages_includes_sources(self) -> None:
        await ChatMessage.objects.acreate(session=self.session, role="user", content="질문")
        answer = await ChatMessage.objects.acreate(
            session=self.session, role="assistant", content="답변"
        )
        await MessageMetadata.objects.acreate(message=answer, route="knowledge", sources=SOURCES)

        client = AsyncClient()
        await client.alogin(username="sync_user", password="password123")
        response = await client.get(f"/api/v1/chat/rooms/{self.session.session_id}/messages")

        messages = response.json()["messages"]
        assert messages[1]["sources"] == SOURCES
        assert "sources" not in messages[0]
