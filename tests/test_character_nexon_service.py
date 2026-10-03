# tests/test_character_nexon_service.py
"""
Django 캐릭터 서비스 테스트 (공용 넥슨 클라이언트 연동)

- 캐릭터 검색 데이터 조회 (apps.character.nexon.character_service)
- 회원가입 시 대표 캐릭터 확인
- 캐릭터 연동 인증의 오류 분류 (apps.character.services)
넥슨 API는 가짜 클라이언트로 대체하고, JSON 파일은 저장하지 않습니다.
"""

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from django.conf import settings
from django.contrib.auth.models import User
from django.core.cache import cache

from apps.character.models import CharacterLink
from apps.character.nexon import character_service
from apps.character import services as link_services
from common.exceptions.nexon import CharacterNotFound, NexonApiError
from common.nexon import CharacterFetchResult
from common.nexon.constants import CHARACTER_INFO_ENDPOINTS
from common.nexon.extractors import extract_hexamatrix

BASIC = {"character_name": "검색캐릭", "world_name": "루나", "character_level": 280}


@pytest.fixture(autouse=True)
def _clean_cache_and_files(monkeypatch: pytest.MonkeyPatch):
    """Django 캐시를 비우고, 테스트 중 JSON 파일이 저장되지 않게 합니다."""
    cache.clear()
    saved: list = []
    monkeypatch.setattr(
        character_service,
        "save_character_data_to_json",
        lambda name, data, *args, **kwargs: saved.append(name),
    )
    yield saved
    cache.clear()


class _Session(dict):
    """modified 플래그를 가진 Django 세션 대역."""

    modified = False


def _fake_client(**methods: Any) -> MagicMock:
    client = MagicMock()
    for name, mock in methods.items():
        setattr(client, name, mock)
    return client


@pytest.mark.asyncio
async def test_get_character_data_extracts_and_caches(
    monkeypatch: pytest.MonkeyPatch, _clean_cache_and_files: list
) -> None:
    fetch = AsyncMock(
        return_value=CharacterFetchResult(
            ocid="ocid-1",
            responses={
                "/character/basic": dict(BASIC),
                "/character/stat": {"final_stat": [{"stat_name": "전투력", "stat_value": "1000"}]},
            },
        )
    )
    monkeypatch.setattr(character_service, "get_nexon_client", lambda api_key=None: _fake_client(fetch_character=fetch))

    first = await character_service.get_character_data("검색캐릭")
    second = await character_service.get_character_data("검색캐릭")

    # 검색 화면이 쓰는 응답 형식(basic_info, stat_info, item_info ...)을 유지합니다.
    assert first["basic_info"]["character_name"] == "검색캐릭"
    assert first["stat_info"]["전투력"] == "1000"
    assert "item_info" in first
    # 모든 화면용 엔드포인트를 한 번에 요청하고, 두 번째 조회는 캐시를 사용합니다.
    fetch.assert_awaited_once()
    assert list(fetch.await_args.args[0]) == list(CHARACTER_INFO_ENDPOINTS.values())
    assert second == first
    assert _clean_cache_and_files == ["검색캐릭"]


@pytest.mark.asyncio
@pytest.mark.parametrize("error", [CharacterNotFound("없는캐릭"), NexonApiError("점검 중")])
async def test_get_character_data_returns_none_on_failure(
    monkeypatch: pytest.MonkeyPatch, error: Exception
) -> None:
    fetch = AsyncMock(side_effect=error)
    monkeypatch.setattr(character_service, "get_nexon_client", lambda api_key=None: _fake_client(fetch_character=fetch))

    assert await character_service.get_character_data("없는캐릭") is None


