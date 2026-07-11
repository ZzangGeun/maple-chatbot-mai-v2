# tests/test_chat_views.py
"""
chat 앱 뷰(엔드포인트) 통합 테스트

채팅 세션 CRUD 및 메시지 전송 API를 테스트합니다.
AI 서버 호출은 모킹 처리합니다.
"""

import json
import uuid

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from django.contrib.auth.models import User
from django.test import AsyncClient

from apps.chat.models import ChatMessage, ChatSession, MessageMetadata


@pytest.mark.django_db(transaction=True)
class TestRoomsDispatch:
    """
    /api/v1/chat/rooms 엔드포인트 테스트.
    GET: 세션 목록 조회, POST: 세션 생성
    """

    ROOMS_URL = "/api/v1/chat/rooms"

    @pytest.fixture(autouse=True)
    def _setup(self, db) -> None:
        self.user = User.objects.create_user(
            username="chat_view_user", password="password123"
        )

    @pytest.mark.asyncio
    async def test_get_rooms_authenticated(self) -> None:
        """로그인 사용자의 세션 목록을 정상 조회해야 합니다."""
        # 세션 미리 생성
        session = await ChatSession.objects.acreate(user=self.user)
        await ChatMessage.objects.acreate(
            session=session, role="user", content="테스트 메시지입니다"
        )

        client = AsyncClient()
        await client.alogin(username="chat_view_user", password="password123")
        response = await client.get(self.ROOMS_URL)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["rooms"]) == 1
        # 첫 메시지 기반 타이틀 확인
        assert "테스트 메시지입니다" in data["rooms"][0]["room_name"]

    @pytest.mark.asyncio
    async def test_get_rooms_anonymous(self) -> None:
        """비로그인 사용자는 빈 세션 목록을 받아야 합니다."""
        client = AsyncClient()
        response = await client.get(self.ROOMS_URL)
        assert response.status_code == 200
        data = response.json()
        assert data["rooms"] == []

    @pytest.mark.asyncio
    async def test_create_room(self) -> None:
        """POST 요청으로 새 세션을 생성해야 합니다."""
        client = AsyncClient()
        await client.alogin(username="chat_view_user", password="password123")
        response = await client.post(
            self.ROOMS_URL,
            data=json.dumps({"room_name": "새 대화방"}),
            content_type="application/json",
        )
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert "id" in data["room"]

    @pytest.mark.asyncio
    async def test_create_room_anonymous(self) -> None:
        """비로그인 사용자도 세션을 생성할 수 있어야 합니다(user=None)."""
        client = AsyncClient()
        response = await client.post(
            self.ROOMS_URL,
            data=json.dumps({}),
            content_type="application/json",
        )
        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_method_not_allowed(self) -> None:
        """PUT 요청은 405를 반환해야 합니다."""
        client = AsyncClient()
        response = await client.put(self.ROOMS_URL)
        assert response.status_code == 405


