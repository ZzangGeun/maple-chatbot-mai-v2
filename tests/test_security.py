# tests/test_security.py
"""
운영 보안 동작 테스트

- 채팅 세션 소유권 (다른 사람의 대화를 읽거나 지울 수 없음)
- CSRF 검사와 CSRF 쿠키 발급
- 메시지 전송 횟수·길이 제한
- AI 서버 내부 호출 토큰·관리자 토큰, 헬스체크
"""

import httpx
import pytest
from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import AsyncClient, override_settings
from fastapi import FastAPI
from unittest.mock import AsyncMock, MagicMock, patch

from ai_server.api.router import api_router
from ai_server.config import settings as ai_settings
from apps.chat.models import ChatMessage, ChatSession
from common import ratelimit

ROOMS_URL = "/api/v1/chat/rooms/"


def _messages_url(session) -> str:
    return f"/api/v1/chat/rooms/{session.session_id}/messages/"


async def _login(username: str) -> AsyncClient:
    client = AsyncClient()
    await client.alogin(username=username, password="password123")
    return client


@pytest.fixture(autouse=True)
def _clear_cache():
    cache.clear()
    yield
    cache.clear()


# ---------------------------------------------------------------------------
# 세션 소유권
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
class TestSessionOwnership:
    @pytest.fixture(autouse=True)
    def _setup(self, db) -> None:
        self.owner = User.objects.create_user(username="owner_user", password="password123")
        User.objects.create_user(username="other_user", password="password123")
        self.session = ChatSession.objects.create(user=self.owner)
        ChatMessage.objects.create(session=self.session, role="user", content="비밀 대화")

    @pytest.mark.asyncio
    async def test_owner_can_read(self) -> None:
        response = await (await _login("owner_user")).get(_messages_url(self.session))
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_other_user_and_anonymous_cannot_read_or_delete(self) -> None:
        other = await _login("other_user")
        for client in (other, AsyncClient()):
            assert (await client.get(_messages_url(self.session))).status_code == 404
            delete = await client.delete(f"/api/v1/chat/rooms/{self.session.session_id}/")
            assert delete.status_code == 404
        assert await ChatSession.objects.filter(pk=self.session.pk).aexists()

    @pytest.mark.asyncio
    async def test_anonymous_session_belongs_to_creating_browser(self) -> None:
        creator = AsyncClient()
        created = await creator.post(ROOMS_URL)
        session = await ChatSession.objects.aget(pk=created.json()["room"]["id"])

        assert session.user_id is None and session.owner_key
        assert (await creator.get(_messages_url(session))).status_code == 200
        assert (await AsyncClient().get(_messages_url(session))).status_code == 404


# ---------------------------------------------------------------------------
# CSRF
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
class TestCsrf:
    @pytest.mark.asyncio
    async def test_post_without_token_is_rejected(self) -> None:
        client = AsyncClient(enforce_csrf_checks=True)
        assert (await client.post(ROOMS_URL)).status_code == 403

    @pytest.mark.asyncio
    async def test_user_info_issues_cookie_that_allows_post(self) -> None:
        client = AsyncClient(enforce_csrf_checks=True)

        # 프론트가 앱을 열 때 부르는 API입니다. 비로그인(401)이어도 쿠키를 발급해야 합니다.
        info = await client.get("/api/v1/auth/user/")
        assert info.status_code == 401
        token = client.cookies["csrftoken"].value

        # 프론트(axios)처럼 JSON으로 보냅니다.
        response = await client.post(
            ROOMS_URL, data={}, content_type="application/json", headers={"X-CSRFToken": token}
        )
        assert response.status_code == 201


# ---------------------------------------------------------------------------
# 요청 횟수·길이 제한
# ---------------------------------------------------------------------------


def test_parse_rate_limits() -> None:
    assert ratelimit.parse_rate_limits("20/m, 300/d") == [
        ratelimit.RateLimit(20, 60),
        ratelimit.RateLimit(300, 86400),
    ]
    assert ratelimit.parse_rate_limits("") == []


@pytest.mark.asyncio
async def test_rate_limit_counts_per_identity() -> None:
    limits = [ratelimit.RateLimit(2, 60)]
    assert await ratelimit.ahit("test", "a", limits)
    assert await ratelimit.ahit("test", "a", limits)
    assert not await ratelimit.ahit("test", "a", limits)
    # 다른 사용자(IP)는 따로 셉니다.
    assert await ratelimit.ahit("test", "b", limits)


def test_client_ip_uses_proxy_header_only_when_trusted() -> None:
    request = MagicMock(META={"REMOTE_ADDR": "10.0.0.2", "HTTP_X_REAL_IP": "1.2.3.4"})
    with override_settings(TRUST_X_REAL_IP=False):
        assert ratelimit.client_ip(request) == "10.0.0.2"
    with override_settings(TRUST_X_REAL_IP=True):
        assert ratelimit.client_ip(request) == "1.2.3.4"


