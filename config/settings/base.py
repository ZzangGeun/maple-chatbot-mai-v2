"""
공통 Django 설정 (base.py)
개발(development.py)과 운영(production.py) 환경에서 공통으로 사용하는 설정값을 정의합니다.
"""

from pathlib import Path
from decouple import config

# 프로젝트 최상위 디렉토리 (MAP_Help_You/)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# ─────────────────────────────────────────────
# 앱 정의
# ─────────────────────────────────────────────
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

LOCAL_APPS = [
    "apps.core",
    "apps.accounts",
    "apps.character",
    "apps.chat",
]

THIRD_PARTY_APPS = [
    "corsheaders",
    "pgvector.django",
]

INSTALLED_APPS = DJANGO_APPS + LOCAL_APPS + THIRD_PARTY_APPS

# ─────────────────────────────────────────────
# 미들웨어
# ─────────────────────────────────────────────
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],  # 앱별 templates 폴더 사용
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.core.context_processors.ads_settings",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# ─────────────────────────────────────────────
# 데이터베이스 (모든 환경 공통: PostgreSQL)
# ─────────────────────────────────────────────
DATABASES = {
    "default": {
        "ENGINE": config("DB_ENGINE", default="django.db.backends.postgresql"),
        "NAME": config("DATABASE_NAME", default=config("DB_NAME", default="")),
        "USER": config("DATABASE_USER", default=config("DB_USER", default="")),
        "PASSWORD": config(
            "DATABASE_PASSWORD", default=config("DB_PASSWORD", default="")
        ),
        "HOST": config("DATABASE_HOST", default=config("DB_HOST", default="localhost")),
        "PORT": config("DATABASE_PORT", default=config("DB_PORT", default="5432")),
    }
}

# ─────────────────────────────────────────────
# 비밀번호 검증
# ─────────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ─────────────────────────────────────────────
# 국제화
# ─────────────────────────────────────────────
LANGUAGE_CODE = "ko-kr"
TIME_ZONE = "Asia/Seoul"
USE_I18N = True
USE_TZ = True

# ─────────────────────────────────────────────
# 정적 / 미디어 파일
# ─────────────────────────────────────────────
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ─────────────────────────────────────────────
# 외부 API 키 (.env에서 로드, 코드에 노출 금지)
# ─────────────────────────────────────────────
NEXON_API_KEY = config("NEXON_API_KEY", default="")
OPENAI_API_KEY = config("OPENAI_API_KEY", default="")

# AI 서버 설정 (LangGraph FastAPI 서버)
# .env에서 AI_SERVER_URL=http://your-server:8001 으로 오버라이드 가능
AI_SERVER_BASE_URL = config("AI_SERVER_URL", default="http://127.0.0.1:8001")

# ─────────────────────────────────────────────
# 광고 설정
# ─────────────────────────────────────────────
ADS_ENABLED = config("ADS_ENABLED", default=False, cast=bool)
ADS_PROVIDER = config("ADS_PROVIDER", default="mock")
ADSENSE_CLIENT = config("ADSENSE_CLIENT", default="")
ADS_SLOTS = {
    "leaderboard": config("ADS_SLOT_LEADERBOARD", default=""),
    "medium_rectangle": config("ADS_SLOT_MEDIUM_RECT", default=""),
    "skyscraper": config("ADS_SLOT_SKYSCRAPER", default=""),
}

# ─────────────────────────────────────────────
# CSRF
# ─────────────────────────────────────────────
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

# ─────────────────────────────────────────────
# 이메일
# ─────────────────────────────────────────────
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
