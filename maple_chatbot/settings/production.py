"""
운영 환경 설정 (production.py)

서버 배포 시 사용합니다.
SECRET_KEY, ALLOWED_HOSTS 등 모든 민감한 값은 반드시 환경변수로 설정해야 합니다.

사용 방법:
    export DJANGO_SETTINGS_MODULE=maple_chatbot.settings.production
    또는 .env에 DJANGO_SETTINGS_MODULE=maple_chatbot.settings.production 추가
"""

from .base import *  # noqa: F401, F403

from decouple import config, Csv

# ─────────────────────────────────────────────
# 보안 (운영 환경: 반드시 환경변수에서 로드)
# ─────────────────────────────────────────────
SECRET_KEY = config("SECRET_KEY")  # default 없음 — 미설정 시 즉시 오류 발생
DEBUG = False
ALLOWED_HOSTS = config("ALLOWED_HOSTS", cast=Csv())  # 예: "example.com,www.example.com"

# ─────────────────────────────────────────────
# CORS (운영 환경: 명시적으로 허용된 출처만)
# ─────────────────────────────────────────────
CORS_ALLOW_ALL_ORIGINS = False  # 운영에서는 절대 True 금지
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = config(
    "CORS_ALLOWED_ORIGINS",
    cast=Csv(),
    default="",  # 미설정 시 빈 목록 → 모든 교차 출처 차단
)

# ─────────────────────────────────────────────
# 보안 헤더 (운영 환경 권장)
# ─────────────────────────────────────────────
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

# HTTPS 환경일 경우 아래 주석 해제
# SECURE_SSL_REDIRECT = True
# SESSION_COOKIE_SECURE = True
# CSRF_COOKIE_SECURE = True

# ─────────────────────────────────────────────
# 이메일 (운영: SMTP 서버 사용)
# ─────────────────────────────────────────────
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = config("EMAIL_HOST", default="")
EMAIL_PORT = config("EMAIL_PORT", default=587, cast=int)
EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = True
