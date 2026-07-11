# ai_server/graph/tools/nexon_api_tool.py
"""
넥슨 메이플스토리 Open API 클라이언트

담당 역할:
  - 캐릭터 식별자(ocid) 조회
  - 캐릭터 기본 정보 조회 (레벨, 직업, 월드, 길드 등)
  - 캐릭터 스탯 조회
  - 장착 아이템 정보 조회

사용 방법:
  client = NexonAPIClient()
  data   = await client.get_character_summary("홍길동")

환경변수:
  NEXON_API_KEY — 넥슨 Open API 발급 키 (코드에 절대 하드코딩 금지)

"""

import asyncio
import logging
from typing import Any

import aiohttp

from ai_server.config import settings
from common.constants.api import NEXON_BASE_URL

logger = logging.getLogger("NexonAPIClient")

_BASE_URL = NEXON_BASE_URL
_MAX_RETRIES = 3
_INITIAL_RETRY_DELAY_SECONDS = 1.0
_REQUEST_TIMEOUT_SECONDS = 10


class NexonAPIClient:
    """
    넥슨 메이플스토리 Open API 비동기 클라이언트.

    aiohttp를 사용하여 비동기로 API를 호출합니다.
    API Key는 환경변수에서만 로드합니다.
    """

    def __init__(self) -> None:
        self._api_key: str = settings.api.nexon_api_key
        if not self._api_key:
            logger.warning("NEXON_API_KEY가 설정되지 않았습니다. API 호출이 실패합니다.")

        # 모든 요청에 공통으로 사용하는 인증 헤더
        self._headers: dict[str, str] = {
            "x-nxopen-api-key": self._api_key,
            "User-Agent": "MAI-Help-You-AI/1.0",
        }

    async def _get(self, endpoint: str, params: dict[str, Any] | None = None) -> dict:
        """GET 요청을 재시도 정책과 함께 비동기로 수행합니다."""
        if not self._api_key:
            raise ValueError("NEXON_API_KEY가 설정되지 않았습니다.")

        url = f"{_BASE_URL}{endpoint}"
        timeout = aiohttp.ClientTimeout(total=_REQUEST_TIMEOUT_SECONDS)
        delay = _INITIAL_RETRY_DELAY_SECONDS

        async with aiohttp.ClientSession(
            headers=self._headers,
            timeout=timeout,
        ) as session:
            for attempt in range(1, _MAX_RETRIES + 1):
                try:
                    async with session.get(url, params=params) as response:
                        if response.status == 200:
                            return await response.json()

                        retryable = response.status == 429 or 500 <= response.status < 600
                        if retryable and attempt < _MAX_RETRIES:
                            logger.warning(
                                "Nexon API HTTP %d. %d/%d차 요청 재시도",
                                response.status,
                                attempt,
                                _MAX_RETRIES,
                            )
                            await asyncio.sleep(delay)
                            delay *= 2
                            continue

                        response.raise_for_status()
                except (aiohttp.ClientConnectionError, asyncio.TimeoutError):
                    if attempt == _MAX_RETRIES:
                        raise
                    logger.warning(
                        "Nexon API 네트워크 오류. %d/%d차 요청 재시도",
                        attempt,
                        _MAX_RETRIES,
                    )
                    await asyncio.sleep(delay)
                    delay *= 2

        raise RuntimeError("Nexon API 요청이 응답 없이 종료되었습니다.")

    async def get_ocid(self, character_name: str) -> str:
        """
        캐릭터명으로 고유 식별자(ocid)를 조회합니다.
        넥슨 API는 ocid를 기준으로 모든 캐릭터 정보를 조회하므로
        대부분의 메서드에서 이 메서드를 먼저 호출해야 합니다.

        Args:
            character_name: 조회할 캐릭터 이름.

        Returns:
            ocid 문자열.
        """
        normalized_name = character_name.strip()
        if not normalized_name:
            raise ValueError("캐릭터명이 비어 있습니다.")

        data = await self._get(
            "/id",
            params={"character_name": normalized_name},
        )
        ocid = data.get("ocid")
        if not ocid:
            raise ValueError(f"캐릭터 '{normalized_name}'의 OCID를 찾을 수 없습니다.")
        return ocid

    async def get_character_basic(self, ocid: str) -> dict:
        """
        캐릭터 기본 정보를 조회합니다.
        (레벨, 직업, 월드, 길드, 인기도 등)

        Args:
            ocid: 캐릭터 고유 식별자.

        Returns:
            캐릭터 기본 정보 딕셔너리.
        """
        if not ocid:
            raise ValueError("OCID가 비어 있습니다.")
        return await self._get("/character/basic", params={"ocid": ocid})

    async def get_character_stat(self, ocid: str) -> dict:
        """
        캐릭터 스탯 정보를 조회합니다.
        (전투력, 데미지, 보스 데미지 등 주요 스탯 포함)

        Args:
            ocid: 캐릭터 고유 식별자.

        Returns:
            캐릭터 스탯 딕셔너리.
        """
        if not ocid:
            raise ValueError("OCID가 비어 있습니다.")
        return await self._get("/character/stat", params={"ocid": ocid})

    async def get_character_item_equipment(self, ocid: str) -> dict:
        """
        캐릭터 장착 아이템 정보를 조회합니다.

        Args:
            ocid: 캐릭터 고유 식별자.

        Returns:
            장착 아이템 리스트 딕셔너리.
        """
        if not ocid:
            raise ValueError("OCID가 비어 있습니다.")
        return await self._get(
            "/character/item-equipment",
            params={"ocid": ocid},
        )

    async def get_character_summary(self, character_name: str) -> dict:
        """
        캐릭터명으로 기본 정보 + 스탯을 한 번에 조회하는 편의 메서드.

        내부적으로 get_ocid → get_character_basic → get_character_stat 순으로 호출합니다.

        Args:
            character_name: 조회할 캐릭터 이름.

        Returns:
            {"basic": {...}, "stat": {...}} 형태의 통합 딕셔너리.
        """
        ocid = await self.get_ocid(character_name)
        basic, stat = await asyncio.gather(
            self.get_character_basic(ocid),
            self.get_character_stat(ocid),
        )
        return {"basic": basic, "stat": stat}
