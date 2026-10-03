# common/nexon/client.py
"""
넥슨 Open API 비동기 클라이언트

Django(캐릭터 검색·연동)와 AI 서버(챗봇 캐릭터 조회)가 함께 사용합니다.

- 429·5xx·네트워크 오류는 지수 백오프로 재시도하고, 그 외 오류는 바로 예외로 바꿉니다.
    CharacterNotFound    : 존재하지 않는 캐릭터명 또는 유효하지 않은 OCID
    ApiRateLimitExceeded : 재시도 후에도 호출 한도 초과
    NexonApiError        : 그 밖의 API 오류, 점검, 네트워크 장애, API 키 미설정
- cache(NexonCache)를 넘기면 OCID와 캐릭터 정보 응답을 Redis에 캐싱합니다.

API 키는 코드에 두지 않고 호출하는 쪽에서 설정값(NEXON_API_KEY 또는 사용자 키)으로 넘겨받습니다.
"""

import asyncio
import logging
import random
import threading
import time
from collections.abc import AsyncIterator, Iterable
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Any

import aiohttp

from common.exceptions.base import AppException
from common.exceptions.nexon import ApiRateLimitExceeded, CharacterNotFound, NexonApiError
from common.nexon import constants as c
from common.nexon.cache import NexonCache

logger = logging.getLogger(__name__)

USER_AGENT = "MAI-Help-You/1.0"


@dataclass
class CharacterFetchResult:
    """한 캐릭터의 여러 엔드포인트 조회 결과. 일부 엔드포인트만 실패할 수 있습니다."""

    ocid: str
    responses: dict[str, dict] = field(default_factory=dict)  # 경로 → 응답
    failed: dict[str, AppException] = field(default_factory=dict)  # 경로 → 실패 원인


class _RateLimiter:
    """요청 시작 시각을 일정 간격으로 띄워 초당 요청 수를 제한합니다. (프로세스 단위)

    Django는 요청마다 이벤트 루프가 바뀔 수 있어 asyncio.Lock 대신 threading.Lock으로
    다음 시작 시각만 예약하고, 실제 대기는 asyncio.sleep으로 합니다.
    """

    def __init__(self, per_second: float) -> None:
        self.interval = 1.0 / per_second if per_second > 0 else 0.0
        self._lock = threading.Lock()
        self._next_start = 0.0

    async def wait(self) -> None:
        if self.interval <= 0:
            return
        with self._lock:
            now = time.monotonic()
            start = max(now, self._next_start)
            self._next_start = start + self.interval
        if start > now:
            await asyncio.sleep(start - now)


_rate_limiter = _RateLimiter(c.REQUESTS_PER_SECOND)


def _is_retryable(status: int) -> bool:
    return status == 429 or 500 <= status < 600


async def _read_error_name(response: aiohttp.ClientResponse) -> str:
    """넥슨 API 오류 응답({"error": {"name": ...}})에서 오류 코드를 꺼냅니다."""
    try:
        body = await response.json(content_type=None)
    except Exception:
        return ""
    if not isinstance(body, dict):
        return ""
    return (body.get("error") or {}).get("name", "")


def _to_exception(status: int, error_name: str, path: str, params: dict[str, Any]) -> AppException:
    """재시도하지 않을 오류 응답을 예외로 변환합니다."""
    if status == 429 or error_name == c.ERROR_RATE_LIMIT:
        return ApiRateLimitExceeded()
    if path == c.OCID_PATH and error_name == c.ERROR_INVALID_PARAMETER:
        return CharacterNotFound(params.get("character_name", ""))
    if error_name == c.ERROR_INVALID_ID:
        return CharacterNotFound()
    return NexonApiError(
        f"넥슨 Open API 오류 (HTTP {status}, {error_name or '알 수 없음'})",
        error_name=error_name,
    )


