# auth/urls.py
"""
auth 앱 URL 설정

인증 관련 모든 API 엔드포인트를 직접 등록합니다.
중앙 urls.py에서 /api/v1/auth/ prefix로 include됩니다.

    POST  /api/v1/auth/signup/   — 회원가입
    POST  /api/v1/auth/login/    — 로그인
    POST  /api/v1/auth/logout/   — 로그아웃
    GET   /api/v1/auth/user/     — 내 정보 조회
"""

from django.urls import path
from . import views
from apps.character import views as char_views

app_name = "auth"

urlpatterns = [
    path("signup", views.signup, name="signup"),
    path("signup/", views.signup, name="signup_slash"),
    
    path("login", views.login_view, name="login"),
    path("login/", views.login_view, name="login_slash"),
    
    path("logout", views.logout_view, name="logout"),
    path("logout/", views.logout_view, name="logout_slash"),
    
    path("user/", views.user_info, name="user_info"), # 기존 엔드포인트 유지
    
    # 캐릭터 연동 관련 엔드포인트 연결 (auth-api.md 설계서 스펙)
    path("character/link", char_views.character_link, name="character_link"),
    path("character/verify", char_views.character_verify, name="character_verify"),
]

