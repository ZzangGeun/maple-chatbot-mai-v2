from django.conf import settings
import logging
import json
import os
from datetime import datetime, timedelta
from .api_client import get_api_data
from bs4 import BeautifulSoup
import time

logger = logging.getLogger(__name__)
CACHE_DURATION = timedelta(hours=1)  # 캐시 유효 기간 설정 (1시간)

NOTICE_JSON_PATH = os.path.join(settings.BASE_DIR, 'rag_documents', 'notices', 'notice_data_rag.json')
RANKING_JSON_PATH = os.path.join(settings.BASE_DIR, 'rag_documents', 'rankings', 'ranking_data_rag.json')

def get_notice_list() -> dict:
    """
    공지사항 데이터를 Nexon API에서 가져와서 JSON 파일로 저장하고 반환합니다.
    JSON 파일이 있고 최신이면(1시간 이내) API 호출 없이 파일 내용을 반환합니다.

    Returns:
        dict: 카테고리별 공지사항 데이터. 키: notice_general, notice_event 등
    """
    # 캐시 확인
    if os.path.exists(NOTICE_JSON_PATH):
        try:
            modified_time = datetime.fromtimestamp(os.path.getmtime(NOTICE_JSON_PATH))
            if datetime.now() - modified_time < CACHE_DURATION:
                data = load_notice_data_from_json()
                if data:
                    logger.info("캐시된 공지사항 데이터를 사용합니다.")
                    return data
        except Exception as e:
            logger.warning(f"캐시 확인 중 오류: {e}")

    # API 호출
    notice_general = get_api_data("/notice")
    notice_event = get_api_data("/notice-event")
    notice_cashshop = get_api_data("/notice-cashshop")
    notice_update = get_api_data("/notice-update")

    notice_data = {
        "notice_general": notice_general,
        "notice_event": notice_event,
        "notice_cashshop": notice_cashshop,
        "notice_update": notice_update
    }
    
    # JSON 파일로 저장
    save_notice_data_to_json(notice_data)

    return notice_data


def save_notice_data_to_json(notice_data: dict) -> None:
    """
    공지사항 데이터를 JSON 파일로 저장합니다.

    Args:
        notice_data: 저장할 공지사항 데이터
    """
    try:
        # character_data 디렉토리가 없으면 생성
        os.makedirs(os.path.dirname(NOTICE_JSON_PATH), exist_ok=True)
        
        # JSON 파일로 저장 (한글 지원)
        with open(NOTICE_JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(notice_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"공지사항 데이터가 {NOTICE_JSON_PATH}에 저장되었습니다.")
    except Exception as e:
        logger.error(f"공지사항 데이터 저장 중 오류 발생: {e}")


def load_notice_data_from_json() -> dict:
    """
    JSON 파일에서 공지사항 데이터를 로드합니다.

    Returns:
        dict: 로드된 공지사항 데이터. 파일이 없거나 오류 시 빈 딕셔너리 반환
    """
    try:
        if os.path.exists(NOTICE_JSON_PATH):
            with open(NOTICE_JSON_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"공지사항 데이터 로드 중 오류 발생: {e}")
    
    return {}


def save_ranking_data_to_json(ranking_data: dict) -> None:
    """
    랭킹 데이터를 JSON 파일로 저장합니다.

    Args:
        ranking_data: 저장할 랭킹 데이터
    """
    try:
        # character_data 디렉토리가 없으면 생성
        os.makedirs(os.path.dirname(RANKING_JSON_PATH), exist_ok=True)
        
        # JSON 파일로 저장 (한글 지원)
        with open(RANKING_JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(ranking_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"랭킹 데이터가 {RANKING_JSON_PATH}에 저장되었습니다.")
    except Exception as e:
        logger.error(f"랭킹 데이터 저장 중 오류 발생: {e}")


def load_ranking_data_from_json() -> dict:
    """
    JSON 파일에서 랭킹 데이터를 로드합니다.

    Returns:
        dict: 로드된 랭킹 데이터. 파일이 없거나 오류 시 빈 딕셔너리 반환
    """
    try:
        if os.path.exists(RANKING_JSON_PATH):
            with open(RANKING_JSON_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"랭킹 데이터 로드 중 오류 발생: {e}")
    
    return {}


def get_ranking_list() -> dict:
    """
    랭킹 데이터를 Nexon API에서 가져와서 JSON 파일로 저장하고 반환합니다.
    상위 50위까지만 저장합니다.

    Returns:
        dict: overall_ranking 키를 포함한 랭킹 데이터
    """
    overall_ranking = get_api_data("/ranking/overall")
    
    # JSON 구조: overall_ranking -> ranking 배열
    ranking_list = []
    if overall_ranking and isinstance(overall_ranking, dict):
        ranking_list = overall_ranking.get('ranking', [])
    elif isinstance(overall_ranking, list):
        ranking_list = overall_ranking
    
    # 상위 50위까지만 저장
    ranking_list = ranking_list[:50] if ranking_list else []
    
    ranking_data = {
        "overall_ranking": ranking_list
    }
    
    # JSON 파일로 저장
    save_ranking_data_to_json(ranking_data)
    
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
        detail_data = get_api_data(endpoint, params={"notice_id": notice_id})
        if detail_data:
            # 넥슨 API에 따라 'contents' 또는 'content' 필드에 내용이 있음
            raw_content = detail_data.get("contents") or detail_data.get("content")

            if raw_content:
                # HTML 태그 제거
                soup = BeautifulSoup(raw_content, 'html.parser')
                content = soup.get_text(separator='\n').strip()
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
        ('notice_general', '/notice/detail', 'notice'),
        ('notice_event', '/notice-event/detail', 'event_notice'),
        ('notice_cashshop', '/notice-cashshop/detail', 'cashshop_notice'),
        ('notice_update', '/notice-update/detail', 'update_notice')
    ]

    for cat_key, detail_endpoint, item_key in categories:
        items = notice_data.get(cat_key, {}).get(item_key, [])
        # 최신 20개만 처리하여 API 호출 제한 방지
        items = items[:20]
        logger.info(f"{cat_key} 카테고리 처리 중... ({len(items)}건)")

        for item in items:
            title = item.get('title', '제목 없음')
            notice_id = item.get('notice_id')
            url = item.get('url', '')
            date_str = item.get('date', '')

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
                "content": content if content else f"본문 내용을 가져올 수 없습니다. 링크를 확인하세요: {url}",
                "content_type": "notice",
                "source": url,
                "metadata": {
                    "category": cat_key,
                    "date": date_str,
                    "notice_id": notice_id,
                    "original_title": title
                }
            }
            rag_docs.append(doc)

    # JSON 저장
    try:
        abs_path = os.path.abspath(NOTICE_JSON_PATH)
        logger.info(f"파일 저장 시도: {abs_path}")

        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, 'w', encoding='utf-8') as f:
            json.dump(rag_docs, f, ensure_ascii=False, indent=2)

        logger.info(f"RAG용 공지사항 데이터가 {abs_path}에 저장되었습니다. (총 {len(rag_docs)}건)")
        return True
    except OSError as e:
        # IOError/FileNotFoundError 등 파일 시스템 오류를 구체적으로 잡음
        logger.error(f"RAG용 공지사항 저장 중 오류 발생: {e}")
        return False


