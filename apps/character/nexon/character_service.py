# services/nexon/character_service.py
"""
캐릭터 서비스 오케스트레이터

캐시 조회 → API 호출 → 데이터 추출 → 저장 흐름을 조율합니다.
개별 책임은 client.py(HTTP)와 extractors.py(변환)에 위임합니다.
"""

import json
import logging
from datetime import datetime
from pathlib import Path

import aiohttp
from django.core.cache import cache

from apps.character.nexon.client import (
    fetch_account_character_list,
    fetch_all_character_info,
    fetch_character_ocid,
    _build_headers
)
from apps.character.nexon.constants import CACHE_DURATION, NEXON_API_KEY
from apps.character.nexon.extractors import all_info_extract

logger = logging.getLogger(__name__)





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
      1. 캐시 확인 (Redis 또는 Django 기본 캐시)
      2. 캐시 미스 → 넥슨 API 호출
      3. 데이터 추출 및 정제
      4. 캐시 저장 + JSON 파일 저장

    Args:
        character_name: 조회할 캐릭터 이름.
        api_key: 사용할 API 키. None이면 환경변수에서 로드합니다.

    Returns:
        정제된 캐릭터 정보 딕셔너리, 실패 시 None.
    """
    if not character_name or not character_name.strip():
        return None

    final_api_key = api_key or NEXON_API_KEY
    if not final_api_key or not final_api_key.strip():
        logger.error("NEXON_API_KEY가 설정되지 않았습니다.")
        return None

    # 1. 캐시 확인
    cache_key = f"character_info_{character_name}"
    cached_data = cache.get(cache_key)
    if cached_data:
        return cached_data

    try:
        headers = _build_headers(final_api_key)

        async with aiohttp.ClientSession() as session:
            # 2. OCID 조회
            ocid = await fetch_character_ocid(session, character_name, headers)
            if not ocid:
                return None

            # 3. 상세 정보 조회
            raw_info = await fetch_all_character_info(session, ocid, headers)

        # 4. 데이터 추출
        extracted_info = all_info_extract(raw_info)

        # 5. 캐시 저장 및 JSON 파일 백업
        cache.set(cache_key, extracted_info, timeout=int(CACHE_DURATION.total_seconds()))
        save_character_data_to_json(character_name, extracted_info)

        return extracted_info

    except Exception as e:
        logger.error(f"캐릭터 정보 조회 중 오류 발생: {e!s}")
        return None


async def process_signup_with_key(api_key: str) -> tuple[str, str] | None:
    """
    API 키를 사용하여 계정 내 가장 레벨이 높은 캐릭터를 찾아 반환합니다.
    회원가입 자동 캐릭터 연동 시 사용됩니다.

    Args:
        api_key: 사용자가 입력한 넥슨 API 키.

    Returns:
        (character_name, character_ocid) 튜플, 실패 시 None.
    """
    if not api_key or not api_key.strip():
        return None

    try:
        all_characters = await fetch_account_character_list(api_key)

        if not all_characters:
            return None

        # 레벨 내림차순 정렬 후 최고 레벨 캐릭터 선택
        all_characters.sort(
            key=lambda x: int(x.get("character_level", 0)), reverse=True
        )
        best = all_characters[0]
        character_name = best.get("character_name")
        character_ocid = best.get("ocid")

        if not character_name:
            return None

        # 상세 정보 조회를 통해 유효성 검증 및 캐싱
        result = await get_character_data(character_name, api_key)
        if result:
            return character_name, character_ocid

        return None

    except Exception as e:
        logger.error(f"회원가입 캐릭터 자동 연동 실패: {e!s}")
        return None
