# common/exceptions/base.py
"""
프로젝트 공통 예외 기반 클래스

모든 커스텀 예외는 AppException을 상속받아야 합니다.
글로벌 에러 핸들러(common.middleware.error_handler)가 AppException을
잡아 통일된 JSON 응답으로 변환합니다.
"""


class AppException(Exception):
    """
    프로젝트 공통 예외 기반 클래스.

    Args:
        message: 사용자에게 보여줄 에러 메시지.
        code: 에러 식별 코드 (예: "CHARACTER_NOT_FOUND").
        status_code: HTTP 상태 코드 (기본 400).
    """

    def __init__(
        self,
        message: str = "요청을 처리할 수 없습니다.",
        code: str = "APP_ERROR",
        status_code: int = 400,
    ) -> None:
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(self.message)

    def to_dict(self) -> dict:
        """JSON 직렬화용 딕셔너리를 반환합니다."""
        return {
            "success": False,
            "error": {
                "code": self.code,
                "message": self.message,
            },
        }
