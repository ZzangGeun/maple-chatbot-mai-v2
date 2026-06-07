"""
테스트 전용 Django 설정 (test.py)

개발 설정을 상속하되, 테스트 DB를 SQLite in-memory로 교체합니다.
PostgreSQL의 기존 마이그레이션 충돌과 무관하게 테스트를 실행할 수 있습니다.

사용 방법:
    pytest --ds=config.settings.test
"""

from .development import *  # noqa: F401, F403

import os

# Django의 AuthenticationMiddleware가 비동기 뷰에서 User 조회 시
# 동기 ORM 호출을 하여 SynchronousOnlyOperation이 발생합니다.
# 테스트 환경에서만 이 제한을 해제합니다.
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

# ─────────────────────────────────────────────
# 테스트 DB: SQLite in-memory (빠르고 독립적)
# ─────────────────────────────────────────────
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# ─────────────────────────────────────────────
# 테스트 성능 최적화
# ─────────────────────────────────────────────
# 비밀번호 해싱 비용을 줄여 테스트 속도를 높입니다.
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# pgvector 관련 마이그레이션 오류 방지를 위해 THIRD_PARTY_APPS에서 제거
INSTALLED_APPS = [
    app for app in INSTALLED_APPS if app != "pgvector.django"  # noqa: F405
]

# Redis 캐시 비활성화 (테스트 시 Redis 의존 제거)
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

# ─────────────────────────────────────────────
# 세션 백엔드: 캐시 기반 (비동기 호환)
# ─────────────────────────────────────────────
# 왜 변경하는가: 기본 DB 세션 백엔드는 비동기 뷰 테스트에서
# SynchronousOnlyOperation 에러를 발생시킵니다.
# 캐시 기반 백엔드는 DB 접근 없이 세션을 관리하므로 이 문제가 없습니다.
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
