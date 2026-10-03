import json
import logging

import redis
from asgiref.sync import async_to_sync
from django.conf import settings

from common.utils.api_client import get_api_data

logger = logging.getLogger(__name__)

# Redis 연결 설정
REDIS_URL = getattr(settings, "REDIS_URL", "redis://127.0.0.1:6379/0")
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

CACHE_DURATION = 3600  # 캐시 유효 기간 설정 (초 단위: 1시간)


def save_data_to_redis(key: str, data: dict | list) -> None:
    """Redis에 데이터를 캐싱하는 제네릭 함수"""
    try:
        redis_client.setex(key, CACHE_DURATION, json.dumps(data, ensure_ascii=False))
        logger.info(f"데이터가 Redis에 캐시되었습니다: {key}")
    except Exception as e:
        logger.error(f"Redis 데이터 저장 중 오류 발생 ({key}): {e}")


def load_data_from_redis(key: str) -> dict | list | None:
    """Redis에서 캐싱된 데이터를 불러오는 제네릭 함수"""
    try:
        data = redis_client.get(key)
        if data:
            return json.loads(data)
    except Exception as e:
        logger.error(f"Redis 데이터 로드 중 오류 발생 ({key}): {e}")
    return None


# 도메인별 Redis 캐시 접근 래핑 함수 (views.py에서 import하기 위한 별칭)
def load_notice_data_from_redis() -> dict | None:
    """Redis에서 공지사항 캐시 데이터를 불러옵니다."""
    return load_data_from_redis("cache:notice_list")


def load_ranking_data_from_redis() -> dict | None:
    """Redis에서 랭킹 캐시 데이터를 불러옵니다."""
    return load_data_from_redis("cache:ranking_list")


def save_notice_data_to_redis(data: dict) -> None:
    """공지사항 데이터를 Redis에 캐싱합니다."""
    save_data_to_redis("cache:notice_list", data)


def save_ranking_data_to_redis(data: dict) -> None:
    """랭킹 데이터를 Redis에 캐싱합니다."""
    save_data_to_redis("cache:ranking_list", data)


def get_notice_list() -> dict:
    """
    공지사항 데이터를 Nexon API에서 가져와서 Redis에 캐시하고 반환합니다.
    캐시가 있고 최신이면(1시간 이내) API 호출 없이 캐시 데이터를 반환합니다.
    """
    cached_data = load_notice_data_from_redis()
    if cached_data:
        logger.info("Redis에 캐시된 공지사항 데이터를 사용합니다.")
        return cached_data

    # 비동기로 변경된 get_api_data를 동기 환경에서 호출
    _get_api_data = async_to_sync(get_api_data)

    notice_general = _get_api_data("/notice")
    notice_event = _get_api_data("/notice-event")
    notice_cashshop = _get_api_data("/notice-cashshop")
    notice_update = _get_api_data("/notice-update")

    notice_data = {
        "notice_general": notice_general,
        "notice_event": notice_event,
        "notice_cashshop": notice_cashshop,
        "notice_update": notice_update,
    }

    save_notice_data_to_redis(notice_data)

    return notice_data


def get_ranking_list() -> dict:
    """
    랭킹 데이터를 Nexon API에서 가져와서 Redis에 캐시하고 반환합니다.
    상위 50위까지만 저장합니다.
    """
    cached_data = load_ranking_data_from_redis()
    if cached_data:
        logger.info("Redis에 캐시된 랭킹 데이터를 사용합니다.")
        return cached_data

    _get_api_data = async_to_sync(get_api_data)
    overall_ranking = _get_api_data("/ranking/overall")

    # JSON 구조: overall_ranking -> ranking 배열
    ranking_list = []
    if overall_ranking and isinstance(overall_ranking, dict):
        ranking_list = overall_ranking.get("ranking", [])
    elif isinstance(overall_ranking, list):
        ranking_list = overall_ranking

    # 상위 50위까지만 저장
    ranking_list = ranking_list[:50] if ranking_list else []

    ranking_data = {"overall_ranking": ranking_list}

    save_ranking_data_to_redis(ranking_data)

    return ranking_data
