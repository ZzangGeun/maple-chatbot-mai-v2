import json
import logging
import time

import redis
from asgiref.sync import async_to_sync
from bs4 import BeautifulSoup
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


def get_notice_detail(endpoint: str, notice_id: int) -> str:
    """
    Nexon API의 /detail 엔드포인트를 호출하여 공지사항 본문 내용을 가져옵니다.

    Args:
        endpoint: API 엔드포인트 경로 (예: /notice/detail)
        notice_id: 조회할 공지사항 ID

    Returns:
        str: HTML 태그가 제거된 공지사항 본문. 실패 시 빈 문자열
    """
    try:
        # endpoint 예: /notice/detail, /notice-event/detail 등
        _get_api_data = async_to_sync(get_api_data)
        detail_data = _get_api_data(endpoint, params={"notice_id": notice_id})
        if detail_data:
            # 넥슨 API에 따라 'contents' 또는 'content' 필드에 내용이 있음
            raw_content = detail_data.get("contents") or detail_data.get("content")

            if raw_content:
                # HTML 태그 제거
                soup = BeautifulSoup(raw_content, "html.parser")
                content = soup.get_text(separator="\n").strip()
                return content
            else:
                logger.warning(
                    f"상세 데이터에 내용 필드가 없습니다: {list(detail_data.keys())} (ID: {notice_id})"
                )
        else:
            logger.warning(f"상세 데이터를 가져오지 못했습니다. (ID: {notice_id})")
    except Exception as e:
        logger.error(f"공지사항 상세 내용 가져오기 실패 ({endpoint}, {notice_id}): {e}")
    return ""


def sync_notices_to_rag() -> bool:
    """
    최신 공지사항/이벤트를 가져와서 RAG용 JSON 파일로 저장합니다.
    넥슨 API의 상세 페이지 엔드포인트를 활용합니다.

    Returns:
        bool: 동기화 성공 여부
    """
    logger.info("RAG용 공지사항 동기화 시작")

    notice_data = get_notice_list()
    if not notice_data:
        logger.warning("가져올 공지사항 데이터가 없습니다.")
        return False

    rag_docs = []

    # 처리할 카테고리 정의 (리스트 엔드포인트 키 : 상세 엔드포인트 경로 : 아이템 리스트 키)
    categories = [
        ("notice_general", "/notice/detail", "notice"),
        ("notice_event", "/notice-event/detail", "event_notice"),
        ("notice_cashshop", "/notice-cashshop/detail", "cashshop_notice"),
        ("notice_update", "/notice-update/detail", "update_notice"),
    ]

    for cat_key, detail_endpoint, item_key in categories:
        items = notice_data.get(cat_key, {}).get(item_key, [])
        # 최신 20개만 처리하여 API 호출 제한 방지
        items = items[:20]
        logger.info(f"{cat_key} 카테고리 처리 중... ({len(items)}건)")

        for item in items:
            title = item.get("title", "제목 없음")
            notice_id = item.get("notice_id")
            url = item.get("url", "")
            date_str = item.get("date", "")

            if not notice_id:
                logger.warning(f"notice_id 누락: {title}")
                continue

            logger.debug(f"문서화 중: {title[:30]}...")

            # API를 통한 본문 추출
            content = get_notice_detail(detail_endpoint, notice_id)

            # API 호출 간 지연 (429 에러 방지)
            time.sleep(0.5)

            # RAG 형식으로 구성
            doc = {
                "title": f"[{cat_key.replace('notice_', '')}] {title}",
                "content": content
                if content
                else f"본문 내용을 가져올 수 없습니다. 링크를 확인하세요: {url}",
                "content_type": "notice",
                "source": url,
                "metadata": {
                    "category": cat_key,
                    "date": date_str,
                    "notice_id": notice_id,
                    "original_title": title,
                },
            }
            rag_docs.append(doc)

    # Redis에 RAG 문서 JSON 저장
    try:
        redis_client.set("rag_docs:notices", json.dumps(rag_docs, ensure_ascii=False))
        logger.info(
            f"RAG용 공지사항 데이터가 Redis (rag_docs:notices)에 저장되었습니다. (총 {len(rag_docs)}건)"
        )
        return True
    except Exception as e:
        logger.error(f"Redis RAG용 공지사항 저장 중 오류 발생: {e}")
        return False