@pytest.mark.asyncio
async def test_signup_picks_highest_level_character(monkeypatch: pytest.MonkeyPatch) -> None:
    characters = [
        {"character_name": "부캐", "ocid": "ocid-low", "character_level": "200"},
        {"character_name": "본캐", "ocid": "ocid-high", "character_level": "285"},
    ]
    monkeypatch.setattr(
        character_service,
        "NexonClient",
        lambda api_key, cache=None: _fake_client(get_account_characters=AsyncMock(return_value=characters)),
    )
    get_data = AsyncMock(return_value={"basic_info": {}})
    monkeypatch.setattr(character_service, "get_character_data", get_data)

    assert await character_service.process_signup_with_key("user-key") == ("본캐", "ocid-high")
    get_data.assert_awaited_once_with("본캐", "user-key")


@pytest.mark.asyncio
async def test_signup_with_invalid_key_returns_none(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        character_service,
        "NexonClient",
        lambda api_key, cache=None: _fake_client(
            get_account_characters=AsyncMock(side_effect=NexonApiError(error_name="OPENAPI00005"))
        ),
    )

    assert await character_service.process_signup_with_key("bad-key") is None


def test_hexamatrix_extractor_reads_core_equipment() -> None:
    extracted = extract_hexamatrix(
        {
            "date": None,
            "character_hexa_core_equipment": [
                {"hexa_core_name": "솔 야누스", "hexa_core_level": 14, "hexa_core_type": "공용 코어"}
            ],
        }
    )

    assert extracted["hexamatrix"] == [
        {"hexa_core_name": "솔 야누스", "hexa_core_level": 14, "hexa_core_type": "공용 코어"}
    ]


@pytest.mark.django_db(transaction=True)
class TestLinkVerificationWithNexonClient:
    """캐릭터 연동 인증이 넥슨 API 오류를 올바른 에러 코드로 바꾸는지 검증합니다."""

    @pytest.fixture(autouse=True)
    def _setup(self, db, monkeypatch: pytest.MonkeyPatch) -> None:
        self.user = User.objects.create_user(username="link_user", password="password123")
        self.session = _Session({"verify_code_연동캐릭": "MAI-1234"})
        monkeypatch.setattr(settings, "NEXON_API_KEY", "service-key")
        self.monkeypatch = monkeypatch

    def _use_client(self, **methods: Any) -> MagicMock:
        client = _fake_client(**methods)
        self.monkeypatch.setattr(link_services, "get_nexon_client", lambda api_key=None: client)
        return client

    async def _verify(self) -> tuple:
        return await link_services.verify_and_link_character(
            user=self.user,
            session=self.session,
            character_name="연동캐릭",
            verification_code="MAI-1234",
        )

    @pytest.mark.asyncio
    async def test_unknown_character(self) -> None:
        self._use_client(get_ocid=AsyncMock(side_effect=CharacterNotFound("연동캐릭")))

        assert await self._verify() == (False, "CHARACTER_NOT_FOUND", None)

    @pytest.mark.asyncio
    async def test_api_failure(self) -> None:
        self._use_client(
            get_ocid=AsyncMock(return_value="ocid-1"),
            get_character_endpoint=AsyncMock(side_effect=NexonApiError("점검 중")),
        )

        assert await self._verify() == (False, "API_COMMUNICATION_ERROR", None)

    @pytest.mark.asyncio
    async def test_code_found_links_character_with_fresh_data(self) -> None:
        endpoint = AsyncMock(
            return_value={"world_name": "루나", "character_description": "인증 MAI-1234"}
        )
        self._use_client(get_ocid=AsyncMock(return_value="ocid-1"), get_character_endpoint=endpoint)

        success, code, info = await self._verify()

        assert (success, code) == (True, "SUCCESS")
        assert info["ocid"] == "ocid-1" and info["is_main"] is True
        # 소개글 변경을 바로 확인해야 하므로 캐시를 쓰지 않습니다.
        endpoint.assert_awaited_once_with("/character/basic", "ocid-1", use_cache=False)
        assert await CharacterLink.objects.filter(user=self.user, ocid="ocid-1").aexists()
        # 사용한 인증 코드는 세션에서 지웁니다.
        assert "verify_code_연동캐릭" not in self.session
