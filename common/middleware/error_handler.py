# common/middleware/error_handler.py
"""
글로벌 에러 핸들러 미들웨어

AppException을 잡아 통일된 JSON 응답으로 변환합니다.
Django의 기본 예외 처리(404, 500 등)는 그대로 유지하면서,
비즈니스 로직에서 발생하는 AppException만 가로챕니다.
"""

import logging

from django.http import HttpRequest, HttpResponse, JsonResponse

from common.exceptions.base import AppException

logger = logging.getLogger(__name__)


class ErrorHandlerMiddleware:
    """
    AppException → JSON 변환 미들웨어.

    MIDDLEWARE 설정에 추가하여 사용합니다:
        "common.middleware.error_handler.ErrorHandlerMiddleware"

    반드시 다른 미들웨어보다 상위(리스트 앞쪽)에 위치시켜야
    하위 미들웨어/뷰에서 발생한 AppException을 모두 잡을 수 있습니다.
    """

    def __init__(self, get_response) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        return self.get_response(request)

    def process_exception(
        self, request: HttpRequest, exception: Exception
    ) -> JsonResponse | None:
        """
        뷰에서 발생한 예외를 가로챕니다.

        AppException이면 통일된 JSON 포맷으로 변환하고,
        그 외 예외는 Django 기본 처리에 맡깁니다.
        """
        if isinstance(exception, AppException):
            request_id = getattr(request, "request_id", "unknown")
            logger.warning(
                "[%s] AppException: %s (code=%s, status=%d)",
                request_id,
                exception.message,
                exception.code,
                exception.status_code,
            )
            return JsonResponse(
                exception.to_dict(),
                status=exception.status_code,
            )

        # AppException이 아닌 예외는 Django 기본 핸들러에 위임
        return None
