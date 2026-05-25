# services/nexon/client.py
"""
넥슨 Open API HTTP 클라이언트

aiohttp를 사용한 순수 API 호출 로직만 담당합니다.
비즈니스 로직(캐싱, 파일 저장 등)은 character_service.py에 위임합니다.
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


def _build_headers(api_key: str) -> dict:
    """넥슨 API 요청에 필요한 헤더를 반환합니다."""
    return {
        "x-nxopen-api-key": api_key.strip(),
        "Content-Type": "application/json",
        "User-Agent": "MAI-Help-You/1.0",
    }


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

    async with session.get(url, headers=headers) as response:
        if response.status != 200:
            logger.error(f"OCID 조회 실패 (HTTP {response.status}): {character_name}")
            return None

        data = await response.json()
        return data.get("ocid") or None


async def _fetch_single_endpoint(
    session: aiohttp.ClientSession,
    endpoint_key: str,
    ocid: str,
    headers: dict,
) -> dict:
    """
    단일 엔드포인트에서 캐릭터 정보를 조회합니다.
    429(Rate Limit) 발생 시 1회 재시도합니다.

    Args:
        session: 재사용할 aiohttp 클라이언트 세션.
        endpoint_key: API_ENDPOINTS의 키 이름.
        ocid: 캐릭터 OCID.
        headers: 넥슨 API 요청 헤더.

    Returns:
        API 응답 딕셔너리. 실패 시 빈 딕셔너리.
    """
    url = _build_url(endpoint_key, ocid=ocid)

    async with session.get(url, headers=headers) as response:
        if response.status == 200:
            return await response.json()

        if response.status == 429:
            # Rate Limit: 잠시 대기 후 1회 재시도합니다.
            logger.warning(f"Rate Limit 발생, {RATE_LIMIT_RETRY_DELAY_SECONDS}초 후 재시도: {endpoint_key}")
            await asyncio.sleep(RATE_LIMIT_RETRY_DELAY_SECONDS)
            async with session.get(url, headers=headers) as retry:
                if retry.status == 200:
                    return await retry.json()

        logger.warning(f"엔드포인트 조회 실패 (HTTP {response.status}): {endpoint_key}")
        return {}


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

        character_info[endpoint_key] = await _fetch_single_endpoint(
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
    headers = {"x-nxopen-api-key": api_key}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status != 200:
                    logger.error(f"캐릭터 목록 조회 실패: HTTP {response.status}")
                    return []

                data = await response.json()
                all_characters: list[dict] = []
                for account in data.get("account_list", []):
                    all_characters.extend(account.get("character_list", []))
                return all_characters

    except aiohttp.ClientError as e:
        logger.error(f"캐릭터 목록 조회 중 네트워크 오류: {e}")
        return []
