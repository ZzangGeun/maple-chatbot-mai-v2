"""
운영 환경 설정 (production.py)

서버 배포 시 사용합니다. (docker-compose.prod.yml이 DJANGO_SETTINGS_MODULE로 지정)
SECRET_KEY, ALLOWED_HOSTS 등 모든 민감한 값은 반드시 환경변수로 설정해야 합니다.

전제: Django는 uvicorn(ASGI)으로 실행되고, 앞단의 리버스 프록시(Caddy)가 HTTPS를 처리한 뒤
X-Forwarded-Proto, X-Real-IP 헤더를 붙여 전달합니다.
"""

from .base import *  # noqa: F401, F403

from decouple import config, Csv

# ─────────────────────────────────────────────
# 기본 보안
# ─────────────────────────────────────────────
SECRET_KEY = config("SECRET_KEY")  # default 없음 — 미설정 시 즉시 오류 발생
DEBUG = False
# 컨테이너 헬스체크는 내부에서 localhost로 접속하므로 함께 허용합니다.
ALLOWED_HOSTS = config("ALLOWED_HOSTS", cast=Csv()) + ["localhost", "127.0.0.1"]

# 서비스 주소(https://도메인). 로그인·채팅 등 POST 요청의 CSRF 출처 검사에 사용합니다.
CSRF_TRUSTED_ORIGINS = config("CSRF_TRUSTED_ORIGINS", cast=Csv(), default="")

# ─────────────────────────────────────────────
# HTTPS (리버스 프록시 뒤)
# ─────────────────────────────────────────────
# 프록시가 HTTPS로 받은 요청임을 X-Forwarded-Proto로 알려 줍니다.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
# http → https 리다이렉트는 프록시가 담당합니다. (내부 헬스체크가 리다이렉트되지 않도록 기본 False)
SECURE_SSL_REDIRECT = config("SECURE_SSL_REDIRECT", default=False, cast=bool)
SESSION_COOKIE_SECURE = config("SESSION_COOKIE_SECURE", default=True, cast=bool)
CSRF_COOKIE_SECURE = config("CSRF_COOKIE_SECURE", default=True, cast=bool)
# HSTS는 HTTPS가 정상 동작하는 것을 확인한 뒤 켭니다. (예: 31536000 = 1년)
SECURE_HSTS_SECONDS = config("SECURE_HSTS_SECONDS", default=0, cast=int)
SECURE_HSTS_INCLUDE_SUBDOMAINS = SECURE_HSTS_SECONDS > 0

SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"

# 요청 횟수 제한에서 프록시가 넣은 X-Real-IP를 클라이언트 IP로 사용합니다.
TRUST_X_REAL_IP = config("TRUST_X_REAL_IP", default=True, cast=bool)

# ─────────────────────────────────────────────
# CORS (프론트엔드를 같은 도메인에서 서빙하므로 기본적으로 교차 출처를 허용하지 않습니다)
# ─────────────────────────────────────────────
CORS_ALLOW_ALL_ORIGINS = False  # 운영에서는 절대 True 금지
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = config("CORS_ALLOWED_ORIGINS", cast=Csv(), default="")

# ─────────────────────────────────────────────
# 캐시: Redis (여러 워커가 캐릭터 정보 캐시·요청 제한 카운터를 공유)
# ─────────────────────────────────────────────
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": REDIS_URL,  # noqa: F405
    }
}

# ─────────────────────────────────────────────
# 정적 파일: WhiteNoise가 collectstatic 결과(STATIC_ROOT)를 직접 서빙합니다.
# URL 라우팅보다 먼저 처리되므로 React catch-all 라우트가 /static/ 요청을 가로채지 않습니다.
# 프론트엔드 빌드 파일은 Vite가 이미 해시를 붙이므로 압축만 적용합니다.
# ─────────────────────────────────────────────
MIDDLEWARE = list(MIDDLEWARE)  # noqa: F405
MIDDLEWARE.insert(
    MIDDLEWARE.index("django.middleware.security.SecurityMiddleware") + 1,
    "whitenoise.middleware.WhiteNoiseMiddleware",
)
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
}

# ─────────────────────────────────────────────
# 로깅: 컨테이너 표준 출력으로 남깁니다. (docker logs로 확인)
# ─────────────────────────────────────────────
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"plain": {"format": "%(asctime)s %(levelname)s %(name)s: %(message)s"}},
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "plain"}},
    "root": {"handlers": ["console"], "level": config("LOG_LEVEL", default="INFO")},
}

# ─────────────────────────────────────────────
# 이메일 (운영: SMTP 서버 사용)
# ─────────────────────────────────────────────
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = config("EMAIL_HOST", default="")
EMAIL_PORT = config("EMAIL_PORT", default=587, cast=int)
EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = True
