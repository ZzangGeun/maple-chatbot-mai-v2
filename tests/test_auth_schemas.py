# tests/test_auth_schemas.py
"""
auth 앱 Pydantic 스키마 유닛 테스트

DB나 HTTP 의존 없이 스키마 유효성 검사 로직만 독립적으로 테스트합니다.
"""

import pytest
from pydantic import ValidationError

from apps.auth.schemas import LoginSchema, SignupSchema


# ---------------------------------------------------------------------------
# SignupSchema 테스트
# ---------------------------------------------------------------------------


class TestSignupSchema:
    """회원가입 스키마 유효성 검사 테스트."""

    def _make_valid_data(self, **overrides) -> dict:
        """유효한 기본 데이터를 생성하고, 필요한 필드만 오버라이드합니다."""
        data = {
            "username": "valid_user01",
            "password": "securepass123",
            "confirm_password": "securepass123",
            "maple_nickname": "테스트캐릭터",
            "nexon_api_key": "test_api_key_value",
        }
        data.update(overrides)
        return data

    def test_valid_signup_data(self) -> None:
        """정상적인 데이터는 유효성 검사를 통과해야 합니다."""
        schema = SignupSchema(**self._make_valid_data())
        assert schema.username == "valid_user01"
        assert schema.maple_nickname == "테스트캐릭터"

    def test_username_too_short(self) -> None:
        """아이디가 6자 미만이면 ValidationError가 발생해야 합니다."""
        with pytest.raises(ValidationError) as exc_info:
            SignupSchema(**self._make_valid_data(username="abc"))
        assert "아이디는 6~20자" in str(exc_info.value)

    def test_username_too_long(self) -> None:
        """아이디가 20자 초과이면 ValidationError가 발생해야 합니다."""
        with pytest.raises(ValidationError):
            SignupSchema(**self._make_valid_data(username="a" * 21))

    def test_username_invalid_characters(self) -> None:
        """아이디에 허용되지 않는 특수문자가 포함되면 실패해야 합니다."""
        with pytest.raises(ValidationError):
            SignupSchema(**self._make_valid_data(username="user@name!"))

    def test_username_with_korean_characters(self) -> None:
        """아이디에 한글이 포함되면 실패해야 합니다."""
        with pytest.raises(ValidationError):
            SignupSchema(**self._make_valid_data(username="유저이름테스트"))

    def test_password_too_short(self) -> None:
        """비밀번호가 8자 미만이면 ValidationError가 발생해야 합니다."""
        with pytest.raises(ValidationError) as exc_info:
            SignupSchema(
                **self._make_valid_data(
                    password="short",
                    confirm_password="short",
                )
            )
        assert "비밀번호는 최소 8자" in str(exc_info.value)

    def test_password_mismatch(self) -> None:
        """비밀번호와 확인 비밀번호가 다르면 ValidationError가 발생해야 합니다."""
        with pytest.raises(ValidationError) as exc_info:
            SignupSchema(
                **self._make_valid_data(
                    password="password1234",
                    confirm_password="different1234",
                )
            )
        assert "비밀번호와 비밀번호 확인이 일치하지 않습니다" in str(exc_info.value)

    def test_missing_required_field(self) -> None:
        """필수 필드가 빠지면 ValidationError가 발생해야 합니다."""
        with pytest.raises(ValidationError):
            # maple_nickname 필드 누락
            SignupSchema(
                username="valid_user01",
                password="securepass123",
                confirm_password="securepass123",
                nexon_api_key="test_key",
            )

    def test_username_with_underscore(self) -> None:
        """밑줄(_)은 아이디에 허용되어야 합니다."""
        schema = SignupSchema(**self._make_valid_data(username="user_name_01"))
        assert schema.username == "user_name_01"

    def test_username_boundary_six_characters(self) -> None:
        """아이디 최소 길이(6자) 경계값 테스트."""
        schema = SignupSchema(**self._make_valid_data(username="abcdef"))
        assert schema.username == "abcdef"

    def test_username_boundary_twenty_characters(self) -> None:
        """아이디 최대 길이(20자) 경계값 테스트."""
        schema = SignupSchema(**self._make_valid_data(username="a" * 20))
        assert len(schema.username) == 20

    def test_password_boundary_eight_characters(self) -> None:
        """비밀번호 최소 길이(8자) 경계값 테스트."""
        schema = SignupSchema(
            **self._make_valid_data(
                password="12345678",
                confirm_password="12345678",
            )
        )
        assert schema.password == "12345678"


# ---------------------------------------------------------------------------
# LoginSchema 테스트
# ---------------------------------------------------------------------------


class TestLoginSchema:
    """로그인 스키마 유효성 검사 테스트."""

    def test_valid_login_data(self) -> None:
        """정상적인 로그인 데이터는 통과해야 합니다."""
        schema = LoginSchema(username="valid_user01", password="password123")
        assert schema.username == "valid_user01"

    def test_missing_username(self) -> None:
        """username이 빠지면 ValidationError가 발생해야 합니다."""
        with pytest.raises(ValidationError):
            LoginSchema(password="password123")

    def test_missing_password(self) -> None:
        """password가 빠지면 ValidationError가 발생해야 합니다."""
        with pytest.raises(ValidationError):
            LoginSchema(username="valid_user01")
