from datetime import datetime, timedelta
import requests
import logging
import os
from django.conf import settings

# BASE_URL과 NEXON_API_KEY는 settings.py가 단일 소스입니다.
# character/get_character_info.py에도 동일 상수가 있었으나 중복이므로 여기서만 정의합니다.
BASE_URL = "https://open.api.nexon.com/maplestory/v1"
NEXON_API_KEY = getattr(settings, 'NEXON_API_KEY', '') or os.getenv('NEXON_API_KEY', '')
logger = logging.getLogger(__name__)



def get_api_data(endpoint, params=None):
    """공통 Nexon API 호출 유틸

    - 헤더에 `x-nxopen-api-key`를 포함
    - 날짜 파라미터가 필요한 엔드포인트에 대해 기본 날짜를 추가
    - 오류 로깅 후 None 반환
    """
    headers = {'x-nxopen-api-key': NEXON_API_KEY}
    url = f'{BASE_URL}{endpoint}'

    if params is None:
        params = {}

    date_required_endpoints = [
        "/ranking/overall"
    ]

    if endpoint in date_required_endpoints and 'date' not in params:
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        params['date'] = yesterday

    try:
        response = requests.get(url, headers=headers, params=params)

        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f'API 요청 실패: {url}, 상태 코드: {response.status_code}, 파라미터: {params}, 응답: {response.text}')
            return None

    except requests.RequestException as e:
        logger.error(f'API 요청 중 예외 발생: {url}, 오류: {e}')
        return None
