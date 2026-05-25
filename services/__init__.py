# 외부 서비스 연동 패키지
#
# 구조:
#   services/
#   ├── nexon/
#   │   ├── constants.py        — API 엔드포인트, 상수
#   │   ├── client.py           — aiohttp HTTP 클라이언트
#   │   ├── extractors.py       — 순수 데이터 변환 함수
#   │   └── character_service.py — 캐시+API+추출 오케스트레이터
#   └── shared/
#       └── config.py           — AI 서버(FastAPI), DB, RAG 공통 설정값
