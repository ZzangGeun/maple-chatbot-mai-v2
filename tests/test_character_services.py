# tests/test_character_services.py
"""
character 앱 서비스 레이어 테스트

generate_verification_code 및 verify_and_link_character의
비즈니스 로직을 테스트합니다.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from django.conf import settings
from django.contrib.auth.models import User

from apps.character.models import CharacterLink
from apps.character.services import (
    generate_verification_code,
    verify_and_link_character,
)


class TestGenerateVerificationCode:
    """인증 코드 생성 함수 테스트."""

    def _make_mock_session(self) -> MagicMock:
        """Django 세션처럼 동작하는 모킹 세션을 생성합니다.

        왜 MagicMock을 사용하는가: generate_verification_code 내부에서
        session.modified = True를 호출하는데, 일반 dict는 이 속성을 지원하지 않습니다.
        """
        session = MagicMock()
        session.__setitem__ = MagicMock()
        session.__getitem__ = MagicMock()
        session.__contains__ = MagicMock(return_value=True)
        # dict처럼 키-값 저장을 위해 내부 저장소 사용
        _store: dict = {}
        session.__setitem__.side_effect = _store.__setitem__
        session.__getitem__.side_effect = _store.__getitem__
        session.__contains__.side_effect = _store.__contains__
        session._store = _store
        return session

    def test_code_format(self) -> None:
        """생성된 코드가 'MAI-XXXX' 형식이어야 합니다."""
        session = self._make_mock_session()
        code = generate_verification_code(session, "테스트캐릭터")
        assert code.startswith("MAI-")
        # 숫자 부분이 4자리인지 확인
        num_part = code.split("-")[1]
        assert len(num_part) == 4
        assert num_part.isdigit()

    def test_code_stored_in_session(self) -> None:
        """생성된 코드가 세션에 올바른 키로 저장되어야 합니다."""
        session = self._make_mock_session()
        code = generate_verification_code(session, "캐릭터A")
        assert session._store["verify_code_캐릭터A"] == code

    def test_different_characters_get_different_keys(self) -> None:
        """다른 캐릭터명에 대해 각각 다른 세션 키가 생성되어야 합니다."""
        session = self._make_mock_session()
        generate_verification_code(session, "캐릭터A")
        generate_verification_code(session, "캐릭터B")
        assert "verify_code_캐릭터A" in session._store
        assert "verify_code_캐릭터B" in session._store

    def test_session_modified_flag(self) -> None:
        """세션의 modified 플래그가 True로 설정되어야 합니다."""
        session = MagicMock()
        generate_verification_code(session, "플래그테스트")
        assert session.modified is True

    def test_code_range(self) -> None:
        """생성된 숫자가 1000~9999 범위 내에 있어야 합니다."""
        session = self._make_mock_session()
        for _ in range(50):
            code = generate_verification_code(session, "범위테스트")
            num = int(code.split("-")[1])
            assert 1000 <= num <= 9999


@pytest.mark.django_db(transaction=True)
class TestVerifyAndLinkCharacter:
    """캐릭터 인증 및 연동 서비스 테스트."""

    @pytest.fixture(autouse=True)
    def _setup(self, db) -> None:
        self.user = User.objects.create_user(
            username="verify_svc_user", password="password123"
        )

    @pytest.mark.asyncio
    async def test_wrong_verification_code(self) -> None:
        """세션에 저장된 코드와 다른 코드를 입력하면 VERIFICATION_FAILED를 반환해야 합니다."""
        session = {"verify_code_테스트캐릭": "MAI-1234"}
        success, error_code, info = await verify_and_link_character(
            user=self.user,
            session=session,
            character_name="테스트캐릭",
            verification_code="MAI-9999",  # 잘못된 코드
        )
        assert success is False
        assert error_code == "VERIFICATION_FAILED"
        assert info is None

    @pytest.mark.asyncio
    async def test_no_cached_code(self) -> None:
        """세션에 인증 코드가 없으면 VERIFICATION_FAILED를 반환해야 합니다."""
        session: dict = {}
        success, error_code, info = await verify_and_link_character(
            user=self.user,
            session=session,
            character_name="미발급캐릭",
            verification_code="MAI-1234",
        )
        assert success is False
        assert error_code == "VERIFICATION_FAILED"

    @pytest.mark.asyncio
    @patch.object(settings, "DEBUG", True)
    @patch.object(settings, "NEXON_API_KEY", "")
    async def test_debug_mock_verification(self) -> None:
        """DEBUG 모드 + API 키 미설정 시 가상 연동이 성공해야 합니다.

        왜 이렇게 테스트하는가: 개발 환경에서 넥슨 API 키 없이도
        캐릭터 연동 흐름을 테스트할 수 있도록 Mock 경로가 동작하는지 검증합니다.
        """
        session = MagicMock()
        session.get.return_value = "MAI-5678"
        session.__contains__ = lambda self, key: True
        session.__getitem__ = lambda self, key: "MAI-5678"
        session.__delitem__ = MagicMock()

        success, error_code, info = await verify_and_link_character(
            user=self.user,
            session=session,
            character_name="디버그캐릭",
            verification_code="MAI-5678",
        )
        assert success is True
        assert error_code == "SUCCESS"
        assert info is not None
        assert info["character_name"] == "디버그캐릭"

        # DB에 실제로 저장되었는지 확인
        exists = await CharacterLink.objects.filter(
            user=self.user, character_name="디버그캐릭"
        ).aexists()
        assert exists is True
