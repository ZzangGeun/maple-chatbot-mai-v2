# ai_server/graph/tools/nexon_api_tool.py
"""
넥슨 메이플스토리 Open API 클라이언트 (뼈대)

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

TODO:
  - 각 메서드에 실제 API 호출 로직 구현
  - 응답 데이터를 Pydantic 모델로 구조화
  - Rate limit(429) 재시도 로직 추가
"""

import logging
from typing import Any

import aiohttp

from ai_server.config import settings

logger = logging.getLogger("NexonAPIClient")

# 넥슨 Open API 베이스 URL
_BASE_URL = "https://open.api.nexon.com/maplestory/v1"


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
        }

    # ------------------------------------------------------------------
    # 내부 유틸
    # ------------------------------------------------------------------

    async def _get(self, endpoint: str, params: dict[str, Any] | None = None) -> dict:
        """
        GET 요청을 비동기로 수행합니다.

        Args:
            endpoint: 베이스 URL 이후 경로 (예: "/id")
            params  : 쿼리 파라미터

        Returns:
            파싱된 JSON 딕셔너리.

        Raises:
            aiohttp.ClientResponseError: 4xx/5xx 응답 시.
        """
        url = f"{_BASE_URL}{endpoint}"
        async with aiohttp.ClientSession(headers=self._headers) as session:
            async with session.get(url, params=params) as response:
                # 429(Rate Limit), 500(서버 오류) 등을 명시적으로 처리합니다.
                if response.status == 429:
                    logger.warning("넥슨 API Rate Limit 초과. 잠시 후 재시도 하세요.")
                    raise aiohttp.ClientResponseError(
                        response.request_info,
                        response.history,
                        status=429,
                        message="Too Many Requests",
                    )
                response.raise_for_status()
                return await response.json()

    # ------------------------------------------------------------------
    # 공개 API 메서드
    # ------------------------------------------------------------------

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
        # TODO: 실제 API 호출 구현
        # data = await self._get("/id", params={"character_name": character_name})
        # return data["ocid"]
        logger.info(f"[TODO] get_ocid 호출: character_name={character_name}")
        return "SKELETON_OCID"

    async def get_character_basic(self, ocid: str) -> dict:
        """
        캐릭터 기본 정보를 조회합니다.
        (레벨, 직업, 월드, 길드, 인기도 등)

        Args:
            ocid: 캐릭터 고유 식별자.

        Returns:
            캐릭터 기본 정보 딕셔너리.
        """
        # TODO: 실제 API 호출 구현
        # return await self._get("/character/basic", params={"ocid": ocid})
        logger.info(f"[TODO] get_character_basic 호출: ocid={ocid}")
        return {
            "character_name": "SKELETON_NAME",
            "character_level": 0,
            "character_class": "SKELETON_CLASS",
            "world_name": "SKELETON_WORLD",
        }

    async def get_character_stat(self, ocid: str) -> dict:
        """
        캐릭터 스탯 정보를 조회합니다.
        (전투력, 데미지, 보스 데미지 등 주요 스탯 포함)

        Args:
            ocid: 캐릭터 고유 식별자.

        Returns:
            캐릭터 스탯 딕셔너리.
        """
        # TODO: 실제 API 호출 구현
        # return await self._get("/character/stat", params={"ocid": ocid})
        logger.info(f"[TODO] get_character_stat 호출: ocid={ocid}")
        return {"final_stat": []}

    async def get_character_item_equipment(self, ocid: str) -> dict:
        """
        캐릭터 장착 아이템 정보를 조회합니다.

        Args:
            ocid: 캐릭터 고유 식별자.

        Returns:
            장착 아이템 리스트 딕셔너리.
        """
        # TODO: 실제 API 호출 구현
        # return await self._get("/character/item-equipment", params={"ocid": ocid})
        logger.info(f"[TODO] get_character_item_equipment 호출: ocid={ocid}")
        return {"item_equipment": []}

    async def get_character_summary(self, character_name: str) -> dict:
        """
        캐릭터명으로 기본 정보 + 스탯을 한 번에 조회하는 편의 메서드.

        내부적으로 get_ocid → get_character_basic → get_character_stat 순으로 호출합니다.

        Args:
            character_name: 조회할 캐릭터 이름.

        Returns:
            {"basic": {...}, "stat": {...}} 형태의 통합 딕셔너리.
        """
        try:
            ocid = await self.get_ocid(character_name)
            basic = await self.get_character_basic(ocid)
            stat = await self.get_character_stat(ocid)
            return {"basic": basic, "stat": stat}
        except aiohttp.ClientResponseError as e:
            logger.error(f"넥슨 API 오류 (status={e.status}): {e.message}")
            raise
        except (aiohttp.ClientConnectionError, TimeoutError) as e:
            logger.error(f"넥슨 API 네트워크 연결 또는 타임아웃 오류: {e}")
            raise
        except ValueError as e:
            logger.error(f"캐릭터 정보 처리 중 값 오류: {e}")
            raise
        except Exception as e:
            logger.error(f"캐릭터 조회 중 예상치 못한 오류: {e}")
            raise
