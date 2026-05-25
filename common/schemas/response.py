# common/schemas/response.py
"""
통합 API 응답 스키마

모든 API 엔드포인트가 동일한 포맷으로 응답하도록
표준 응답 구조를 정의합니다.

사용 예:
    return JsonResponse(ApiResponse(data={"user": "foo"}).to_dict())
    return JsonResponse(ApiResponse.error("잘못된 요청", code="BAD_REQUEST").to_dict(), status=400)
"""

from typing import Any

from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """에러 상세 정보 스키마."""

    code: str = "UNKNOWN_ERROR"
    message: str = ""


class ApiResponse(BaseModel):
    """
    통합 API 응답 스키마.

    성공/실패 모두 이 포맷을 사용합니다:
        {
            "success": true/false,
            "data": ...,
            "error": {"code": "...", "message": "..."}  # 실패 시만
        }
    """

    success: bool = True
    data: Any = None
    error: ErrorDetail | None = None

    def to_dict(self) -> dict:
        """JsonResponse에 전달할 딕셔너리를 반환합니다."""
        result: dict[str, Any] = {
            "success": self.success,
            "data": self.data,
        }
        if self.error is not None:
            result["error"] = {
                "code": self.error.code,
                "message": self.error.message,
            }
        return result

    @classmethod
    def ok(cls, data: Any = None) -> "ApiResponse":
        """성공 응답을 간편하게 생성합니다."""
        return cls(success=True, data=data)

    @classmethod
    def fail(
        cls,
        message: str = "요청을 처리할 수 없습니다.",
        code: str = "UNKNOWN_ERROR",
    ) -> "ApiResponse":
        """실패 응답을 간편하게 생성합니다."""
        return cls(
            success=False,
            error=ErrorDetail(code=code, message=message),
        )
