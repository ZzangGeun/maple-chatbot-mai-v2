# common/utils/api_client.py
"""
범용 Nexon API HTTP 클라이언트

Nexon Open API 호출을 위한 공통 함수입니다.
core 앱에서 분리하여 common에 배치함으로써,
services/nexon과 apps/core 양쪽에서 의존 방향이 깔끔해집니다.
"""

import logging
import aiohttp
from django.conf import settings

from common.constants.api import NEXON_BASE_URL
from common.utils.datetime_util import get_yesterday_str
from common.exceptions.nexon import ApiRateLimitExceeded, NexonApiError

logger = logging.getLogger(__name__)


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

    if params is None:
        params = {}

    date_required_endpoints = [
        "/ranking/overall",
    ]

    if endpoint in date_required_endpoints and "date" not in params:
        params["date"] = get_yesterday_str()

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 429:
                    raise ApiRateLimitExceeded()
                else:
                    text = await response.text()
                    logger.error(
                        "API 요청 실패: %s, 상태 코드: %d, 파라미터: %s, 응답: %s",
                        url,
                        response.status,
                        params,
                        text,
                    )
                    raise NexonApiError(f"API 요청 실패 (HTTP {response.status})")

    except aiohttp.ClientError as e:
        logger.error("API 요청 중 예외 발생: %s, 오류: %s", url, e)
        raise NexonApiError("API 네트워크 오류 발생")
