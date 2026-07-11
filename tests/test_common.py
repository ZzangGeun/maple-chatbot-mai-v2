# tests/test_common.py
"""
common 패키지 테스트

공통 예외 클래스, API 응답 스키마, Nexon API 클라이언트 등
프로젝트 전반에서 공유되는 유틸리티를 테스트합니다.
"""

import pytest

from common.exceptions.base import AppException
from common.exceptions.chat import (
    AiServerUnavailable,
    InvalidSessionId,
    SessionNotFound,
)
from common.schemas.response import ApiResponse, ErrorDetail


# ---------------------------------------------------------------------------
# 커스텀 예외 테스트
# ---------------------------------------------------------------------------


class TestAppException:
    """프로젝트 기반 예외 클래스 테스트."""

    def test_default_values(self) -> None:
        """기본 인자로 생성 시 기본값이 설정되어야 합니다."""
        exc = AppException()
        assert exc.message == "요청을 처리할 수 없습니다."
        assert exc.code == "APP_ERROR"
        assert exc.status_code == 400

    def test_custom_values(self) -> None:
        """커스텀 인자가 정상 반영되어야 합니다."""
        exc = AppException(
            message="커스텀 에러",
            code="CUSTOM_CODE",
            status_code=500,
        )
        assert exc.message == "커스텀 에러"
        assert exc.code == "CUSTOM_CODE"
        assert exc.status_code == 500

    def test_to_dict(self) -> None:
        """to_dict()가 올바른 구조의 딕셔너리를 반환해야 합니다."""
        exc = AppException(message="테스트", code="TEST")
        result = exc.to_dict()
        assert result["success"] is False
        assert result["error"]["code"] == "TEST"
        assert result["error"]["message"] == "테스트"


class TestChatExceptions:
    """채팅 도메인 예외 클래스 테스트."""

    def test_session_not_found_with_id(self) -> None:
        """session_id가 포함된 에러 메시지를 생성해야 합니다."""
        exc = SessionNotFound("abc-123")
        assert "abc-123" in exc.message
        assert exc.status_code == 404
        assert exc.code == "SESSION_NOT_FOUND"

    def test_session_not_found_without_id(self) -> None:
        """session_id 없이도 기본 메시지가 생성되어야 합니다."""
        exc = SessionNotFound()
        assert "찾을 수 없습니다" in exc.message

    def test_invalid_session_id(self) -> None:
        """InvalidSessionId 예외가 올바른 속성을 가져야 합니다."""
        exc = InvalidSessionId()
        assert exc.status_code == 400
        assert exc.code == "INVALID_SESSION_ID"

    def test_ai_server_unavailable(self) -> None:
        """AiServerUnavailable 예외가 503 상태 코드를 가져야 합니다."""
        exc = AiServerUnavailable()
        assert exc.status_code == 503
        assert exc.code == "AI_SERVER_UNAVAILABLE"


# ---------------------------------------------------------------------------
# API 응답 스키마 테스트
# ---------------------------------------------------------------------------


class TestApiResponse:
    """통합 API 응답 스키마 테스트."""

    def test_ok_response(self) -> None:
        """성공 응답이 올바른 구조를 가져야 합니다."""
        resp = ApiResponse.ok(data={"key": "value"})
        assert resp.success is True
        assert resp.data == {"key": "value"}
        assert resp.error is None

    def test_ok_response_to_dict(self) -> None:
        """to_dict()가 올바른 딕셔너리를 반환해야 합니다."""
        result = ApiResponse.ok(data=["item1", "item2"]).to_dict()
        assert result["success"] is True
        assert result["data"] == ["item1", "item2"]
        assert "error" not in result

    def test_fail_response(self) -> None:
        """실패 응답이 올바른 구조를 가져야 합니다."""
        resp = ApiResponse.fail(
            message="잘못된 요청입니다",
            code="BAD_REQUEST",
        )
        assert resp.success is False
        assert resp.error is not None
        assert resp.error.code == "BAD_REQUEST"
        assert resp.error.message == "잘못된 요청입니다"

    def test_fail_response_to_dict(self) -> None:
        """실패 응답의 to_dict()가 error 필드를 포함해야 합니다."""
        result = ApiResponse.fail(message="에러", code="ERR").to_dict()
        assert result["success"] is False
        assert result["error"]["code"] == "ERR"
        assert result["error"]["message"] == "에러"

    def test_fail_default_values(self) -> None:
        """인자 없이 생성 시 기본 에러 메시지와 코드가 설정되어야 합니다."""
        resp = ApiResponse.fail()
        assert resp.error.code == "UNKNOWN_ERROR"
        assert resp.error.message == "요청을 처리할 수 없습니다."

    def test_ok_with_none_data(self) -> None:
        """data=None인 성공 응답도 정상 생성되어야 합니다."""
        resp = ApiResponse.ok(data=None)
        assert resp.success is True
        assert resp.data is None


class TestErrorDetail:
    """에러 상세 스키마 테스트."""

    def test_default_values(self) -> None:
        """기본값이 올바르게 설정되어야 합니다."""
        detail = ErrorDetail()
        assert detail.code == "UNKNOWN_ERROR"
        assert detail.message == ""

    def test_custom_values(self) -> None:
        """커스텀 값이 정상 반영되어야 합니다."""
        detail = ErrorDetail(code="CUSTOM", message="커스텀 메시지")
        assert detail.code == "CUSTOM"
        assert detail.message == "커스텀 메시지"
