# common/exceptions/nexon.py
"""
Nexon API 관련 커스텀 예외

Nexon Open API 호출 시 발생할 수 있는 오류를 구체적으로 분류합니다.
"""

from common.exceptions.base import AppException


class NexonApiError(AppException):
    """Nexon API 호출 중 일반적인 오류가 발생했을 때."""

    def __init__(
        self,
        message: str = "넥슨 API 요청 중 오류가 발생했습니다.",
        status_code: int = 502,
    ) -> None:
        super().__init__(
            message=message,
            code="NEXON_API_ERROR",
            status_code=status_code,
        )


class CharacterNotFound(AppException):
    """캐릭터 이름으로 조회했으나 결과가 없을 때."""

    def __init__(self, character_name: str = "") -> None:
        message = (
            f"캐릭터 '{character_name}'을(를) 찾을 수 없습니다."
            if character_name
            else "캐릭터를 찾을 수 없습니다."
        )
        super().__init__(
            message=message,
            code="CHARACTER_NOT_FOUND",
            status_code=404,
        )


class ApiRateLimitExceeded(AppException):
    """Nexon API 429 Too Many Requests 응답을 받았을 때."""

    def __init__(self) -> None:
        super().__init__(
            message="API 호출 횟수 제한을 초과했습니다. 잠시 후 다시 시도해주세요.",
            code="API_RATE_LIMIT_EXCEEDED",
            status_code=429,
        )
