# services/nexon/client.py
"""
넥슨 Open API HTTP 클라이언트

aiohttp를 사용한 API 호출을 수행하며, 429(Rate Limit) 및 5xx 계열 서버 장애 시
지수 백오프(Exponential Backoff)를 지원하는 견고한 재시도 메커니즘을 내장합니다.
"""

import asyncio
import logging
from urllib.parse import urlencode

import aiohttp

from apps.character.nexon.constants import (
    API_ENDPOINTS,
    BASE_URL,
    RATE_LIMIT_RETRY_DELAY_SECONDS,
    REQUEST_DELAY_SECONDS,
)

logger = logging.getLogger(__name__)


def _build_url(endpoint_key: str, **params) -> str:
    """
    엔드포인트 키와 쿼리 파라미터로 완성된 URL을 생성합니다.

    Args:
        endpoint_key: API_ENDPOINTS의 키 이름.
        **params: URL 쿼리 파라미터.

    Returns:
        완성된 URL 문자열.
    """
    path = API_ENDPOINTS[endpoint_key]
    url = f"{BASE_URL}{path}"
    if params:
        url += "?" + urlencode(params)
    return url


def build_headers(api_key: str) -> dict[str, str]:
    """넥슨 API 요청에 필요한 헤더를 반환합니다."""
    return {
        "x-nxopen-api-key": api_key.strip(),
        "Content-Type": "application/json",
        "User-Agent": "MAI-Help-You/1.0",
    }


async def _request_with_retry(
    session: aiohttp.ClientSession,
    url: str,
    headers: dict,
    max_retries: int = 3,
    initial_delay: float = RATE_LIMIT_RETRY_DELAY_SECONDS,
) -> aiohttp.ClientResponse | None:
    """
    HTTP GET 요청을 지수 백오프 재시도와 함께 실행합니다.

    429(Rate Limit) 및 5xx 계열 서버 일시 에러 발생 시 최대 max_retries 만큼
    대기 시간을 늘려가며 재시도합니다.

    Args:
        session: aiohttp 클라이언트 세션.
        url: 요청할 대상 URL.
        headers: 요청 헤더.
        max_retries: 최대 재시도 횟수.
        initial_delay: 최초 재시도 대기 시간(초).

    Returns:
        aiohttp.ClientResponse 인스턴스 또는 실패 시 None.
    """
    delay = initial_delay
    for attempt in range(1, max_retries + 1):
        try:
            # 넥슨 Open API의 지연 및 먹통 상황에 대처하기 위해 타임아웃을 설정합니다.
            timeout = aiohttp.ClientTimeout(total=10)
            response = await session.get(url, headers=headers, timeout=timeout)

            # 성공 시 즉시 응답을 반환합니다.
            if response.status == 200:
                return response

            # 429(Rate Limit) 혹은 5xx(서버 일시 장애)인 경우 백오프 적용
            if response.status == 429 or 500 <= response.status < 600:
                response.release()
                logger.warning(
                    "HTTP %d 발생. %d/%d차 요청 실패",
                    response.status,
                    attempt,
                    max_retries,
                )
                if attempt == max_retries:
                    break
                await asyncio.sleep(delay)
                delay *= 2
                continue

            # 그 외의 에러(400, 403, 404 등)는 재시도가 무의미하므로 바로 루프를 탈출합니다.
            logger.error(
                "HTTP %d 에러로 요청을 중단합니다. URL: %s",
                response.status,
                url,
            )
            return response

        except asyncio.TimeoutError:
            logger.warning(
                "타임아웃 초과. %d/%d차 요청 실패",
                attempt,
                max_retries,
            )
            if attempt == max_retries:
                break
            await asyncio.sleep(delay)
            delay *= 2
        except aiohttp.ClientError as e:
            logger.warning(
                "네트워크 오류 (%s). %d/%d차 요청 실패",
                e,
                attempt,
                max_retries,
            )
            if attempt == max_retries:
                break
            await asyncio.sleep(delay)
            delay *= 2

    logger.error("최대 %d회 재시도 후 요청이 실패했습니다. URL: %s", max_retries, url)
    return None


async def fetch_character_ocid(
    session: aiohttp.ClientSession,
    character_name: str,
    headers: dict,
) -> str | None:
    """
    캐릭터 이름으로 OCID(고유 식별자)를 조회합니다.

    Args:
        session: 재사용할 aiohttp 클라이언트 세션.
        character_name: 조회할 캐릭터 이름.
        headers: 넥슨 API 요청 헤더.

    Returns:
        OCID 문자열 또는 조회 실패 시 None.
    """
    url = _build_url("get_character_id", character_name=character_name)
    response = await _request_with_retry(session, url, headers)
    if response and response.status == 200:
        data = await response.json()
        return data.get("ocid")
    return None


async def fetch_character_endpoint(
    session: aiohttp.ClientSession,
    endpoint_key: str,
    ocid: str,
    headers: dict,
) -> dict:
    """
    단일 엔드포인트에서 캐릭터 정보를 조회합니다.
    재시도 로직을 통해 Rate Limit 상황을 유연하게 대처합니다.

    Args:
        session: 재사용할 aiohttp 클라이언트 세션.
        endpoint_key: API_ENDPOINTS의 키 이름.
        ocid: 캐릭터 OCID.
        headers: 넥슨 API 요청 헤더.

    Returns:
        API 응답 딕셔너리. 실패 시 빈 딕셔너리.
    """
    url = _build_url(endpoint_key, ocid=ocid)
    response = await _request_with_retry(session, url, headers)
    if response and response.status == 200:
        return await response.json()
    return {}


async def fetch_character_basic_info(
    session: aiohttp.ClientSession,
    ocid: str,
    headers: dict,
) -> dict:
    """캐릭터 기본 프로필 정보를 조회합니다."""
    return await fetch_character_endpoint(
        session,
        "get_character_basic_info",
        ocid,
        headers,
    )


async def fetch_all_character_info(
    session: aiohttp.ClientSession,
    ocid: str,
    headers: dict,
) -> dict:
    """
    캐릭터 OCID로 모든 상세 정보를 순차 조회합니다.

    순차 처리 이유: 넥슨 API 초당 호출 한도를 초과하지 않기 위함입니다.
    각 요청 사이에 REQUEST_DELAY_SECONDS만큼 대기합니다.

    Args:
        session: 재사용할 aiohttp 클라이언트 세션.
        ocid: 캐릭터 OCID.
        headers: 넥슨 API 요청 헤더.

    Returns:
        엔드포인트 키 → API 응답 딕셔너리 매핑.
    """
    character_info: dict = {}

    for endpoint_key in API_ENDPOINTS:
        if endpoint_key == "get_character_id":
            continue  # OCID 조회 엔드포인트는 건너뜁니다.

        character_info[endpoint_key] = await fetch_character_endpoint(
            session, endpoint_key, ocid, headers
        )
        await asyncio.sleep(REQUEST_DELAY_SECONDS)

    return character_info


async def fetch_account_character_list(api_key: str) -> list[dict]:
    """
    계정에 속한 모든 캐릭터 목록을 조회합니다.

    Args:
        api_key: 넥슨 API 키.

    Returns:
        캐릭터 정보 딕셔너리 리스트. 실패 시 빈 리스트.
    """
    url = _build_url("get_account_character_list")
    headers = build_headers(api_key)

    async with aiohttp.ClientSession() as session:
        response = await _request_with_retry(session, url, headers)
        if response and response.status == 200:
            data = await response.json()
            all_characters: list[dict] = []
            for account in data.get("account_list", []):
                all_characters.extend(account.get("character_list", []))
            return all_characters
        return []
