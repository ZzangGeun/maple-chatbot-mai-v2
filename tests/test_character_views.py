# tests/test_character_views.py
"""
character 앱 뷰(엔드포인트) 통합 테스트

캐릭터 검색, 연동 신청, 인증 API를 테스트합니다.
넥슨 API 호출은 모킹 처리합니다.
"""

import json

import pytest
from unittest.mock import AsyncMock, patch

from django.contrib.auth.models import User
from django.test import AsyncClient

from apps.auth.models import UserProfile
from apps.character.models import CharacterLink


@pytest.mark.django_db(transaction=True)
class TestCharacterSearchView:
    """GET /api/v1/character/search/ 엔드포인트 테스트."""

    SEARCH_URL = "/api/v1/character/search/"

    @pytest.mark.asyncio
    @patch(
        "apps.character.views.get_character_data",
        new_callable=AsyncMock,
        return_value={
            "basic": {
                "character_name": "은월",
                "character_level": 280,
                "character_class": "은월",
                "world_name": "루나",
            }
        },
    )
    async def test_search_existing_character(
        self, mock_get_data: AsyncMock
    ) -> None:
        """존재하는 캐릭터 검색 시 200과 캐릭터 정보를 반환해야 합니다."""
        client = AsyncClient()
        response = await client.get(f"{self.SEARCH_URL}?name=은월")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["basic"]["character_name"] == "은월"

    @pytest.mark.asyncio
    async def test_search_missing_name(self) -> None:
        """캐릭터명 파라미터가 없으면 400을 반환해야 합니다."""
        client = AsyncClient()
        response = await client.get(self.SEARCH_URL)
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "NAME_REQUIRED"

    @pytest.mark.asyncio
    async def test_search_empty_name(self) -> None:
        """빈 문자열 캐릭터명은 400을 반환해야 합니다."""
        client = AsyncClient()
        response = await client.get(f"{self.SEARCH_URL}?name=")
        assert response.status_code == 400

    @pytest.mark.asyncio
    @patch(
        "apps.character.views.get_character_data",
        new_callable=AsyncMock,
        return_value=None,
    )
    async def test_search_nonexistent_character(
        self, mock_get_data: AsyncMock
    ) -> None:
        """존재하지 않는 캐릭터 검색 시 404를 반환해야 합니다."""
        client = AsyncClient()
        response = await client.get(f"{self.SEARCH_URL}?name=없는캐릭터명")
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False

    @pytest.mark.asyncio
    @patch(
        "apps.character.views.get_character_data",
        new_callable=AsyncMock,
        side_effect=Exception("API 오류"),
    )
    async def test_search_api_exception(
        self, mock_get_data: AsyncMock
    ) -> None:
        """넥슨 API 호출 중 예외 발생 시 500을 반환해야 합니다."""
        client = AsyncClient()
        response = await client.get(f"{self.SEARCH_URL}?name=에러캐릭터")
        assert response.status_code == 500
        data = response.json()
        assert data["error"]["code"] == "SERVER_ERROR"


@pytest.mark.django_db(transaction=True)
class TestCharacterLinkView:
    """POST /api/v1/auth/character/link 엔드포인트 테스트."""

    LINK_URL = "/api/v1/auth/character/link"

    @pytest.fixture(autouse=True)
    def _setup(self, db) -> None:
        self.user = User.objects.create_user(
            username="link_user", password="password123"
        )

    @pytest.mark.asyncio
    async def test_link_unauthenticated(self) -> None:
        """비로그인 상태에서는 401을 반환해야 합니다."""
        client = AsyncClient()
        response = await client.post(
            self.LINK_URL,
            data=json.dumps({"character_name": "테스트캐릭"}),
            content_type="application/json",
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_link_success(self) -> None:
        """로그인 상태에서 캐릭터 연동 신청 시 인증 코드를 반환해야 합니다."""
        client = AsyncClient()
        await client.alogin(username="link_user", password="password123")
        response = await client.post(
            self.LINK_URL,
            data=json.dumps({"character_name": "연동테스트캐릭"}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "MAI-" in data["verification_code"]

    @pytest.mark.asyncio
    async def test_link_missing_character_name(self) -> None:
        """캐릭터명이 누락되면 400을 반환해야 합니다."""
        client = AsyncClient()
        await client.alogin(username="link_user", password="password123")
        response = await client.post(
            self.LINK_URL,
            data=json.dumps({"character_name": ""}),
            content_type="application/json",
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_link_invalid_json(self) -> None:
        """잘못된 JSON 바디 시 400을 반환해야 합니다."""
        client = AsyncClient()
        await client.alogin(username="link_user", password="password123")
        response = await client.post(
            self.LINK_URL,
            data="not json",
            content_type="application/json",
        )
        assert response.status_code == 400


@pytest.mark.django_db(transaction=True)
class TestCharacterVerifyView:
    """POST /api/v1/auth/character/verify 엔드포인트 테스트."""

    VERIFY_URL = "/api/v1/auth/character/verify"

    @pytest.fixture(autouse=True)
    def _setup(self, db) -> None:
        self.user = User.objects.create_user(
            username="verify_user", password="password123"
        )

    @pytest.mark.asyncio
    async def test_verify_unauthenticated(self) -> None:
        """비로그인 상태에서는 401을 반환해야 합니다."""
        client = AsyncClient()
        response = await client.post(
            self.VERIFY_URL,
            data=json.dumps({
                "character_name": "테스트",
                "verification_code": "MAI-1234",
            }),
            content_type="application/json",
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_verify_missing_fields(self) -> None:
        """필수 필드가 누락되면 400을 반환해야 합니다."""
        client = AsyncClient()
        await client.alogin(username="verify_user", password="password123")
        response = await client.post(
            self.VERIFY_URL,
            data=json.dumps({"character_name": "테스트"}),
            content_type="application/json",
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_verify_wrong_code(self) -> None:
        """잘못된 인증 코드로 인증 시 실패해야 합니다."""
        client = AsyncClient()
        await client.alogin(username="verify_user", password="password123")

        # 먼저 인증 코드 발급
        link_response = await client.post(
            "/api/v1/auth/character/link",
            data=json.dumps({"character_name": "인증테스트"}),
            content_type="application/json",
        )
        assert link_response.status_code == 200

        # 잘못된 코드로 인증 시도
        response = await client.post(
            self.VERIFY_URL,
            data=json.dumps({
                "character_name": "인증테스트",
                "verification_code": "MAI-0000",  # 잘못된 코드
            }),
            content_type="application/json",
        )
        assert response.status_code == 400
