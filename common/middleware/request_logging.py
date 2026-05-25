# common/middleware/request_logging.py
"""
요청 로깅 미들웨어

모든 HTTP 요청에 고유한 X-Request-ID를 부여하고,
요청/응답 정보를 구조화된 형태로 기록합니다.
LLM 프로젝트에서 디버깅 시 요청 추적에 필수적입니다.
"""

import logging
import time
import uuid

from django.http import HttpRequest, HttpResponse

logger = logging.getLogger("request")


class RequestLoggingMiddleware:
    """
    Django 미들웨어: 요청마다 X-Request-ID를 생성하고 로깅합니다.

    MIDDLEWARE 설정에 추가하여 사용합니다:
        "common.middleware.request_logging.RequestLoggingMiddleware"
    """

    def __init__(self, get_response) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        # 요청 ID 생성 (클라이언트가 보낸 값이 있으면 재사용)
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4())[:8])
        request.request_id = request_id

        start_time = time.time()

        # 요청 시작 로그
        logger.info(
            "[%s] %s %s (user=%s)",
            request_id,
            request.method,
            request.get_full_path(),
            getattr(request.user, "username", "anonymous"),
        )

        response = self.get_response(request)

        # 응답 완료 로그
        duration_ms = int((time.time() - start_time) * 1000)
        logger.info(
            "[%s] %s %s → %d (%dms)",
            request_id,
            request.method,
            request.get_full_path(),
            response.status_code,
            duration_ms,
        )

        # 응답 헤더에도 Request-ID를 포함하여 프론트에서 추적 가능하게 함
        response["X-Request-ID"] = request_id

        return response
