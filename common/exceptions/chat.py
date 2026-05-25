# common/exceptions/chat.py
"""
채팅 도메인 관련 커스텀 예외

채팅 세션 관리 및 AI 서버 통신 시 발생할 수 있는 오류를 분류합니다.
"""

from common.exceptions.base import AppException


class SessionNotFound(AppException):
    """주어진 session_id에 해당하는 세션이 존재하지 않을 때."""

    def __init__(self, session_id: str = "") -> None:
        message = (
            f"세션 '{session_id}'을(를) 찾을 수 없습니다."
            if session_id
            else "세션을 찾을 수 없습니다."
        )
        super().__init__(
            message=message,
            code="SESSION_NOT_FOUND",
            status_code=404,
        )


class InvalidSessionId(AppException):
    """session_id 형식이 올바르지 않을 때 (UUID 파싱 실패)."""

    def __init__(self) -> None:
        super().__init__(
            message="유효하지 않은 세션 ID입니다.",
            code="INVALID_SESSION_ID",
            status_code=400,
        )


class AiServerUnavailable(AppException):
    """AI 서버(FastAPI)에 연결할 수 없을 때."""

    def __init__(self) -> None:
        super().__init__(
            message="AI 서버에 연결할 수 없습니다. 잠시 후 다시 시도해주세요.",
            code="AI_SERVER_UNAVAILABLE",
            status_code=503,
        )
