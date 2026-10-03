# common/nexon/__init__.py
"""
넥슨 메이플스토리 Open API 공용 패키지

Django와 AI 서버가 함께 사용합니다.
  - client.py     : 비동기 API 클라이언트 (재시도, 오류 분류, Redis 캐시)
  - cache.py      : 응답 캐시 (Redis, 장애 시 캐시 없이 동작)
  - extractors.py : 캐릭터 검색 화면용 응답 정제 함수
  - constants.py  : 엔드포인트, 캐시 유효 기간, 오류 코드
"""

from common.nexon.cache import NexonCache
from common.nexon.client import CharacterFetchResult, NexonClient

__all__ = ["CharacterFetchResult", "NexonCache", "NexonClient"]
