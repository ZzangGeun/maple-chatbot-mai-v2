# services/nexon/__init__.py
"""
Nexon 서비스 패키지 공개 API

외부 모듈은 이 파일에서 export하는 함수만 사용합니다.
내부 구조(client, extractors, constants)가 변경되어도
이 파일의 인터페이스는 유지되므로 외부 import가 깨지지 않습니다.
"""

from apps.character.nexon.character_service import get_character_data, process_signup_with_key

__all__ = [
    "get_character_data",
    "process_signup_with_key",
]
