import json

from django.http import HttpRequest, JsonResponse


def parse_json_body(
    request: HttpRequest,
) -> tuple[dict | None, JsonResponse | None]:
    """JSON 객체 요청을 파싱하고 실패 시 공통 400 응답을 반환합니다."""
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None, JsonResponse({"detail": "잘못된 JSON 형식입니다."}, status=400)

    if not isinstance(data, dict):
        return None, JsonResponse(
            {"detail": "JSON 객체 형식의 요청이 필요합니다."},
            status=400,
        )

    return data, None
