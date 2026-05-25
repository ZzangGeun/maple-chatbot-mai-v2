# maple_chatbot/urls.py
"""
프로젝트 중앙 URL 설정

Django Ninja를 제거하고 표준 Django URL 패턴으로 통합합니다.
각 앱의 urls.py가 API 엔드포인트를 직접 관리합니다.

API 경로 구조:
    /api/accounts/  ← accounts/urls.py
    /api/chat/      ← chat/urls.py
    /api/character/ ← character/urls.py
    /api/core/      ← core/urls.py
"""

from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from core.views import serve_react

urlpatterns = [
    # Django 관리자 페이지
    path("admin/", admin.site.urls),

    # API 엔드포인트 (앱별 urls.py로 위임)
    path("api/accounts/", include("accounts.urls")),
    path("api/chat/", include("chat.urls")),
    path("api/character/", include("character.urls")),
    path("api/core/", include("core.urls")),

    # React SPA Catch-all (클라이언트 사이드 라우팅 지원)
    # API 경로 이후에 위치해야 API 요청이 올바르게 처리됩니다.
    re_path(r"^.*$", serve_react, name="react_app"),
]

# 개발 환경에서 미디어/정적 파일 서빙
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
