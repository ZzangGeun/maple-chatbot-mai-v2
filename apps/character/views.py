# character/views.py
"""
캐릭터 정보 뷰 모듈 (표준 Django JsonResponse)

넥슨 API에서 캐릭터 정보를 조회하여 반환합니다.
실제 API 호출은 apps.character.nexon 패키지에 위임합니다.
"""

import logging

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from apps.character.nexon import get_character_data

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["GET"])
async def character_search(request) -> JsonResponse:
    """
    캐릭터 이름을 입력받아 넥슨 API에서 종합 캐릭터 정보를 조회합니다.

    GET /api/character/search/?name={캐릭터명}
    """
    try:
        character_name = request.GET.get("name", "").strip()

        if not character_name:
            return JsonResponse({"error": "캐릭터 이름을 입력해주세요.", "status": "error"}, status=400)

        logger.info(f"캐릭터 정보 조회 요청: {character_name}")

        character_info = await get_character_data(character_name)

        if not character_info:
            return JsonResponse(
                {"error": "캐릭터 정보를 찾을 수 없거나 가져오는 데 실패했습니다.", "status": "error"},
                status=404,
            )

        logger.info(f"캐릭터 정보 조회 성공: {character_name}")

        return JsonResponse(
            {"message": "캐릭터 정보 조회 성공", "data": character_info, "status": "success"},
            status=200,
        )

    except Exception as e:
        logger.error(f"캐릭터 정보 조회 오류: {e!s}")
        return JsonResponse({"error": "서버 오류가 발생했습니다.", "status": "error"}, status=500)
