# config/urls.py
"""
프로젝트 중앙 URL 설정

각 앱의 urls.py가 API 엔드포인트를 직접 관리합니다.

API 경로 구조:
    /api/v1/accounts/  ← apps.accounts.urls
    /api/v1/chat/      ← apps.chat.urls
    /api/v1/character/ ← apps.character.urls
    /api/v1/core/      ← apps.core.urls
"""

from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from apps.core.views import serve_react

urlpatterns = [
    # Django 관리자 페이지
    path("admin/", admin.site.urls),

    # API 엔드포인트 (앱별 urls.py로 위임)
    # 향후 API 버전 관리(v2 등) 및 체계적인 경로 관리를 위해 기본 prefix를 /api/v1/으로 지정합니다.
    path("api/v1/auth/", include("apps.accounts.urls")),
    path("api/v1/chat/", include("apps.chat.urls")),
    path("api/v1/character/", include("apps.character.urls")),

    path("api/v1/core/", include("apps.core.urls")),

    # React SPA Catch-all (클라이언트 사이드 라우팅 지원)
    # API 경로 이후에 위치해야 API 요청이 올바르게 처리됩니다.
    re_path(r"^.*$", serve_react, name="react_app"),
]

# 개발 환경에서 미디어/정적 파일 서빙
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
