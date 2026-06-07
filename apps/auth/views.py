# auth/views.py
"""
인증 API 뷰 (표준 Django JsonResponse)

Django Ninja Router에서 표준 Django 뷰로 전환합니다.
비즈니스 로직은 auth.services에 위임하고,
입력값 유효성 검사는 auth.schemas(Pydantic)가 담당합니다.
"""

import json
import logging

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from asgiref.sync import sync_to_async
from pydantic import ValidationError

from apps.auth.models import UserProfile
from apps.auth.schemas import LoginSchema, SignupSchema
from apps.auth.services import create_user_with_profile, validate_signup_data

logger = logging.getLogger(__name__)


def _parse_json_body(request) -> dict:
    """요청 바디에서 JSON을 파싱합니다."""
    try:
        return json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return {}


@csrf_exempt
@require_http_methods(["POST"])
async def signup(request) -> JsonResponse:
    """
    회원가입 엔드포인트.

    POST /api/v1/auth/signup/

    - Pydantic 스키마에서 1차 유효성 검사(형식, 비밀번호 일치)
    - services.validate_signup_data에서 2차 검사(중복 여부 및 넥슨 캐릭터 본인확인)
    """
    raw_data = _parse_json_body(request)

    # Pydantic으로 입력값 유효성 검사
    try:
        data = SignupSchema(**raw_data)
    except ValidationError as e:
        return JsonResponse(
            {"detail": e.errors()[0].get("msg", "유효하지 않은 입력입니다.")},
            status=400,
        )

    # DB 중복 등 비즈니스 규칙 및 넥슨 API 인증 검사
    is_valid, error_message = await validate_signup_data(
        {
            "user_id": data.username,
            "password": data.password,
            "confirm_password": data.confirm_password,
            "maple_nickname": data.maple_nickname,
            "nexon_api_key": data.nexon_api_key,
        }
    )
    if not is_valid:
        return JsonResponse({"detail": error_message}, status=400)

    try:
        user = await create_user_with_profile(
            user_id=data.username,
            password=data.password,
            maple_nickname=data.maple_nickname,
            nexon_api_key=data.nexon_api_key,
        )
        return JsonResponse(
            {
                "message": "회원가입이 완료되었습니다.",
                "username": user.username,
                "maple_nickname": data.maple_nickname,
            },
            status=201,
        )
    except Exception as e:
        logger.error(f"회원가입 처리 중 오류: {e}")
        return JsonResponse(
            {"detail": "회원가입 중 서버 오류가 발생했습니다."}, status=500
        )


@csrf_exempt
@require_http_methods(["POST"])
async def login_view(request) -> JsonResponse:
    """
    로그인 엔드포인트.

    POST /api/v1/auth/login/

    Django의 authenticate()로 자격증명을 확인하고 세션을 생성합니다.
    """
    raw_data = _parse_json_body(request)

    try:
        data = LoginSchema(**raw_data)
    except ValidationError as e:
        return JsonResponse(
            {"detail": e.errors()[0].get("msg", "유효하지 않은 입력입니다.")},
            status=400,
        )

    # 1. 아이디 존재 여부 검사 (보안상 권장되지는 않으나 명확한 오류 피드백을 위해 분리)
    user_exists = await User.objects.filter(username=data.username).aexists()
    if not user_exists:
        logger.warning(f"로그인 실패 (존재하지 않는 아이디): {data.username}")
        return JsonResponse(
            {"detail": "존재하지 않는 아이디입니다."}, status=401
        )

    credentials = {
        "username": data.username,
        "password": data.password,
    }
    user = await sync_to_async(authenticate)(**credentials)

    if user is None:
        logger.warning(f"로그인 실패 (비밀번호 불일치): {data.username}")
        return JsonResponse(
            {"detail": "비밀번호가 일치하지 않습니다."}, status=401
        )

    if not user.is_active:
        return JsonResponse({"detail": "비활성화된 계정입니다."}, status=401)

    await sync_to_async(login)(request, user)

    profile = await sync_to_async(UserProfile.objects.get_by_user_or_none)(user)
    maple_nickname = profile.maple_nickname if profile else None

    logger.info(f"로그인 성공: {data.username}")

    return JsonResponse(
        {
            "message": f"{user.username}님, 환영합니다!",
            "user": {"id": user.id, "username": user.username, "email": user.email},
            "maple_nickname": maple_nickname,
        },
        status=200,
    )


@csrf_exempt
@require_http_methods(["POST"])
def logout_view(request) -> JsonResponse:
    """
    로그아웃 엔드포인트.

    POST /api/v1/auth/logout/

    세션 인증이 필요합니다.
    """
    if not request.user.is_authenticated:
        return JsonResponse({"detail": "로그인 상태가 아닙니다."}, status=401)

    logger.info(f"로그아웃: {request.user.username}")
    logout(request)
    return JsonResponse({"message": "로그아웃되었습니다."}, status=200)


@require_http_methods(["GET"])
def user_info(request) -> JsonResponse:
    """
    현재 로그인한 사용자 정보 조회 엔드포인트.

    GET /api/v1/auth/user/
    """
    if not request.user.is_authenticated:
        return JsonResponse({"detail": "로그인이 필요합니다."}, status=401)

    user: User = request.user
    profile = UserProfile.objects.get_by_user_or_none(user)
    maple_nickname = profile.maple_nickname if profile else None

    return JsonResponse(
        {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "profile": {
                "maple_nickname": maple_nickname,
            },
        },
        status=200,
    )