@pytest.mark.django_db(transaction=True)
class TestMessagesDispatch:
    """
    /api/v1/chat/rooms/{session_id}/messages 엔드포인트 테스트.
    GET: 메시지 목록 조회, POST: 메시지 전송
    """

    @pytest.fixture(autouse=True)
    def _setup(self, db) -> None:
        self.user = User.objects.create_user(
            username="msg_view_user", password="password123"
        )
        self.session = ChatSession.objects.create(user=self.user)
        self.messages_url = (
            f"/api/v1/chat/rooms/{self.session.session_id}/messages"
        )

    @pytest.mark.asyncio
    async def test_get_messages(self) -> None:
        """세션의 메시지 목록을 정상 조회해야 합니다."""
        # 메시지 추가
        user_msg = await ChatMessage.objects.acreate(
            session=self.session, role="user", content="안녕!"
        )
        assistant_msg = await ChatMessage.objects.acreate(
            session=self.session, role="assistant", content="반가워요!"
        )
        await MessageMetadata.objects.acreate(
            message=assistant_msg, thinking="사고 과정"
        )

        client = AsyncClient()
        response = await client.get(self.messages_url)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["messages"]) == 2
        assert data["messages"][0]["sender_type"] == "user"
        assert data["messages"][1]["sender_type"] == "assistant"

    @pytest.mark.asyncio
    async def test_get_messages_empty(self) -> None:
        """메시지가 없는 세션은 빈 목록을 반환해야 합니다."""
        client = AsyncClient()
        response = await client.get(self.messages_url)
        assert response.status_code == 200
        data = response.json()
        assert data["messages"] == []

    @pytest.mark.asyncio
    async def test_get_messages_invalid_session_id(self) -> None:
        """잘못된 세션 ID로 조회 시 에러를 반환해야 합니다."""
        client = AsyncClient()
        response = await client.get(
            "/api/v1/chat/rooms/not-a-uuid/messages"
        )
        # InvalidSessionId 예외 → ErrorHandlerMiddleware가 처리
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_get_messages_nonexistent_session(self) -> None:
        """존재하지 않는 세션 ID로 조회 시 404를 반환해야 합니다."""
        fake_uuid = str(uuid.uuid4())
        client = AsyncClient()
        response = await client.get(
            f"/api/v1/chat/rooms/{fake_uuid}/messages"
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    @patch("apps.chat.views.send_message_async", new_callable=AsyncMock)
    async def test_send_message(self, mock_send: AsyncMock) -> None:
        """메시지 전송 시 AI 서비스를 호출하고 200을 반환해야 합니다."""
        # AI 서비스 모킹: 저장된 assistant 메시지를 반환
        mock_msg = MagicMock()
        mock_msg.id = 100
        mock_msg.content = "AI 응답입니다"
        mock_msg.created_at.isoformat.return_value = "2026-06-07T15:00:00+09:00"
        mock_send.return_value = (mock_msg, mock_msg, {})

        client = AsyncClient()
        response = await client.post(
            self.messages_url,
            data=json.dumps({"message_content": "메이플 보스 추천해줘"}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        mock_send.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_send_message_invalid_json(self) -> None:
        """잘못된 JSON 요청은 AI 서비스를 호출하지 않고 400을 반환해야 합니다."""
        client = AsyncClient()
        response = await client.post(
            self.messages_url,
            data="not-json",
            content_type="application/json",
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_send_message_empty_content(self) -> None:
        """빈 메시지 전송 시 400을 반환해야 합니다."""
        client = AsyncClient()
        response = await client.post(
            self.messages_url,
            data=json.dumps({"message_content": ""}),
            content_type="application/json",
        )
        assert response.status_code == 400


@pytest.mark.django_db(transaction=True)
class TestRoomDetailDispatch:
    """
    /api/v1/chat/rooms/{session_id} 엔드포인트 테스트.
    DELETE: 세션 삭제
    """

    @pytest.fixture(autouse=True)
    def _setup(self, db) -> None:
        self.user = User.objects.create_user(
            username="del_user", password="password123"
        )
        self.session = ChatSession.objects.create(user=self.user)
        self.detail_url = f"/api/v1/chat/rooms/{self.session.session_id}"

    @pytest.mark.asyncio
    async def test_delete_session(self) -> None:
        """DELETE 요청으로 세션을 삭제해야 합니다."""
        client = AsyncClient()
        response = await client.delete(self.detail_url)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # DB에서 실제로 삭제되었는지 검증
        exists = await ChatSession.objects.filter(
            session_id=self.session.session_id
        ).aexists()
        assert exists is False

    @pytest.mark.asyncio
    async def test_delete_nonexistent_session(self) -> None:
        """존재하지 않는 세션 삭제 시 404를 반환해야 합니다."""
        fake_uuid = str(uuid.uuid4())
        client = AsyncClient()
        response = await client.delete(f"/api/v1/chat/rooms/{fake_uuid}")
        assert response.status_code == 404