class NexonClient:
    """넥슨 메이플스토리 Open API 비동기 클라이언트."""

    def __init__(self, api_key: str, cache: NexonCache | None = None) -> None:
        self._api_key = (api_key or "").strip()
        self._cache = cache

    @asynccontextmanager
    async def _session(
        self, session: aiohttp.ClientSession | None = None
    ) -> AsyncIterator[aiohttp.ClientSession]:
        """주어진 세션을 그대로 쓰거나, 없으면 새 세션을 열고 닫습니다."""
        if session is not None:
            yield session
            return

        if not self._api_key:
            raise NexonApiError("NEXON_API_KEY가 설정되지 않았습니다.", error_name="NO_API_KEY")

        async with aiohttp.ClientSession(
            headers={"x-nxopen-api-key": self._api_key, "User-Agent": USER_AGENT},
            timeout=aiohttp.ClientTimeout(total=c.REQUEST_TIMEOUT_SECONDS),
        ) as new_session:
            yield new_session

    async def _request(
        self, session: aiohttp.ClientSession, path: str, params: dict[str, Any]
    ) -> dict:
        """GET 요청을 재시도 정책과 함께 수행합니다."""
        url = f"{c.BASE_URL}{path}"
        delay = c.RETRY_DELAY_SECONDS

        for attempt in range(1, c.MAX_RETRIES + 1):
            await _rate_limiter.wait()
            try:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        return await response.json()

                    error_name = await _read_error_name(response)
                    if not (_is_retryable(response.status) and attempt < c.MAX_RETRIES):
                        raise _to_exception(response.status, error_name, path, params)
                    logger.warning(
                        "넥슨 API HTTP %d (%s). %d/%d차 요청 재시도",
                        response.status,
                        error_name,
                        attempt,
                        c.MAX_RETRIES,
                    )
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                if attempt == c.MAX_RETRIES:
                    raise NexonApiError(f"넥슨 Open API에 연결할 수 없습니다: {e}") from e
                logger.warning("넥슨 API 네트워크 오류 (%s). %d/%d차 요청 재시도", e, attempt, c.MAX_RETRIES)

            # 동시에 429를 받은 요청들이 같은 순간에 다시 몰리지 않도록 대기 시간을 흩뜨립니다.
            await asyncio.sleep(delay * random.uniform(0.5, 1.5))
            delay *= 2

        raise NexonApiError("넥슨 Open API 요청이 응답 없이 종료되었습니다.")

    async def get_ocid(
        self, character_name: str, session: aiohttp.ClientSession | None = None
    ) -> str:
        """캐릭터명으로 고유 식별자(OCID)를 조회합니다."""
        name = (character_name or "").strip()
        if not name:
            raise CharacterNotFound()

        # 영문 캐릭터명의 대소문자 차이로 같은 캐릭터가 따로 캐싱되지 않도록 소문자로 키를 만듭니다.
        cache_key = f"ocid:{name.lower()}"
        if self._cache and (cached := await self._cache.get(cache_key)):
            return cached

        async with self._session(session) as s:
            data = await self._request(s, c.OCID_PATH, {"character_name": name})

        ocid = data.get("ocid")
        if not ocid:
            raise CharacterNotFound(name)
        if self._cache:
            await self._cache.set(cache_key, ocid, c.OCID_CACHE_TTL)
        return ocid

    async def get_character_endpoint(
        self,
        path: str,
        ocid: str,
        session: aiohttp.ClientSession | None = None,
        *,
        use_cache: bool = True,
    ) -> dict:
        """OCID로 캐릭터 정보 엔드포인트 하나를 조회합니다. (예: "/character/stat")

        use_cache=False면 캐시를 읽지 않고 최신 응답을 받아 캐시를 갱신합니다.
        """
        cache_key = f"{path}:{ocid}"
        if use_cache and self._cache:
            cached = await self._cache.get(cache_key)
            if cached is not None:
                return cached

        async with self._session(session) as s:
            data = await self._request(s, path, {"ocid": ocid})

        if self._cache:
            await self._cache.set(cache_key, data, c.CHARACTER_CACHE_TTL)
        return data

    async def fetch_character(
        self,
        paths: Iterable[str],
        *,
        character_name: str = "",
        ocid: str = "",
        use_cache: bool = True,
    ) -> CharacterFetchResult:
        """캐릭터 하나의 여러 엔드포인트를 한 세션에서 동시에 조회합니다.

        ocid를 알면 캐릭터명 조회(/id)를 건너뜁니다.
        일부 엔드포인트가 실패하면 failed에 담아 돌려주고, 모두 실패하거나
        캐릭터가 존재하지 않으면 예외를 발생시킵니다.
        """
        unique_paths = list(dict.fromkeys(paths))

        async with self._session() as session:
            resolved_ocid = ocid or await self.get_ocid(character_name, session)
            semaphore = asyncio.Semaphore(c.MAX_CONCURRENT_REQUESTS)

            async def fetch_one(path: str) -> tuple[str, dict | AppException]:
                async with semaphore:
                    try:
                        data = await self.get_character_endpoint(
                            path, resolved_ocid, session, use_cache=use_cache
                        )
                        return path, data
                    except AppException as e:
                        logger.warning(f"넥슨 API {path} 조회 실패: {e.message}")
                        return path, e

            outcomes = await asyncio.gather(*(fetch_one(path) for path in unique_paths))

        result = CharacterFetchResult(ocid=resolved_ocid)
        for path, outcome in outcomes:
            if isinstance(outcome, AppException):
                result.failed[path] = outcome
            else:
                result.responses[path] = outcome

        not_found = next(
            (e for e in result.failed.values() if isinstance(e, CharacterNotFound)), None
        )
        if not_found:
            raise not_found
        if result.failed and not result.responses:
            raise next(iter(result.failed.values()))
        return result

    async def get_account_characters(self) -> list[dict]:
        """이 클라이언트의 API 키를 발급한 계정의 모든 캐릭터 목록을 반환합니다. (캐시하지 않음)"""
        async with self._session() as session:
            data = await self._request(session, c.ACCOUNT_CHARACTER_LIST_PATH, {})

        characters: list[dict] = []
        for account in data.get("account_list", []):
            characters.extend(account.get("character_list", []))
        return characters
