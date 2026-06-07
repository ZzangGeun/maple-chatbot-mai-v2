import json
from django.http import HttpRequest, JsonResponse

def parse_json_body(request: HttpRequest) -> tuple[dict | None, JsonResponse | None]:
    """요청 바디의 JSON 파싱을 시도하고 실패 시 에러 응답을 반환하는 공통 유틸"""
    try:
        data = json.loads(request.body)
        return data, None
    except json.JSONDecodeError:
        return None, JsonResponse({"detail": "잘못된 JSON 형식입니다."}, status=400)
