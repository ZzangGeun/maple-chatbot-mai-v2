# common/utils/api_client.py
"""
범용 Nexon API HTTP 클라이언트

Nexon Open API 호출을 위한 공통 함수입니다.
core 앱에서 분리하여 common에 배치함으로써,
services/nexon과 apps/core 양쪽에서 의존 방향이 깔끔해집니다.
"""

import asyncio
import logging

import aiohttp
from django.conf import settings

from common.constants.api import NEXON_BASE_URL
from common.utils.datetime_util import get_yesterday_str
from common.exceptions.nexon import ApiRateLimitExceeded, NexonApiError

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
INITIAL_RETRY_DELAY_SECONDS = 1.0


async def get_api_data(
    endpoint: str, params: dict | None = None
) -> dict | list | None:
    """공통 Nexon API 호출 유틸 (비동기)

    - 헤더에 `x-nxopen-api-key`를 포함
    - 날짜 파라미터가 필요한 엔드포인트에 대해 기본 날짜를 추가
    - 오류 로깅 후 예외 발생 또는 None 반환

    Args:
        endpoint: API 엔드포인트 경로 (예: "/notice", "/ranking/overall").
        params: 추가 쿼리 파라미터.

    Returns:
        JSON 응답 데이터(dict 또는 list). 실패 시 None.
    """
    api_key = getattr(settings, "NEXON_API_KEY", "")
    if not api_key:
        logger.error("NEXON_API_KEY가 설정되지 않았습니다.")
        raise NexonApiError("API 키가 없습니다.", status_code=500)

    headers = {"x-nxopen-api-key": api_key}
    url = f"{NEXON_BASE_URL}{endpoint}"

    request_params = dict(params or {})

    date_required_endpoints = [
        "/ranking/overall",
    ]

    if endpoint in date_required_endpoints and "date" not in request_params:
        request_params["date"] = get_yesterday_str()

    try:
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            delay = INITIAL_RETRY_DELAY_SECONDS
            for attempt in range(1, MAX_RETRIES + 1):
                async with session.get(
                    url,
                    headers=headers,
                    params=request_params,
                ) as response:
                    if response.status == 200:
                        return await response.json()

                    response_text = await response.text()
                    retryable = response.status == 429 or 500 <= response.status < 600
                    if retryable and attempt < MAX_RETRIES:
                        logger.warning(
                            "Nexon API HTTP %d. %d/%d차 요청 재시도",
                            response.status,
                            attempt,
                            MAX_RETRIES,
                        )
                        await asyncio.sleep(delay)
                        delay *= 2
                        continue

                    logger.error(
                        "API 요청 실패: %s, 상태 코드: %d, 파라미터: %s, 응답: %s",
                        url,
                        response.status,
                        request_params,
                        response_text,
                    )
                    if response.status == 429:
                        raise ApiRateLimitExceeded()
                    raise NexonApiError(f"API 요청 실패 (HTTP {response.status})")

    except (aiohttp.ClientError, asyncio.TimeoutError) as e:
        logger.error("API 요청 중 예외 발생: %s, 오류: %s", url, e)
        raise NexonApiError("API 네트워크 오류 발생")
