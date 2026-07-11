# tests/test_chat_models.py
"""
chat 앱 모델 및 커스텀 QuerySet 테스트

ChatSession, ChatMessage, MessageMetadata 모델의 CRUD와
ChatSessionQuerySet의 커스텀 조회 메서드를 테스트합니다.
"""

import uuid

import pytest

from django.contrib.auth.models import User

from apps.chat.models import ChatMessage, ChatSession, MessageMetadata
from common.exceptions.chat import InvalidSessionId, SessionNotFound


@pytest.mark.django_db(transaction=True)
class TestChatSessionModel:
    """ChatSession 모델 기본 동작 테스트."""

    @pytest.fixture(autouse=True)
    def _setup(self, db) -> None:
        self.user = User.objects.create_user(
            username="chat_user", password="password123"
        )

    def test_create_session_with_user(self) -> None:
        """로그인 사용자의 세션이 정상 생성되어야 합니다."""
        session = ChatSession.objects.create(user=self.user)
        assert session.session_id is not None
        assert session.user == self.user

    def test_create_anonymous_session(self) -> None:
        """비로그인(익명) 세션이 user=None으로 정상 생성되어야 합니다."""
        session = ChatSession.objects.create(user=None)
        assert session.session_id is not None
        assert session.user is None

    def test_session_id_is_uuid(self) -> None:
        """session_id가 유효한 UUID 형식이어야 합니다."""
        session = ChatSession.objects.create(user=self.user)
        # UUID 형식 검증
        parsed = uuid.UUID(str(session.session_id))
        assert parsed == session.session_id

    def test_str_representation(self) -> None:
        """__str__이 session_id의 앞 8자를 반환해야 합니다."""
        session = ChatSession.objects.create(user=self.user)
        assert str(session) == str(session.session_id)[:8]

    def test_cascade_delete(self) -> None:
        """사용자 삭제 시 관련 세션도 함께 삭제되어야 합니다."""
        ChatSession.objects.create(user=self.user)
        user_pk = self.user.pk
        assert ChatSession.objects.filter(user_id=user_pk).count() == 1
        self.user.delete()
        assert ChatSession.objects.filter(user_id=user_pk).count() == 0


@pytest.mark.django_db(transaction=True)
class TestChatSessionQuerySet:
    """ChatSessionQuerySet 커스텀 메서드 테스트."""

    @pytest.fixture(autouse=True)
    def _setup(self, db) -> None:
        self.user = User.objects.create_user(
            username="qs_chat_user", password="password123"
        )
        self.session = ChatSession.objects.create(user=self.user)

    def test_get_by_uuid_or_raise_success(self) -> None:
        """유효한 UUID로 세션을 정상 조회해야 합니다."""
        result = ChatSession.objects.get_by_uuid_or_raise(
            str(self.session.session_id)
        )
        assert result.session_id == self.session.session_id

    def test_get_by_uuid_or_raise_invalid_uuid(self) -> None:
        """잘못된 UUID 형식이면 InvalidSessionId 예외가 발생해야 합니다."""
        with pytest.raises(InvalidSessionId):
            ChatSession.objects.get_by_uuid_or_raise("not-a-valid-uuid")

    def test_get_by_uuid_or_raise_not_found(self) -> None:
        """존재하지 않는 UUID이면 SessionNotFound 예외가 발생해야 합니다."""
        fake_uuid = str(uuid.uuid4())
        with pytest.raises(SessionNotFound):
            ChatSession.objects.get_by_uuid_or_raise(fake_uuid)

    @pytest.mark.asyncio
    async def test_aget_by_uuid_or_raise_success(self) -> None:
        """비동기 버전으로 유효한 UUID 세션을 정상 조회해야 합니다."""
        result = await ChatSession.objects.aget_by_uuid_or_raise(
            str(self.session.session_id)
        )
        assert result.session_id == self.session.session_id

    @pytest.mark.asyncio
    async def test_aget_by_uuid_or_raise_invalid_uuid(self) -> None:
        """비동기 버전에서 잘못된 UUID 형식 시 InvalidSessionId 예외."""
        with pytest.raises(InvalidSessionId):
            await ChatSession.objects.aget_by_uuid_or_raise("invalid-format")

    @pytest.mark.asyncio
    async def test_aget_by_uuid_or_raise_not_found(self) -> None:
        """비동기 버전에서 존재하지 않는 UUID 시 SessionNotFound 예외."""
        with pytest.raises(SessionNotFound):
            await ChatSession.objects.aget_by_uuid_or_raise(str(uuid.uuid4()))


