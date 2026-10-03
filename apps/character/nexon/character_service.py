# apps/character/nexon/character_service.py
"""
캐릭터 서비스 오케스트레이터

캐시 조회 → API 호출 → 데이터 추출 → 저장 흐름을 조율합니다.
HTTP 호출과 응답 캐시(Redis, AI 서버와 공유)는 공용 넥슨 클라이언트(common.nexon)에,
응답 정제는 common.nexon.extractors에 위임합니다.
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

from django.conf import settings
from django.core.cache import cache

from common.exceptions.base import AppException
from common.exceptions.nexon import CharacterNotFound
from common.nexon import NexonCache, NexonClient
from common.nexon.constants import CHARACTER_INFO_ENDPOINTS
from common.nexon.extractors import all_info_extract

logger = logging.getLogger(__name__)

# 정제된 캐릭터 정보(검색 화면 응답) 캐시 유효 기간
CACHE_DURATION = timedelta(hours=1)

_shared_cache: NexonCache | None = None


def _get_shared_cache() -> NexonCache | None:
    """AI 서버와 함께 쓰는 넥슨 API 응답 캐시(Redis)를 반환합니다."""
    global _shared_cache

    if not getattr(settings, "NEXON_CACHE_ENABLED", True):
        return None
    if _shared_cache is None:
        _shared_cache = NexonCache(settings.REDIS_URL)
    return _shared_cache


def get_nexon_client(api_key: str | None = None) -> NexonClient:
    """넥슨 API 클라이언트를 만듭니다. api_key가 없으면 서비스 키(NEXON_API_KEY)를 사용합니다."""
    return NexonClient(
        api_key or getattr(settings, "NEXON_API_KEY", ""),
        cache=_get_shared_cache(),
    )


def save_character_data_to_json(
    character_name: str,
    character_data: dict,
    save_dir: str = "data/character_data",
) -> str | None:
    """
    캐릭터 데이터를 JSON 파일로 저장합니다.

    Args:
        character_name: 파일명에 사용할 캐릭터 이름.
        character_data: 저장할 데이터 딕셔너리.
        save_dir: 저장 디렉터리 경로 (기본값: "data/character_data").

    Returns:
        저장된 파일 경로 문자열, 실패 시 None.
    """
    try:
        save_path = Path(save_dir)
        save_path.mkdir(parents=True, exist_ok=True)

        # 파일시스템에 안전한 문자만 허용합니다.
        safe_name = "".join(
            c for c in character_name if c.isalnum() or c in (" ", "-", "_")
        ).rstrip()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = save_path / f"{safe_name}_{timestamp}.json"

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(character_data, f, ensure_ascii=False, indent=2)

        return str(file_path)

    except OSError as e:
        logger.error(f"JSON 파일 저장 중 오류 발생: {e}")
        return None


async def get_character_data(
    character_name: str,
    api_key: str | None = None,
) -> dict | None:
    """
    캐릭터 이름으로 종합 정보를 반환합니다.

    처리 순서:
      1. 정제된 정보 캐시 확인 (Django 캐시)
      2. 캐시 미스 → 넥슨 API 조회 (엔드포인트 응답은 Redis에 따로 캐싱)
      3. 데이터 추출 및 정제
      4. 캐시 저장 + JSON 파일 저장

    Args:
        character_name: 조회할 캐릭터 이름.
        api_key: 사용할 API 키. None이면 환경변수에서 로드합니다.

    Returns:
        정제된 캐릭터 정보 딕셔너리. 캐릭터가 없거나 조회에 실패하면 None.
    """
    if not character_name or not character_name.strip():
        return None

    # 1. 캐시 확인
    cache_key = f"character_info_{character_name}"
    cached_data = cache.get(cache_key)
    if cached_data:
        return cached_data

    # 2. 넥슨 API 조회 (일부 엔드포인트가 실패하면 해당 섹션은 빈 값으로 채웁니다)
    client = get_nexon_client(api_key)
    try:
        result = await client.fetch_character(
            CHARACTER_INFO_ENDPOINTS.values(), character_name=character_name
        )
    except CharacterNotFound:
        logger.info(f"존재하지 않는 캐릭터: {character_name}")
        return None
    except AppException as e:
        logger.error(f"캐릭터 정보 조회 실패 ({character_name}): {e.message}")
        return None

    raw_info = {
        key: result.responses.get(path, {})
        for key, path in CHARACTER_INFO_ENDPOINTS.items()
    }

    # 3. 데이터 추출
    extracted_info = all_info_extract(raw_info)

    # 4. 캐시 저장 및 JSON 파일 백업
    cache.set(cache_key, extracted_info, timeout=int(CACHE_DURATION.total_seconds()))
    save_character_data_to_json(character_name, extracted_info)

    return extracted_info


async def process_signup_with_key(api_key: str) -> tuple[str, str] | None:
    """
    API 키를 사용하여 계정 내 가장 레벨이 높은 캐릭터를 찾아 반환합니다.
    회원가입 자동 캐릭터 연동 시 사용됩니다.
    """
    if not api_key or not api_key.strip():
        return None

    try:
        all_characters = await NexonClient(api_key).get_account_characters()
    except AppException as e:
        logger.warning(f"계정 캐릭터 목록 조회 실패: {e.message}")
        return None
    if not all_characters:
        return None

    best = max(
        all_characters,
        key=lambda character: int(character.get("character_level", 0)),
    )
    character_name = best.get("character_name")
    character_ocid = best.get("ocid")
    if not character_name or not character_ocid:
        return None

    if await get_character_data(character_name, api_key):
        return character_name, character_ocid
    return None
