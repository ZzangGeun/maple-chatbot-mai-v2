"""
개발 환경 설정 (development.py)

로컬 개발 시 사용합니다.
모든 출처의 CORS를 허용하고, DEBUG=True로 설정합니다.

사용 방법:
    export DJANGO_SETTINGS_MODULE=config.settings.development
    또는 .env에 DJANGO_SETTINGS_MODULE=config.settings.development 추가
"""

from .base import *  # noqa: F401, F403 — 공통 설정 전체 상속

from decouple import config

# ─────────────────────────────────────────────
# 보안 (개발 환경: 공개 키 허용)
# ─────────────────────────────────────────────
SECRET_KEY = config("SECRET_KEY", default="django-insecure-dev-key-change-me")
DEBUG = True
ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

# ─────────────────────────────────────────────
# CORS (개발 환경: 모든 출처 허용)
# 운영 환경에서는 절대 사용 금지
# ─────────────────────────────────────────────
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# ─────────────────────────────────────────────
# 디버그용 이메일 백엔드 (콘솔 출력)
# ─────────────────────────────────────────────
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# ─────────────────────────────────────────────
# 개발 전용 추가 앱 (필요 시 주석 해제)
# ─────────────────────────────────────────────
# INSTALLED_APPS += ["debug_toolbar"]
