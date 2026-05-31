# character/views.py
"""
캐릭터 정보 뷰 모듈 (표준 Django JsonResponse)

넥슨 API에서 캐릭터 정보를 조회하여 반환합니다.
실제 API 호출은 apps.character.nexon 패키지에 위임합니다.
"""

import logging
import json
import random
import os

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings

from apps.character.nexon import get_character_data

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


@csrf_exempt
@require_http_methods(["POST"])
async def character_link(request) -> JsonResponse:
    """
    메이플스토리 캐릭터 연동 신청 API.

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

    # 1회성 6자리 인증 코드 생성 (예: MAI-1234)
    rand_num = random.randint(1000, 9999)
    verification_code = f"MAI-{rand_num}"

    # 세션에 임시 보관 (캐릭터명과 인증 코드를 대조 검증하기 위함)
    request.session[f"verify_code_{character_name}"] = verification_code
    request.session.modified = True

    logger.info(f"캐릭터 연동 코드 발급 완료: {character_name} -> {verification_code}")

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
    """
    메이플스토리 캐릭터 인증 완료 API.

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

    # 세션에 기록된 임시 인증 코드 비교
    cached_code = request.session.get(f"verify_code_{character_name}")
    if not cached_code or cached_code != verification_code:
        return JsonResponse(
            {"success": False, "error_code": "VERIFICATION_FAILED", "message": "인증 코드가 만료되었거나 일치하지 않습니다."},
            status=400,
        )

    # 넥슨 API 통신 환경 확인
    nexon_api_key = os.getenv("NEXON_API_KEY", "")
    
    # 디버깅 환경이거나 API Key가 비어있는 경우 Mock 성공 처리 (개발 편의성 목적)
    if settings.DEBUG and not nexon_api_key:
        logger.warning("NEXON_API_KEY가 존재하지 않아 개발 디버깅 모드로 자동 인증 성공 처리합니다.")
        
        # 가상의 데이터로 저장
        from apps.character.models import CharacterLink
        from django.utils import timezone
        
        is_first = not await CharacterLink.objects.filter(user=request.user).aexists()
        
        char_link, created = await CharacterLink.objects.aupdate_or_create(
            user=request.user,
            character_name=character_name,
            defaults={
                "ocid": f"mock_ocid_{random.randint(100000, 999999)}",
                "world_name": "루나",
                "is_main": is_first,
                "verified_at": timezone.now()
            }
        )
        
        # 인증 코드 사용 후 세션에서 제거
        del request.session[f"verify_code_{character_name}"]
        request.session.modified = True
        
        return JsonResponse(
            {
                "success": True,
                "message": "캐릭터 본인 인증이 성공적으로 완료되었습니다. (Debug Mock)",
                "character": {
                    "character_name": char_link.character_name,
                    "world_name": char_link.world_name,
                    "ocid": char_link.ocid,
                    "is_main": char_link.is_main
                }
            },
            status=200,
        )

    # 실제 넥슨 Open API 통신 검증 로직 실행
    import aiohttp
    from apps.character.nexon.client import fetch_character_ocid, _fetch_single_endpoint, _build_headers
    
    headers = _build_headers(nexon_api_key)
    
    async with aiohttp.ClientSession() as session:
        # 1. OCID 조회
        ocid = await fetch_character_ocid(session, character_name, headers)
        if not ocid:
            return JsonResponse(
                {"success": False, "error_code": "CHARACTER_NOT_FOUND", "message": "해당 캐릭터를 찾을 수 없습니다."},
                status=404
            )
            
        # 2. 기본 정보 조회 (소개글 확인 목적)
        basic_info = await _fetch_single_endpoint(session, "get_character_basic_info", ocid, headers)
        
        # 넥슨 API 응답에 맞춰 소개글 파싱 (캐릭터 프로필 소개글은 character_description 필드에 탑재)
        character_desc = basic_info.get("character_description", "") or ""
        world_name = basic_info.get("world_name", "알 수 없음")
        
        # 소개글에 발급된 인증코드가 포함되어 있는지 대조
        if verification_code not in character_desc:
            return JsonResponse(
                {
                    "success": False,
                    "error_code": "VERIFICATION_FAILED",
                    "message": "인게임 소개글에서 인증 코드를 확인할 수 없거나 일치하지 않습니다."
                },
                status=400
            )
            
        # 3. 인증 통과 시 DB에 연동 데이터 기록/갱신
        from apps.character.models import CharacterLink
        from django.utils import timezone
        
        is_first = not await CharacterLink.objects.filter(user=request.user).aexists()
        
        char_link, created = await CharacterLink.objects.aupdate_or_create(
            user=request.user,
            character_name=character_name,
            defaults={
                "ocid": ocid,
                "world_name": world_name,
                "is_main": is_first,
                "verified_at": timezone.now()
            }
        )
        
        # 성공 시 임시 세션 삭제
        del request.session[f"verify_code_{character_name}"]
        request.session.modified = True
        
        logger.info(f"캐릭터 연동 본인 인증 완료: {character_name} -> {request.user.username}")
        
        return JsonResponse(
            {
                "success": True,
                "message": "캐릭터 본인 인증이 성공적으로 완료되었습니다.",
                "character": {
                    "character_name": char_link.character_name,
                    "world_name": char_link.world_name,
                    "ocid": char_link.ocid,
                    "is_main": char_link.is_main
                }
            },
            status=200
        )

