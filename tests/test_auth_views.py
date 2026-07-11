# tests/test_auth_views.py
"""
auth 앱 뷰(엔드포인트) 통합 테스트

실제 HTTP 요청/응답 사이클을 Django 테스트 클라이언트로 시뮬레이션합니다.
넥슨 API 연동은 모킹 처리하여 네트워크 의존성을 제거합니다.
"""

import json

import pytest
from unittest.mock import AsyncMock, patch

from django.contrib.auth.models import User
from django.test import AsyncClient, Client

from apps.auth.models import UserProfile


@pytest.mark.django_db(transaction=True)
class TestSignupView:
    """POST /api/v1/auth/signup/ 엔드포인트 테스트."""

    SIGNUP_URL = "/api/v1/auth/signup/"

    def _make_signup_payload(self, **overrides) -> dict:
        """유효한 회원가입 요청 페이로드를 생성합니다."""
        payload = {
            "username": "signup_test01",
            "password": "securepass123",
            "confirm_password": "securepass123",
            "maple_nickname": "테스트캐릭",
            "nexon_api_key": "valid_api_key",
        }
        payload.update(overrides)
        return payload

    @pytest.mark.asyncio
    @patch(
        "apps.auth.services.process_signup_with_key",
        new_callable=AsyncMock,
        return_value=("테스트캐릭", {"character_level": 300}),
    )
    async def test_signup_success(self, mock_process: AsyncMock) -> None:
        """유효한 데이터로 회원가입 시 201 상태 코드를 반환해야 합니다."""
        client = AsyncClient()
        response = await client.post(
            self.SIGNUP_URL,
            data=json.dumps(self._make_signup_payload()),
            content_type="application/json",
        )
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "signup_test01"
        assert data["maple_nickname"] == "테스트캐릭"

        # DB에 실제로 생성되었는지 검증
        assert await User.objects.filter(username="signup_test01").aexists()

    @pytest.mark.asyncio
    async def test_signup_invalid_username_format(self) -> None:
        """아이디 형식이 잘못된 경우 400 에러를 반환해야 합니다."""
        client = AsyncClient()
        response = await client.post(
            self.SIGNUP_URL,
            data=json.dumps(self._make_signup_payload(username="ab")),
            content_type="application/json",
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_signup_password_mismatch(self) -> None:
        """비밀번호 불일치 시 400 에러를 반환해야 합니다."""
        client = AsyncClient()
        response = await client.post(
            self.SIGNUP_URL,
            data=json.dumps(
                self._make_signup_payload(confirm_password="different123")
            ),
            content_type="application/json",
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_signup_invalid_json_body(self) -> None:
        """잘못된 JSON 바디 전송 시 400 에러를 반환해야 합니다."""
        client = AsyncClient()
        response = await client.post(
            self.SIGNUP_URL,
            data="this is not json",
            content_type="application/json",
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_signup_get_method_not_allowed(self) -> None:
        """GET 요청은 405를 반환해야 합니다."""
        client = AsyncClient()
        response = await client.get(self.SIGNUP_URL)
        assert response.status_code == 405


@pytest.mark.django_db(transaction=True)
class TestLoginView:
    """POST /api/v1/auth/login/ 엔드포인트 테스트."""

    LOGIN_URL = "/api/v1/auth/login/"

    @pytest.fixture(autouse=True)
    def _setup_user(self, db) -> None:
        """테스트 전 사용자를 미리 생성합니다."""
        self.user = User.objects.create_user(
            username="login_test_user",
            password="correctpass123",
        )

    @pytest.mark.asyncio
    async def test_login_success(self) -> None:
        """올바른 자격증명으로 로그인 시 200을 반환해야 합니다."""
        client = AsyncClient()
        response = await client.post(
            self.LOGIN_URL,
            data=json.dumps(
                {"username": "login_test_user", "password": "correctpass123"}
            ),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.json()
        assert "환영합니다" in data["message"]
        assert data["user"]["username"] == "login_test_user"

    @pytest.mark.asyncio
    async def test_login_wrong_password(self) -> None:
        """잘못된 비밀번호로 로그인 시 401을 반환해야 합니다."""
        client = AsyncClient()
        response = await client.post(
            self.LOGIN_URL,
            data=json.dumps(
                {"username": "login_test_user", "password": "wrongpassword"}
            ),
            content_type="application/json",
        )
        assert response.status_code == 401
        data = response.json()
        assert "비밀번호가 일치하지 않습니다" in data["detail"]

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self) -> None:
        """존재하지 않는 아이디로 로그인 시 401을 반환해야 합니다."""
        client = AsyncClient()
        response = await client.post(
            self.LOGIN_URL,
            data=json.dumps(
                {"username": "ghost_user999", "password": "anypassword"}
            ),
            content_type="application/json",
        )
        assert response.status_code == 401
        data = response.json()
        assert "존재하지 않는 아이디" in data["detail"]

    @pytest.mark.asyncio
    async def test_login_missing_fields(self) -> None:
        """필수 필드가 누락된 경우 400 에러를 반환해야 합니다."""
        client = AsyncClient()
        response = await client.post(
            self.LOGIN_URL,
            data=json.dumps({"username": "login_test_user"}),
            content_type="application/json",
        )
        assert response.status_code == 400


@pytest.mark.django_db(transaction=True)
class TestLogoutView:
    """POST /api/v1/auth/logout/ 엔드포인트 테스트."""

    LOGOUT_URL = "/api/v1/auth/logout/"

    def test_logout_success(self, authenticated_client: Client) -> None:
        """로그인 상태에서 로그아웃 시 200을 반환해야 합니다."""
        response = authenticated_client.post(self.LOGOUT_URL)
        assert response.status_code == 200
        data = response.json()
        assert "로그아웃" in data["message"]

    def test_logout_without_login(self, api_client: Client) -> None:
        """로그인하지 않은 상태에서 로그아웃 시 401을 반환해야 합니다."""
        response = api_client.post(self.LOGOUT_URL)
        assert response.status_code == 401


@pytest.mark.django_db(transaction=True)
class TestUserInfoView:
    """GET /api/v1/auth/user/ 엔드포인트 테스트."""

    USER_INFO_URL = "/api/v1/auth/user/"

    def test_user_info_authenticated(self, authenticated_client: Client) -> None:
        """로그인 상태에서 사용자 정보를 정상 조회해야 합니다."""
        response = authenticated_client.get(self.USER_INFO_URL)
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "test_user01"

    def test_user_info_unauthenticated(self, api_client: Client) -> None:
        """로그인하지 않은 상태에서 401을 반환해야 합니다."""
        response = api_client.get(self.USER_INFO_URL)
        assert response.status_code == 401

    def test_user_info_with_profile(self, db) -> None:
        """UserProfile이 있는 사용자의 경우 maple_nickname이 포함되어야 합니다."""
        user = User.objects.create_user(
            username="profile_user01", password="testpass123"
        )
        UserProfile.objects.create(
            user=user,
            maple_nickname="프로필캐릭터",
            nexon_api_key="some_key",
        )
        client = Client()
        client.login(username="profile_user01", password="testpass123")
        response = client.get(self.USER_INFO_URL)
        assert response.status_code == 200
        data = response.json()
        assert data["profile"]["maple_nickname"] == "프로필캐릭터"
