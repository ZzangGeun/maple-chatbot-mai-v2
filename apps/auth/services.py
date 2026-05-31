# auth/services.py
"""
계정(회원가입/로그인) 비즈니스 로직 모듈

뷰(views.py)에서 비즈니스 규칙을 분리하여 뷰가 얇게 유지되도록 합니다.
뷰는 HTTP 요청/응답 처리만 담당하고, 실제 로직은 이 모듈에 집중됩니다.
"""

import logging
import re

from asgiref.sync import sync_to_async
from django.contrib.auth.models import User

from apps.auth.models import UserProfile
from apps.character.nexon.character_service import process_signup_with_key

logger = logging.getLogger(__name__)


async def validate_signup_data(data: dict) -> tuple[bool, str]:
    """
    회원가입 요청 데이터의 유효성을 검사합니다.
    넥슨 API 키를 통해 계정 내 대표 캐릭터(최고 레벨)가 입력한 메이플 닉네임과 일치하는지 비동기로 검증합니다.

    Args:
        data: 회원가입 폼 데이터 딕셔너리.
              필수 키: user_id, password, confirm_password, maple_nickname, nexon_api_key

    Returns:
        (is_valid, error_message) 튜플.
        유효하면 (True, ""), 유효하지 않으면 (False, 오류 메시지).
    """
    user_id = data.get("user_id", "").strip()
    password = data.get("password", "").strip()
    confirm_password = data.get("confirm_password", "").strip()
    maple_nickname = data.get("maple_nickname", "").strip()
    nexon_api_key = data.get("nexon_api_key", "").strip()

    # 필수 필드 확인
    if not all([user_id, password, confirm_password, maple_nickname, nexon_api_key]):
        return False, "필수 필드를 모두 채워주세요."

    # 아이디 형식 검사 (6~20자, 영문/숫자/밑줄)
    if not re.match(r"^[a-zA-Z0-9_]{6,20}$", user_id):
        return False, "아이디는 6~20자의 영문자, 숫자, 밑줄(_)만 사용할 수 있습니다."

    # 비밀번호 최소 길이 검사
    if len(password) < 8:
        return False, "비밀번호는 최소 8자 이상이어야 합니다."

    # 비밀번호 확인 일치 검사
    if password != confirm_password:
        return False, "비밀번호와 비밀번호 확인이 일치하지 않습니다."

    # 아이디 중복 검사 (비동기)
    if await User.objects.filter(username=user_id).aexists():
        return False, "이미 존재하는 아이디입니다."

    # 메이플 닉네임 중복 검사 (비동기)
    if await UserProfile.objects.filter(maple_nickname=maple_nickname).aexists():
        return False, "이미 사용 중인 메이플 닉네임입니다."

    # 넥슨 API 키 기반 캐릭터 본인 확인 검증
    try:
        nexon_res = await process_signup_with_key(nexon_api_key)
        if not nexon_res:
            return False, "유효하지 않은 넥슨 API 키이거나 해당 계정에 연동된 캐릭터가 존재하지 않습니다."
        
        best_char_name, _ = nexon_res
        
        # 가입 닉네임과 계정의 최고 레벨 대표 캐릭터명이 일치하는지 검사
        if best_char_name.strip().lower() != maple_nickname.strip().lower():
            return False, f"입력하신 닉네임이 해당 API 키 계정의 대표 캐릭터(최고 레벨 캐릭터)와 일치하지 않습니다. (대표 캐릭터명: {best_char_name})"
            
    except Exception as e:
        logger.error(f"회원가입 넥슨 API 검증 중 오류: {e}")
        return False, "넥슨 API 검증 처리 중 서버 오류가 발생했습니다."

    return True, ""


async def create_user_with_profile(
    user_id: str,
    password: str,
    maple_nickname: str,
    nexon_api_key: str,
) -> User:
    """
    Django User와 UserProfile을 비동기적으로 생성합니다.

    비밀번호는 Django의 create_user()가 자동으로 해싱합니다.
    평문 비밀번호가 DB에 저장되지 않도록 반드시 이 함수를 통해야 합니다.

    Args:
        user_id: 사용자 아이디 (username).
        password: 평문 비밀번호.
        maple_nickname: 메이플스토리 캐릭터 닉네임.
        nexon_api_key: 넥슨 API 키.

    Returns:
        생성된 Django User 인스턴스.

    Raises:
        Exception: DB 저장 중 예외 발생 시 상위로 전파합니다.
    """
    # create_user는 동기 헬퍼이므로 sync_to_async로 감싸 호출합니다.
    user = await sync_to_async(User.objects.create_user)(username=user_id, password=password)

    await UserProfile.objects.acreate(
        user=user,
        maple_nickname=maple_nickname,
        nexon_api_key=nexon_api_key,
    )

    logger.info(f"새 사용자 생성 완료: {user_id}")
    return user
