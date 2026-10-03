# tests/test_nexon_client.py
"""
공용 넥슨 Open API 클라이언트(common.nexon) 테스트

aiohttp 세션과 Redis를 가짜로 대체해 재시도, 오류 분류, 캐시 동작을 검증합니다.
"""

from typing import Any

import aiohttp
import pytest
import redis

from common.exceptions.nexon import ApiRateLimitExceeded, CharacterNotFound, NexonApiError
from common.nexon import NexonCache, NexonClient
from common.nexon import cache as cache_module
from common.nexon import client as client_module
from common.nexon import constants as c


class _FakeResponse:
    def __init__(self, status: int, body: Any) -> None:
        self.status = status
        self._body = body

    async def json(self, content_type: str | None = "application/json") -> Any:
        return self._body

    async def __aenter__(self) -> "_FakeResponse":
        return self

    async def __aexit__(self, *exc: Any) -> bool:
        return False


class _FakeSession:
    """경로별로 미리 정한 응답을 순서대로 돌려주는 가짜 aiohttp 세션.

    마지막 응답은 이후 호출에도 계속 사용합니다.
    """

    def __init__(self, routes: dict[str, list], calls: list) -> None:
        self._routes = routes
        self._calls = calls

    async def __aenter__(self) -> "_FakeSession":
        return self

    async def __aexit__(self, *exc: Any) -> bool:
        return False

    def get(self, url: str, params: dict | None = None) -> _FakeResponse:
        path = url.removeprefix(c.BASE_URL)
        self._calls.append((path, dict(params or {})))
        outcomes = self._routes[path]
        outcome = outcomes.pop(0) if len(outcomes) > 1 else outcomes[0]
        if isinstance(outcome, Exception):
            raise outcome
        return _FakeResponse(*outcome)


class _DictRedis:
    """get/setex만 흉내 내는 동기 Redis 대역."""

    def __init__(self) -> None:
        self.store: dict[str, str] = {}

    def get(self, key: str) -> str | None:
        return self.store.get(key)

    def setex(self, key: str, ttl: int, value: str) -> None:
        self.store[key] = value


@pytest.fixture
def api(monkeypatch: pytest.MonkeyPatch):
    """가짜 넥슨 API를 설치하는 헬퍼. 호출 기록(list)을 반환합니다."""
    monkeypatch.setattr(c, "RETRY_DELAY_SECONDS", 0)
    monkeypatch.setattr(client_module._rate_limiter, "interval", 0)

    def install(routes: dict[str, list]) -> list:
        calls: list = []
        monkeypatch.setattr(
            client_module.aiohttp,
            "ClientSession",
            lambda *args, **kwargs: _FakeSession(routes, calls),
        )
        return calls

    return install


def _error(name: str) -> dict:
    return {"error": {"name": name, "message": "error"}}


# ---------------------------------------------------------------------------
# OCID 조회
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_ocid_is_cached_with_case_insensitive_key(api) -> None:
    calls = api({"/id": [(200, {"ocid": "ocid-1"})]})
    redis_double = _DictRedis()
    client = NexonClient("key", cache=NexonCache(client=redis_double))

    assert await client.get_ocid("  Hero  ") == "ocid-1"
    assert await client.get_ocid("hero") == "ocid-1"

    # 앞뒤 공백을 제거해 요청하고, 두 번째 조회는 캐시를 사용합니다.
    assert calls == [("/id", {"character_name": "Hero"})]
    assert "nexon:ocid:hero" in redis_double.store


@pytest.mark.asyncio
async def test_unknown_character_name_raises_not_found(api) -> None:
    api({"/id": [(400, _error(c.ERROR_INVALID_PARAMETER))]})

    with pytest.raises(CharacterNotFound, match="없는캐릭터"):
        await NexonClient("key").get_ocid("없는캐릭터")


@pytest.mark.asyncio
async def test_empty_name_raises_not_found_without_request(api) -> None:
    calls = api({})

    with pytest.raises(CharacterNotFound):
        await NexonClient("key").get_ocid("   ")
    assert calls == []


@pytest.mark.asyncio
async def test_missing_api_key_raises_without_request(api) -> None:
    calls = api({})

    with pytest.raises(NexonApiError) as error:
        await NexonClient("").get_ocid("캐릭터")
    assert error.value.error_name == "NO_API_KEY"
    assert calls == []


# ---------------------------------------------------------------------------
# 재시도와 오류 분류
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_server_error_is_retried(api) -> None:
    calls = api({"/id": [(500, _error("OPENAPI00001")), (200, {"ocid": "ocid-1"})]})

    assert await NexonClient("key").get_ocid("캐릭터") == "ocid-1"
    assert len(calls) == 2


@pytest.mark.asyncio
async def test_rate_limit_after_retries_raises(api) -> None:
    calls = api({"/id": [(429, _error(c.ERROR_RATE_LIMIT))]})

    with pytest.raises(ApiRateLimitExceeded):
        await NexonClient("key").get_ocid("캐릭터")
    assert len(calls) == c.MAX_RETRIES


@pytest.mark.asyncio
async def test_invalid_api_key_is_not_retried(api) -> None:
    calls = api({"/id": [(400, _error(c.ERROR_INVALID_API_KEY))]})

    with pytest.raises(NexonApiError) as error:
        await NexonClient("bad-key").get_ocid("캐릭터")
    assert error.value.error_name == c.ERROR_INVALID_API_KEY
    assert len(calls) == 1


