# common/nexon/constants.py
"""
넥슨 Open API 관련 상수 모음

Django(캐릭터 검색·연동)와 AI 서버(챗봇 캐릭터 조회)가 함께 사용합니다.
"""

import os
from datetime import timedelta

from common.constants.api import NEXON_BASE_URL

BASE_URL = NEXON_BASE_URL

OCID_PATH = "/id"
ACCOUNT_CHARACTER_LIST_PATH = "/character/list"

# 캐릭터 검색 화면이 한 번에 조회하는 엔드포인트.
# 키 이름은 extractors.all_info_extract가 응답을 찾을 때 사용합니다.
CHARACTER_INFO_ENDPOINTS: dict[str, str] = {
    "get_character_basic_info": "/character/basic",
    "get_character_stat_info": "/character/stat",
    "get_character_hyper_stat_info": "/character/hyper-stat",
    "get_character_ability_info": "/character/ability",
    "get_character_item_equipment_info": "/character/item-equipment",
    "get_character_pet_equipment_info": "/character/pet-equipment",
    "get_character_symbol_info": "/character/symbol-equipment",
    "get_character_set_effect_info": "/character/set-effect",
    "get_character_link_skill_info": "/character/link-skill",
    "get_character_vmatrix_info": "/character/vmatrix",
    "get_character_hexamatrix_info": "/character/hexamatrix",
    "get_character_hexamatrix_stat_info": "/character/hexamatrix-stat",
    "get_character_other_stat_info": "/character/other-stat",
    "get_character_popularity_info": "/character/popularity",
}

# 요청 제한 시간과 재시도 정책 (429, 5xx, 네트워크 오류만 재시도합니다)
REQUEST_TIMEOUT_SECONDS = 10
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 1.0

# 한 캐릭터를 조회할 때 동시에 보내는 최대 요청 수
MAX_CONCURRENT_REQUESTS = 4

# 프로세스당 초당 요청 수 상한. 요청 시작 시각을 고르게 띄워 429(호출 한도 초과)를 피합니다.
# 개발 단계 키는 초당 한도가 낮으므로 기본값을 5로 두고, 서비스 단계 키로 바꾸면 올려서 사용합니다.
# 0 이하면 제한하지 않습니다.
REQUESTS_PER_SECOND = float(os.getenv("NEXON_REQUESTS_PER_SECOND", "5"))

# 캐시 유효 기간
#   - 캐릭터명 → OCID: 닉네임 변경 외에는 바뀌지 않으므로 길게 둡니다.
#   - 캐릭터 정보: 장비 교체 등이 너무 늦게 반영되지 않도록 짧게 둡니다.
OCID_CACHE_TTL = timedelta(days=1)
CHARACTER_CACHE_TTL = timedelta(minutes=15)

# 넥슨 Open API 오류 코드
ERROR_INVALID_ID = "OPENAPI00003"  # 유효하지 않은 식별자(OCID)
ERROR_INVALID_PARAMETER = "OPENAPI00004"  # 파라미터 오류 (/id에서는 존재하지 않는 캐릭터명)
ERROR_INVALID_API_KEY = "OPENAPI00005"
ERROR_RATE_LIMIT = "OPENAPI00007"
