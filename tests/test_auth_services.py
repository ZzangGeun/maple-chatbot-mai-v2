# tests/test_auth_services.py
"""
auth 앱 서비스 레이어 테스트

validate_signup_data, create_user_with_profile 등
비즈니스 로직의 정상/비정상 경로를 테스트합니다.
넥슨 API 호출은 모킹하여 외부 의존성을 제거합니다.

왜 transaction=True를 사용하는가:
    SQLite in-memory DB에서 비동기(async) ORM 호출을 할 때,
    Django가 별도 스레드에서 DB 접근을 시도하므로
    'database table is locked' 에러가 발생합니다.
    transaction=True로 설정하면 각 테스트가 별도 트랜잭션에서 실행되어
    이 문제를 회피할 수 있습니다.
"""

import pytest
from unittest.mock import AsyncMock, patch

from asgiref.sync import sync_to_async
from django.contrib.auth.models import User

from apps.auth.models import UserProfile
from apps.auth.services import create_user_with_profile, validate_signup_data


@pytest.mark.django_db(transaction=True)
class TestValidateSignupData:
    """회원가입 데이터 유효성 검사 서비스 테스트."""

    def _make_valid_data(self, **overrides) -> dict:
        """유효한 회원가입 데이터를 생성합니다."""
        data = {
            "user_id": "new_user_01",
            "password": "securepass123",
            "confirm_password": "securepass123",
            "maple_nickname": "신규캐릭터",
            "nexon_api_key": "valid_nexon_key",
        }
        data.update(overrides)
        return data

    @pytest.mark.asyncio
    @patch(
        "apps.auth.services.process_signup_with_key",
        new_callable=AsyncMock,
        return_value=("신규캐릭터", {"character_level": 300}),
    )
    async def test_valid_data_passes(self, mock_process: AsyncMock) -> None:
        """모든 조건을 충족하는 데이터는 (True, '')을 반환해야 합니다."""
        is_valid, error_msg = await validate_signup_data(self._make_valid_data())
        assert is_valid is True
        assert error_msg == ""
        mock_process.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_missing_required_fields(self) -> None:
        """필수 필드가 비어 있으면 실패해야 합니다."""
        is_valid, error_msg = await validate_signup_data(
            self._make_valid_data(maple_nickname="")
        )
        assert is_valid is False
        assert "필수 필드" in error_msg

    @pytest.mark.asyncio
    async def test_invalid_user_id_format(self) -> None:
        """아이디 형식이 맞지 않으면 실패해야 합니다."""
        is_valid, error_msg = await validate_signup_data(
            self._make_valid_data(user_id="ab")  # 6자 미만
        )
        assert is_valid is False
        assert "아이디는 6~20자" in error_msg

    @pytest.mark.asyncio
    async def test_short_password(self) -> None:
        """비밀번호가 8자 미만이면 실패해야 합니다."""
        is_valid, error_msg = await validate_signup_data(
            self._make_valid_data(password="short", confirm_password="short")
        )
        assert is_valid is False
        assert "8자 이상" in error_msg

    @pytest.mark.asyncio
    async def test_password_mismatch(self) -> None:
        """비밀번호와 확인 비밀번호가 다르면 실패해야 합니다."""
        is_valid, error_msg = await validate_signup_data(
            self._make_valid_data(confirm_password="different_pass")
        )
        assert is_valid is False
        assert "비밀번호와 비밀번호 확인이 일치하지 않습니다" in error_msg

    @pytest.mark.asyncio
    async def test_duplicate_username(self) -> None:
        """이미 존재하는 아이디로 가입하면 실패해야 합니다."""
        # 사전 조건: 동일 아이디 사용자를 동기 래퍼로 생성
        await sync_to_async(User.objects.create_user)(
            username="new_user_01", password="somepassword123"
        )
        is_valid, error_msg = await validate_signup_data(self._make_valid_data())
        assert is_valid is False
        assert "이미 존재하는 아이디" in error_msg

    @pytest.mark.asyncio
    async def test_duplicate_maple_nickname(self) -> None:
        """이미 사용 중인 메이플 닉네임이면 실패해야 합니다."""
        # 사전 조건: 동일 닉네임 프로필을 '다른' user_id로 생성
        existing_user = await sync_to_async(User.objects.create_user)(
            username="existing_user", password="somepassword123"
        )
        await UserProfile.objects.acreate(
            user=existing_user,
            maple_nickname="신규캐릭터",
            nexon_api_key="some_key",
        )
        # user_id는 중복이 아닌 값을 사용해야 닉네임 검사까지 도달
        is_valid, error_msg = await validate_signup_data(
            self._make_valid_data(user_id="unique_user_01")
        )
        assert is_valid is False
        assert "이미 사용 중인 메이플 닉네임" in error_msg

    @pytest.mark.asyncio
    @patch(
        "apps.auth.services.process_signup_with_key",
        new_callable=AsyncMock,
        return_value=None,
    )
    async def test_invalid_nexon_api_key(self, mock_process: AsyncMock) -> None:
        """유효하지 않은 넥슨 API 키를 사용하면 실패해야 합니다."""
        is_valid, error_msg = await validate_signup_data(self._make_valid_data())
        assert is_valid is False
        assert "유효하지 않은 넥슨 API 키" in error_msg

    @pytest.mark.asyncio
    @patch(
        "apps.auth.services.process_signup_with_key",
        new_callable=AsyncMock,
        return_value=("다른캐릭터", {"character_level": 300}),
    )
    async def test_nickname_mismatch_with_nexon_account(
        self, mock_process: AsyncMock
    ) -> None:
        """입력 닉네임이 넥슨 계정의 대표 캐릭터와 일치하지 않으면 실패해야 합니다."""
        is_valid, error_msg = await validate_signup_data(self._make_valid_data())
        assert is_valid is False
        assert "대표 캐릭터" in error_msg

    @pytest.mark.asyncio
    @patch(
        "apps.auth.services.process_signup_with_key",
        new_callable=AsyncMock,
        side_effect=Exception("네트워크 오류"),
    )
    async def test_nexon_api_exception(self, mock_process: AsyncMock) -> None:
        """넥슨 API 호출 중 예외가 발생하면 서버 오류 메시지를 반환해야 합니다."""
        is_valid, error_msg = await validate_signup_data(self._make_valid_data())
        assert is_valid is False
        assert "서버 오류" in error_msg