@pytest.mark.django_db(transaction=True)
class TestMessageLimits:
    @pytest.fixture(autouse=True)
    def _setup(self, db) -> None:
        User.objects.create_user(username="limit_user", password="password123")

    @pytest.mark.asyncio
    @override_settings(CHAT_RATE_LIMIT_ANON="2/m")
    @patch("apps.chat.views.send_message_async", new_callable=AsyncMock)
    async def test_anonymous_rate_limit(self, mock_send: AsyncMock) -> None:
        message = MagicMock(id=1, content="답변")
        message.created_at.isoformat.return_value = "2026-10-04T00:00:00+09:00"
        mock_send.return_value = (message, message, {})
        client = AsyncClient()
        session_id = (await client.post(ROOMS_URL)).json()["room"]["id"]
        url = f"/api/v1/chat/rooms/{session_id}/messages/"

        statuses = [
            (await client.post(url, data={"message_content": "질문"}, content_type="application/json")).status_code
            for _ in range(3)
        ]

        assert statuses == [200, 200, 429]
        assert mock_send.await_count == 2

    @pytest.mark.asyncio
    @override_settings(CHAT_MESSAGE_MAX_CHARS=10)
    async def test_too_long_message_is_rejected_before_ai_call(self) -> None:
        client = await _login("limit_user")
        session_id = (await client.post(ROOMS_URL)).json()["room"]["id"]

        response = await client.post(
            f"/api/v1/chat/rooms/{session_id}/stream/",
            data={"content": "가" * 11},
            content_type="application/json",
        )

        assert response.status_code == 400
        assert response.json()["error_code"] == "MESSAGE_TOO_LONG"


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_django_health() -> None:
    response = await AsyncClient().get("/api/v1/core/health/")
    assert response.status_code == 200 and response.json() == {"status": "ok"}


# ---------------------------------------------------------------------------
# AI 서버 내부 토큰·관리자 토큰·헬스체크
# ---------------------------------------------------------------------------


def _ai_app(with_graph: bool = False) -> FastAPI:
    app = FastAPI()
    app.include_router(api_router)
    app.state.graph = MagicMock() if with_graph else None
    return app


async def _ai_request(app: FastAPI, method: str, path: str, **kwargs) -> httpx.Response:
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        return await client.request(method, path, **kwargs)


BODY = {"session_id": "s", "message": "안녕"}


@pytest.mark.asyncio
async def test_internal_token_is_required_when_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ai_settings, "ai_server_token", "secret-token")
    app = _ai_app()

    missing = await _ai_request(app, "POST", "/generate", json=BODY)
    wrong = await _ai_request(app, "POST", "/generate", json=BODY, headers={"X-Internal-Token": "x"})
    # 토큰이 맞으면 인증을 통과하고, 그래프가 없어 503이 납니다.
    right = await _ai_request(app, "POST", "/generate", json=BODY, headers={"X-Internal-Token": "secret-token"})

    assert (missing.status_code, wrong.status_code, right.status_code) == (401, 401, 503)


@pytest.mark.asyncio
async def test_internal_token_is_optional_in_local_dev(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ai_settings, "ai_server_token", "")

    response = await _ai_request(_ai_app(), "POST", "/generate", json=BODY)

    assert response.status_code == 503  # 인증은 통과, 그래프 없음


@pytest.mark.asyncio
async def test_admin_api_requires_matching_admin_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ai_settings, "ai_server_token", "")
    monkeypatch.setattr("ai_server.rag.ingest.run_scheduled_ingestion", AsyncMock())
    app = _ai_app()
    path = "/api/v1/ai/embed/sync"

    monkeypatch.setattr(ai_settings, "admin_token", "")
    not_configured = await _ai_request(app, "POST", path, headers={"Authorization": "Bearer anything"})

    monkeypatch.setattr(ai_settings, "admin_token", "admin-secret")
    wrong = await _ai_request(app, "POST", path, headers={"Authorization": "Bearer nope"})
    right = await _ai_request(app, "POST", path, headers={"Authorization": "Bearer admin-secret"})

    assert (not_configured.status_code, wrong.status_code, right.status_code) == (401, 401, 200)


@pytest.mark.asyncio
async def test_ai_health_reports_graph_readiness(monkeypatch: pytest.MonkeyPatch) -> None:
    # 헬스체크는 내부 토큰 없이도 호출할 수 있어야 합니다.
    monkeypatch.setattr(ai_settings, "ai_server_token", "secret-token")

    assert (await _ai_request(_ai_app(with_graph=False), "GET", "/health")).status_code == 503
    assert (await _ai_request(_ai_app(with_graph=True), "GET", "/health")).json() == {"status": "ok"}