@pytest.mark.django_db(transaction=True)
class TestChatMessageModel:
    """ChatMessage 모델 기본 동작 테스트."""

    @pytest.fixture(autouse=True)
    def _setup(self, db) -> None:
        self.user = User.objects.create_user(
            username="msg_user", password="password123"
        )
        self.session = ChatSession.objects.create(user=self.user)

    def test_create_user_message(self) -> None:
        """사용자 메시지가 정상 생성되어야 합니다."""
        msg = ChatMessage.objects.create(
            session=self.session,
            role="user",
            content="안녕하세요!",
        )
        assert msg.role == "user"
        assert msg.content == "안녕하세요!"
        assert msg.session == self.session

    def test_create_assistant_message(self) -> None:
        """어시스턴트 메시지가 정상 생성되어야 합니다."""
        msg = ChatMessage.objects.create(
            session=self.session,
            role="assistant",
            content="반갑습니다! 무엇을 도와드릴까요?",
        )
        assert msg.role == "assistant"

    def test_messages_ordering_by_created_at(self) -> None:
        """메시지가 생성 순서대로 정렬되어야 합니다."""
        msg1 = ChatMessage.objects.create(
            session=self.session, role="user", content="첫 번째"
        )
        msg2 = ChatMessage.objects.create(
            session=self.session, role="assistant", content="두 번째"
        )
        messages = list(
            ChatMessage.objects.filter(session=self.session).order_by("created_at")
        )
        assert messages[0].content == "첫 번째"
        assert messages[1].content == "두 번째"

    def test_str_representation(self) -> None:
        """__str__이 'role: content[:50]' 형식이어야 합니다."""
        msg = ChatMessage.objects.create(
            session=self.session,
            role="user",
            content="테스트 메시지입니다.",
        )
        assert str(msg).startswith("user:")

    def test_cascade_delete_with_session(self) -> None:
        """세션 삭제 시 관련 메시지도 함께 삭제되어야 합니다."""
        ChatMessage.objects.create(
            session=self.session, role="user", content="삭제될 메시지"
        )
        assert ChatMessage.objects.count() == 1
        self.session.delete()
        assert ChatMessage.objects.count() == 0


@pytest.mark.django_db(transaction=True)
class TestMessageMetadataModel:
    """MessageMetadata 모델 기본 동작 테스트."""

    @pytest.fixture(autouse=True)
    def _setup(self, db) -> None:
        self.user = User.objects.create_user(
            username="meta_user", password="password123"
        )
        session = ChatSession.objects.create(user=self.user)
        self.message = ChatMessage.objects.create(
            session=session,
            role="assistant",
            content="AI 응답",
        )

    def test_create_metadata(self) -> None:
        """메타데이터가 정상 생성되어야 합니다."""
        meta = MessageMetadata.objects.create(
            message=self.message,
            thinking="이런 저런 사고 과정...",
            response_time_ms=1500,
            model_name="qwen-test",
        )
        assert meta.thinking == "이런 저런 사고 과정..."
        assert meta.response_time_ms == 1500
        assert meta.model_name == "qwen-test"

    def test_metadata_one_to_one(self) -> None:
        """메시지와 메타데이터가 OneToOne 관계로 연결되어야 합니다."""
        meta = MessageMetadata.objects.create(
            message=self.message,
            thinking="사고 과정",
        )
        assert self.message.metadata == meta

    def test_metadata_cascade_delete(self) -> None:
        """메시지 삭제 시 메타데이터도 삭제되어야 합니다."""
        MessageMetadata.objects.create(
            message=self.message,
            thinking="삭제될 메타데이터",
        )
        assert MessageMetadata.objects.count() == 1
        self.message.delete()
        assert MessageMetadata.objects.count() == 0

    def test_nullable_fields(self) -> None:
        """선택 필드(thinking, tokens_used 등)가 null을 허용해야 합니다."""
        meta = MessageMetadata.objects.create(
            message=self.message,
            thinking=None,
            response_time_ms=None,
            tokens_used=None,
        )
        assert meta.thinking is None
        assert meta.response_time_ms is None
        assert meta.tokens_used is None
