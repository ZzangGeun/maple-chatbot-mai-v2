# core/urls.py
"""
core 앱 URL 설정

- serve_react: catch-all React SPA 라우팅 (중앙 urls.py에서 직접 참조)
- API 엔드포인트: /api/core/ prefix로 include

    GET /api/core/home/data/         — 홈 통합 데이터
    GET /api/core/notices/json/      — 공지사항 전체 (JSON 캐시)
    GET /api/core/notices/event/     — 이벤트 공지
    GET /api/core/notices/update/    — 업데이트 공지
    GET /api/core/notices/cashshop/  — 캐시샵 공지
    GET /api/core/ranking/json/      — 랭킹 전체 (JSON 캐시)
    GET /api/core/ranking/overall/   — 종합 랭킹
"""

from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    # 홈
    path("home/data/", views.home_data, name="home_data"),
    # 공지사항
    path("notices/json/", views.get_notices_json, name="notices_json"),
    path("notices/event/", views.get_event_notices, name="notices_event"),
    path("notices/update/", views.get_update_notices, name="notices_update"),
    path("notices/cashshop/", views.get_cashshop_notices, name="notices_cashshop"),
    # 랭킹
    path("ranking/json/", views.get_ranking_json, name="ranking_json"),
    path("ranking/overall/", views.get_overall_ranking, name="ranking_overall"),
]