@pytest.mark.django_db(transaction=True)
class TestCreateUserWithProfile:
    """사용자 및 프로필 생성 서비스 테스트."""

    @pytest.mark.asyncio
    async def test_creates_user_and_profile(self) -> None:
        """User와 UserProfile이 정상적으로 생성되어야 합니다."""
        user = await create_user_with_profile(
            user_id="new_test_user",
            password="password1234",
            maple_nickname="새캐릭터",
            nexon_api_key="api_key_value",
        )
        assert user.username == "new_test_user"
        # 비밀번호가 해싱되었는지 확인 (평문이 아님)
        assert user.password != "password1234"
        assert await sync_to_async(user.check_password)("password1234") is True

        # 프로필이 연동되었는지 확인
        profile = await UserProfile.objects.aget(user=user)
        assert profile.maple_nickname == "새캐릭터"
        assert profile.nexon_api_key == "api_key_value"

    @pytest.mark.asyncio
    async def test_duplicate_user_raises(self) -> None:
        """동일 아이디로 재생성 시 예외가 발생해야 합니다."""
        await create_user_with_profile(
            user_id="dup_user_test",
            password="password1234",
            maple_nickname="캐릭1",
            nexon_api_key="key1",
        )
        with pytest.raises(Exception):
            await create_user_with_profile(
                user_id="dup_user_test",
                password="password5678",
                maple_nickname="캐릭2",
                nexon_api_key="key2",
            )
