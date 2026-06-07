# services/nexon/constants.py
"""
넥슨 Open API 관련 상수 모음

변경 빈도가 낮은 상수를 한 곳에서 관리합니다.
API 엔드포인트 추가/변경 시 이 파일만 수정하면 됩니다.
"""

from datetime import timedelta
from django.conf import settings
from common.constants.api import NEXON_BASE_URL

# 넥슨 Open API 베이스 URL (common.constants 참조)
BASE_URL = NEXON_BASE_URL

# 캐릭터 정보 캐시 유효 기간
CACHE_DURATION = timedelta(hours=1)

# API 키는 settings에서 로드합니다.
NEXON_API_KEY: str | None = getattr(settings, "NEXON_API_KEY", None)

# 엔드포인트 키 → 경로 매핑
# 키 이름은 character_service.py의 딕셔너리 참조 키와 동일합니다.
API_ENDPOINTS: dict[str, str] = {
    "get_character_id": "/id",
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
    "get_account_character_list": "/character/list",
}

# 요청 간 기본 대기 시간 (Rate Limit 방어)
REQUEST_DELAY_SECONDS: float = 0.05

# Rate Limit(429) 발생 시 재시도 대기 시간
RATE_LIMIT_RETRY_DELAY_SECONDS: int = 1
