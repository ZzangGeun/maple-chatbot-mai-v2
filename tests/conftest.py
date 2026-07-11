# tests/conftest.py
"""
pytest 전역 설정 및 공용 Fixture

모든 테스트에서 공통으로 필요한 Django 설정, 사용자 생성,
인증 클라이언트 등을 Fixture로 제공합니다.
"""

import os

import django
from django.conf import settings

# Django 테스트 시 기본 설정 모듈 지정 (pytest.ini 없이도 동작하도록)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")


import pytest
from django.contrib.auth.models import User
from django.test import AsyncClient, Client

from apps.auth.models import UserProfile


# ---------------------------------------------------------------------------
# 사용자 관련 Fixture
# ---------------------------------------------------------------------------


@pytest.fixture
def test_password() -> str:
    """테스트에 사용할 기본 비밀번호."""
    return "securepassword123"


@pytest.fixture
def create_user(db, test_password) -> User:
    """기본 테스트 사용자를 생성합니다.

    Django의 create_user를 사용하므로 비밀번호는 자동 해싱됩니다.
    """
    user = User.objects.create_user(
        username="test_user01",
        password=test_password,
    )
    return user


@pytest.fixture
def create_user_with_profile(db, create_user) -> tuple[User, UserProfile]:
    """UserProfile까지 연결된 테스트 사용자를 생성합니다."""
    profile = UserProfile.objects.create(
        user=create_user,
        maple_nickname="테스트캐릭터",
        nexon_api_key="test_api_key_12345",
    )
    return create_user, profile


@pytest.fixture
def api_client() -> Client:
    """Django 동기 테스트 클라이언트."""
    return Client()


@pytest.fixture
def async_api_client() -> AsyncClient:
    """Django 비동기 테스트 클라이언트."""
    return AsyncClient()


@pytest.fixture
def authenticated_client(api_client, create_user, test_password) -> Client:
    """로그인이 완료된 상태의 테스트 클라이언트.

    세션 인증이 필요한 엔드포인트 테스트에 사용합니다.
    """
    api_client.login(username=create_user.username, password=test_password)
    return api_client


@pytest.fixture
def authenticated_async_client(
    async_api_client, create_user, test_password
) -> AsyncClient:
    """로그인이 완료된 비동기 테스트 클라이언트."""
    # AsyncClient는 login을 동기적으로 호출 가능
    async_api_client.login(username=create_user.username, password=test_password)  # type: ignore[arg-type]
    return async_api_client
