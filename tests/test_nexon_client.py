# tests/test_nexon_client.py
"""
넥슨 Open API 클라이언트 테스트

HTTP 클라이언트의 URL 빌드, 헤더 생성, 재시도 로직 등을
외부 네트워크 호출 없이 모킹으로 테스트합니다.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp

from apps.character.nexon.client import (
    _build_url,
    _request_with_retry,
    build_headers,
    fetch_character_ocid,
)
from apps.character.nexon.constants import API_ENDPOINTS, BASE_URL


# ---------------------------------------------------------------------------
# URL 빌드 테스트
# ---------------------------------------------------------------------------


class TestBuildUrl:
    """_build_url 유틸리티 함수 테스트."""

    def test_build_url_without_params(self) -> None:
        """파라미터 없이 호출 시 기본 URL만 반환해야 합니다."""
        url = _build_url("get_character_id")
        expected_path = API_ENDPOINTS["get_character_id"]
        assert url == f"{BASE_URL}{expected_path}"

    def test_build_url_with_params(self) -> None:
        """쿼리 파라미터가 URL에 올바르게 추가되어야 합니다."""
        url = _build_url("get_character_id", character_name="테스트")
        assert "character_name=" in url
        assert BASE_URL in url

    def test_build_url_with_ocid(self) -> None:
        """ocid 파라미터가 URL에 올바르게 추가되어야 합니다."""
        url = _build_url("get_character_basic_info", ocid="test_ocid_123")
        assert "ocid=test_ocid_123" in url


# ---------------------------------------------------------------------------
# 헤더 빌드 테스트
# ---------------------------------------------------------------------------


class TestBuildHeaders:
    """build_headers 유틸리티 함수 테스트."""

    def test_headers_contain_api_key(self) -> None:
        """헤더에 API 키가 포함되어야 합니다."""
        headers = build_headers("my_test_key")
        assert headers["x-nxopen-api-key"] == "my_test_key"

    def test_headers_content_type(self) -> None:
        """Content-Type이 application/json이어야 합니다."""
        headers = build_headers("key")
        assert headers["Content-Type"] == "application/json"

    def test_headers_user_agent(self) -> None:
        """User-Agent가 설정되어야 합니다."""
        headers = build_headers("key")
        assert "MAI-Help-You" in headers["User-Agent"]

    def test_api_key_stripped(self) -> None:
        """API 키 앞뒤 공백이 제거되어야 합니다."""
        headers = build_headers("  spaced_key  ")
        assert headers["x-nxopen-api-key"] == "spaced_key"


# ---------------------------------------------------------------------------
# 재시도 테스트
# ---------------------------------------------------------------------------


class TestRequestWithRetry:
    """일시적인 Nexon API 장애의 재시도 동작을 테스트합니다."""

    @pytest.mark.asyncio
    async def test_releases_retryable_response_before_retry(self) -> None:
        retry_response = MagicMock()
        retry_response.status = 500
        success_response = MagicMock()
        success_response.status = 200

        mock_session = AsyncMock(spec=aiohttp.ClientSession)
        mock_session.get = AsyncMock(
            side_effect=[retry_response, success_response],
        )

        with patch(
            "apps.character.nexon.client.asyncio.sleep",
            new_callable=AsyncMock,
        ) as mock_sleep:
            result = await _request_with_retry(
                mock_session,
                "https://example.test",
                build_headers("test-key"),
            )

        assert result is success_response
        retry_response.release.assert_called_once()
        mock_sleep.assert_awaited_once_with(1)


# ---------------------------------------------------------------------------
# fetch_character_ocid 테스트
# ---------------------------------------------------------------------------


class TestFetchCharacterOcid:
    """fetch_character_ocid 비동기 함수 테스트."""

    @pytest.mark.asyncio
    async def test_successful_ocid_fetch(self) -> None:
        """200 응답 시 OCID를 정상 반환해야 합니다."""
        # 모킹된 HTTP 응답 구성
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"ocid": "abc123"})

        mock_session = AsyncMock(spec=aiohttp.ClientSession)
        mock_session.get = AsyncMock(return_value=mock_response)

        # _request_with_retry를 모킹하여 직접 응답 반환
        with patch(
            "apps.character.nexon.client._request_with_retry",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            headers = build_headers("test_key")
            result = await fetch_character_ocid(
                mock_session, "테스트캐릭터", headers
            )
            assert result == "abc123"

    @pytest.mark.asyncio
    async def test_ocid_not_found(self) -> None:
        """응답에 ocid가 없으면 None을 반환해야 합니다."""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={})

        mock_session = AsyncMock(spec=aiohttp.ClientSession)

        with patch(
            "apps.character.nexon.client._request_with_retry",
            new_callable=AsyncMock,
            return_value=mock_response,
        ):
            headers = build_headers("test_key")
            result = await fetch_character_ocid(
                mock_session, "없는캐릭터", headers
            )
            assert result is None

    @pytest.mark.asyncio
    async def test_request_failure(self) -> None:
        """요청 실패(None 응답) 시 None을 반환해야 합니다."""
        mock_session = AsyncMock(spec=aiohttp.ClientSession)

        with patch(
            "apps.character.nexon.client._request_with_retry",
            new_callable=AsyncMock,
            return_value=None,
        ):
            headers = build_headers("test_key")
            result = await fetch_character_ocid(
                mock_session, "에러캐릭터", headers
            )
            assert result is None
