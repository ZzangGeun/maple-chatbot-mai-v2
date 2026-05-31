# accounts/urls.py
"""
accounts 앱 URL 설정

인증 관련 모든 API 엔드포인트를 직접 등록합니다.
중앙 urls.py에서 /api/v1/accounts/ prefix로 include됩니다.

    POST  /api/v1/accounts/signup/   — 회원가입
    POST  /api/v1/accounts/login/    — 로그인
    POST  /api/v1/accounts/logout/   — 로그아웃
    GET   /api/v1/accounts/user/     — 내 정보 조회
"""

from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path("signup/", views.signup, name="signup"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("user/", views.user_info, name="user_info"),
]