@pytest.mark.asyncio
async def test_network_error_after_retries_raises_api_error(api) -> None:
    calls = api({"/id": [aiohttp.ClientConnectionError("연결 실패")]})

    with pytest.raises(NexonApiError, match="연결할 수 없습니다"):
        await NexonClient("key").get_ocid("캐릭터")
    assert len(calls) == c.MAX_RETRIES


# ---------------------------------------------------------------------------
# 여러 엔드포인트 조회
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_fetch_character_with_known_ocid_skips_id_lookup(api) -> None:
    calls = api(
        {
            "/character/basic": [(200, {"character_name": "캐릭터"})],
            "/character/stat": [(200, {"final_stat": []})],
        }
    )

    result = await NexonClient("key").fetch_character(
        ["/character/basic", "/character/stat", "/character/basic"], ocid="ocid-1"
    )

    assert result.ocid == "ocid-1"
    assert set(result.responses) == {"/character/basic", "/character/stat"}
    assert [path for path, _ in calls] == ["/character/basic", "/character/stat"]


@pytest.mark.asyncio
async def test_fetch_character_keeps_partial_results(api) -> None:
    api(
        {
            "/id": [(200, {"ocid": "ocid-1"})],
            "/character/basic": [(200, {"character_name": "캐릭터"})],
            "/character/stat": [(503, _error("OPENAPI00011"))],
        }
    )

    result = await NexonClient("key").fetch_character(
        ["/character/basic", "/character/stat"], character_name="캐릭터"
    )

    assert list(result.responses) == ["/character/basic"]
    assert isinstance(result.failed["/character/stat"], NexonApiError)


@pytest.mark.asyncio
async def test_fetch_character_raises_when_everything_fails(api) -> None:
    api({"/character/basic": [(503, _error("OPENAPI00011"))]})

    with pytest.raises(NexonApiError):
        await NexonClient("key").fetch_character(["/character/basic"], ocid="ocid-1")


@pytest.mark.asyncio
async def test_fetch_character_with_invalid_ocid_raises_not_found(api) -> None:
    api(
        {
            "/character/basic": [(400, _error(c.ERROR_INVALID_ID))],
            "/character/stat": [(200, {"final_stat": []})],
        }
    )

    with pytest.raises(CharacterNotFound):
        await NexonClient("key").fetch_character(
            ["/character/basic", "/character/stat"], ocid="old-ocid"
        )


@pytest.mark.asyncio
async def test_endpoint_cache_and_bypass(api) -> None:
    calls = api({"/character/basic": [(200, {"v": 1}), (200, {"v": 2})]})
    client = NexonClient("key", cache=NexonCache(client=_DictRedis()))

    assert await client.get_character_endpoint("/character/basic", "ocid-1") == {"v": 1}
    assert await client.get_character_endpoint("/character/basic", "ocid-1") == {"v": 1}
    # use_cache=False는 캐시를 읽지 않고 최신 응답으로 캐시를 갱신합니다.
    assert await client.get_character_endpoint(
        "/character/basic", "ocid-1", use_cache=False
    ) == {"v": 2}
    assert await client.get_character_endpoint("/character/basic", "ocid-1") == {"v": 2}
    assert len(calls) == 2


@pytest.mark.asyncio
async def test_account_characters_are_flattened(api) -> None:
    api(
        {
            c.ACCOUNT_CHARACTER_LIST_PATH: [
                (
                    200,
                    {
                        "account_list": [
                            {"character_list": [{"character_name": "A"}, {"character_name": "B"}]},
                            {"character_list": [{"character_name": "C"}]},
                        ]
                    },
                )
            ]
        }
    )

    characters = await NexonClient("user-key").get_account_characters()

    assert [ch["character_name"] for ch in characters] == ["A", "B", "C"]


@pytest.mark.asyncio
async def test_rate_limiter_spaces_request_starts() -> None:
    import asyncio
    import time

    limiter = client_module._RateLimiter(per_second=20)  # 0.05초 간격
    started = time.monotonic()
    await asyncio.gather(*(limiter.wait() for _ in range(3)))

    # 첫 요청은 바로, 나머지는 간격을 두고 시작하므로 최소 두 간격이 지나야 합니다.
    assert time.monotonic() - started >= 0.09
    assert client_module._RateLimiter(per_second=0).interval == 0


# ---------------------------------------------------------------------------
# Redis 캐시
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cache_fails_open_and_pauses_after_redis_error(monkeypatch: pytest.MonkeyPatch) -> None:
    class BrokenRedis:
        calls = 0

        def get(self, key: str) -> None:
            BrokenRedis.calls += 1
            raise redis.ConnectionError("Redis 연결 실패")

        def setex(self, *args: Any) -> None:
            BrokenRedis.calls += 1
            raise redis.ConnectionError("Redis 연결 실패")

    cache = NexonCache(client=BrokenRedis())

    assert await cache.get("key") is None
    await cache.set("key", {"v": 1}, c.CHARACTER_CACHE_TTL)
    assert await cache.get("key") is None
    # 첫 실패 이후에는 일정 시간 동안 Redis를 다시 호출하지 않습니다.
    assert BrokenRedis.calls == 1

    monkeypatch.setattr(cache_module, "RETRY_AFTER_SECONDS", 0)
    cache._disabled_until = 0
    assert await cache.get("key") is None
    assert BrokenRedis.calls == 2
