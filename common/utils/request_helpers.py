import json

from django.http import HttpRequest, JsonResponse
from django.http.request import RawPostDataException


def parse_json_body(
    request: HttpRequest,
) -> tuple[dict | None, JsonResponse | None]:
    """JSON 객체 요청을 파싱하고 실패 시 공통 400 응답을 반환합니다."""
    try:
        data = json.loads(request.body)
    except RawPostDataException:
        # multipart 요청은 CSRF 미들웨어가 본문을 먼저 읽어 다시 읽을 수 없습니다. (JSON 요청이 아님)
        return None, JsonResponse({"detail": "JSON 형식의 요청이 필요합니다."}, status=400)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None, JsonResponse({"detail": "잘못된 JSON 형식입니다."}, status=400)

    if not isinstance(data, dict):
        return None, JsonResponse(
            {"detail": "JSON 객체 형식의 요청이 필요합니다."},
            status=400,
        )

    return data, None
