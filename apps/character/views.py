# character/views.py
"""캐릭터 정보 뷰 모듈 (표준 Django JsonResponse)

넥슨 API에서 캐릭터 정보를 조회하여 반환합니다.
실제 API 호출 및 비즈니스 검증 처리는 서비스 레이어(services.py)와 nexon 패키지에 위임합니다.
"""

import logging
import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from apps.character.nexon import get_character_data
from apps.character.services import generate_verification_code, verify_and_link_character


from common.schemas.response import ApiResponse

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["GET"])
async def character_search(request) -> JsonResponse:
    """
    캐릭터 이름을 입력받아 넥슨 API에서 종합 캐릭터 정보를 조회합니다.

    GET /api/v1/character/search/?name={캐릭터명}
    """
    try:
        character_name = request.GET.get("name", "").strip()

        if not character_name:
            return JsonResponse(
                ApiResponse.fail("캐릭터 이름을 입력해주세요.", code="NAME_REQUIRED").to_dict(),
                status=400,
            )

        logger.info(f"캐릭터 정보 조회 요청: {character_name}")

        character_info = await get_character_data(character_name)

        if not character_info:
            return JsonResponse(
                ApiResponse.fail("캐릭터 정보를 찾을 수 없거나 가져오는 데 실패했습니다.", code="CHARACTER_NOT_FOUND").to_dict(),
                status=404,
            )

        logger.info(f"캐릭터 정보 조회 성공: {character_name}")

        # 공통 성공 스키마(success: True, data: character_info) 반환
        return JsonResponse(
            ApiResponse.ok(data=character_info).to_dict(),
            status=200,
        )

    except Exception as e:
        logger.error(f"캐릭터 정보 조회 오류: {e!s}")
        return JsonResponse(
            ApiResponse.fail("서버 오류가 발생했습니다.", code="SERVER_ERROR").to_dict(),
            status=500,
        )


@csrf_exempt
@require_http_methods(["POST"])
async def character_link(request) -> JsonResponse:
    """메이플스토리 캐릭터 연동 신청 API.

    POST /api/v1/auth/character/link
    """
    if not request.user.is_authenticated:
        return JsonResponse(
            {"success": False, "error_code": "UNAUTHORIZED", "message": "로그인이 필요한 서비스입니다."},
            status=401,
        )

    try:
        body = json.loads(request.body)
        character_name = body.get("character_name", "").strip()
    except (json.JSONDecodeError, ValueError):
        return JsonResponse(
            {"success": False, "error_code": "INVALID_BODY", "message": "요청 형식이 올바르지 않습니다."},
            status=400,
        )

    if not character_name:
        return JsonResponse(
            {"success": False, "error_code": "NAME_REQUIRED", "message": "캐릭터명을 입력해주세요."},
            status=400,
        )

    # 비즈니스 서비스 호출: 1회성 6자리 인증 코드 발급
    verification_code = generate_verification_code(request.session, character_name)

    return JsonResponse(
        {
            "success": True,
            "verification_code": verification_code,
            "message": "캐릭터 인증 코드 발급 완료. 인게임 캐릭터 소개글에 위 인증 코드를 삽입한 후 /verify 엔드포인트를 호출하세요.",
        },
        status=200,
    )


@csrf_exempt
@require_http_methods(["POST"])
async def character_verify(request) -> JsonResponse:
    """메이플스토리 캐릭터 인증 완료 API.

    POST /api/v1/auth/character/verify
    """
    if not request.user.is_authenticated:
        return JsonResponse(
            {"success": False, "error_code": "UNAUTHORIZED", "message": "로그인이 필요한 서비스입니다."},
            status=401,
        )

    try:
        body = json.loads(request.body)
        character_name = body.get("character_name", "").strip()
        verification_code = body.get("verification_code", "").strip()
    except (json.JSONDecodeError, ValueError):
        return JsonResponse(
            {"success": False, "error_code": "INVALID_BODY", "message": "요청 형식이 올바르지 않습니다."},
            status=400,
        )

    if not character_name or not verification_code:
        return JsonResponse(
            {"success": False, "error_code": "FIELDS_REQUIRED", "message": "캐릭터명과 인증 코드를 모두 입력해주세요."},
            status=400,
        )

    # 비즈니스 서비스 호출: 세션 검증 + 넥슨 API 인증 대조 + DB 연동 생성/갱신
    success, error_code, character_info = await verify_and_link_character(
        user=request.user,
        session=request.session,
        character_name=character_name,
        verification_code=verification_code,
    )

    if not success:
        error_messages = {
            "VERIFICATION_FAILED": "인증 코드가 만료되었거나 일치하지 않습니다.",
            "CHARACTER_NOT_FOUND": "해당 캐릭터를 찾을 수 없습니다.",
            "CODE_MISMATCH": "인게임 소개글에서 인증 코드를 확인할 수 없거나 일치하지 않습니다.",
            "API_COMMUNICATION_ERROR": "넥슨 API 서버 통신 중 오류가 발생했습니다.",
            "SERVER_ERROR": "서버 내부 오류가 발생했습니다.",
        }
        status_codes = {
            "VERIFICATION_FAILED": 400,
            "CHARACTER_NOT_FOUND": 404,
            "CODE_MISMATCH": 400,
            "API_COMMUNICATION_ERROR": 502,
            "SERVER_ERROR": 500,
        }
        message = error_messages.get(error_code, "본인 인증에 실패했습니다.")
        status_code = status_codes.get(error_code, 400)
        
        return JsonResponse(
            {"success": False, "error_code": error_code, "message": message},
            status=status_code,
        )

    return JsonResponse(
        {
            "success": True,
            "message": "캐릭터 본인 인증이 성공적으로 완료되었습니다.",
            "character": character_info,
        },
        status=200,
    )


