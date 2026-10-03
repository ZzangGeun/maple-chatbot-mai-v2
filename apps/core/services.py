import json
import logging
import time
from threading import Lock

import redis
from asgiref.sync import async_to_sync
from django.conf import settings
from django.core.cache.backends.locmem import LocMemCache
from redis.backoff import NoBackoff
from redis.retry import Retry

from common.utils.api_client import get_api_data

logger = logging.getLogger(__name__)

# Redis 장애가 홈페이지 응답을 오래 지연시키지 않도록 한 번만 연결합니다.
REDIS_URL = getattr(settings, "REDIS_URL", "redis://127.0.0.1:6379/0")
redis_client = redis.from_url(
    REDIS_URL,
    decode_responses=True,
    socket_connect_timeout=1,
    socket_timeout=1,
    retry=Retry(NoBackoff(), 0),
)

CACHE_DURATION = 3600  # 캐시 유효 기간: 1시간
REDIS_RETRY_AFTER_SECONDS = 60
_redis_retry_at = 0.0
_redis_state_lock = Lock()
# Redis를 사용할 수 없어도 같은 프로세스의 반복 요청은 API를 다시 호출하지 않습니다.
_fallback_cache = LocMemCache("mai-core-home-fallback", {})


def _redis_available() -> bool:
    with _redis_state_lock:
        return time.monotonic() >= _redis_retry_at


def _pause_redis(error: redis.RedisError) -> None:
    """연결 실패 후 잠시 재시도를 멈추고 같은 경고의 반복을 제한합니다."""
    global _redis_retry_at
    with _redis_state_lock:
        now = time.monotonic()
        if now < _redis_retry_at:
            return
        _redis_retry_at = now + REDIS_RETRY_AFTER_SECONDS
    logger.warning(
        "Redis 홈 캐시를 사용할 수 없어 %d초 동안 메모리 캐시를 사용합니다. "
        "Redis 실행 상태와 REDIS_URL을 확인하세요: %s",
        REDIS_RETRY_AFTER_SECONDS,
        error,
    )


def save_data_to_redis(key: str, data: dict | list) -> None:
    """홈 데이터를 캐시합니다. Redis 장애 시에는 메모리 캐시만 사용합니다."""
    try:
        payload = json.dumps(data, ensure_ascii=False)
    except (TypeError, ValueError) as error:
        logger.warning("홈 데이터를 JSON 캐시에 저장할 수 없습니다 (%s): %s", key, error)
        return

    _fallback_cache.set(key, data, timeout=CACHE_DURATION)
    if not _redis_available():
        return
    try:
        redis_client.setex(key, CACHE_DURATION, payload)
    except redis.RedisError as error:
        _pause_redis(error)
    else:
        logger.info("데이터가 Redis에 캐시되었습니다: %s", key)


def load_data_from_redis(key: str) -> dict | list | None:
    """Redis 캐시를 우선 조회하고, 연결 실패 시 메모리 캐시를 반환합니다."""
    if not _redis_available():
        return _fallback_cache.get(key)
    try:
        raw = redis_client.get(key)
    except redis.RedisError as error:
        _pause_redis(error)
        return _fallback_cache.get(key)

    if raw:
        try:
            data = json.loads(raw)
        except (json.JSONDecodeError, TypeError) as error:
            logger.warning("Redis 홈 캐시의 JSON 형식이 올바르지 않습니다 (%s): %s", key, error)
        else:
            if isinstance(data, (dict, list)):
                return data
            logger.warning("Redis 홈 캐시가 dict 또는 list 형식이 아닙니다 (%s)", key)
    return _fallback_cache.get(key)


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
