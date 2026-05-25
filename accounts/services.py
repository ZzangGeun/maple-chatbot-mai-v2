# accounts/services.py
"""
계정(회원가입/로그인) 비즈니스 로직 모듈

뷰(views.py)에서 비즈니스 규칙을 분리하여 뷰가 얇게 유지되도록 합니다.
뷰는 HTTP 요청/응답 처리만 담당하고, 실제 로직은 이 모듈에 집중됩니다.
"""

import logging
import re

from django.contrib.auth.models import User

from accounts.models import UserProfile

logger = logging.getLogger(__name__)


def validate_signup_data(data: dict) -> tuple[bool, str]:
    """
    회원가입 요청 데이터의 유효성을 검사합니다.

    Args:
        data: 회원가입 폼 데이터 딕셔너리.
              필수 키: user_id, password, confirm_password, maple_nickname

    Returns:
        (is_valid, error_message) 튜플.
        유효하면 (True, ""), 유효하지 않으면 (False, 오류 메시지).
    """
    user_id = data.get("user_id", "").strip()
    password = data.get("password", "").strip()
    confirm_password = data.get("confirm_password", "").strip()
    maple_nickname = data.get("maple_nickname", "").strip()

    # 필수 필드 확인
    if not all([user_id, password, confirm_password, maple_nickname]):
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

    # 아이디 중복 검사
    if User.objects.filter(username=user_id).exists():
        return False, "이미 존재하는 아이디입니다."

    # 메이플 닉네임 중복 검사
    if UserProfile.objects.filter(maple_nickname=maple_nickname).exists():
        return False, "이미 사용 중인 메이플 닉네임입니다."

    return True, ""


def create_user_with_profile(
    user_id: str,
    password: str,
    maple_nickname: str,
    nexon_api_key: str | None = None,
) -> User:
    """
    Django User와 UserProfile을 생성합니다.

    비밀번호는 Django의 create_user()가 자동으로 해싱합니다.
    평문 비밀번호가 DB에 저장되지 않도록 반드시 이 함수를 통해야 합니다.

    Args:
        user_id: 사용자 아이디 (username).
        password: 평문 비밀번호.
        maple_nickname: 메이플스토리 캐릭터 닉네임.
        nexon_api_key: 넥슨 API 키 (선택사항).

    Returns:
        생성된 Django User 인스턴스.

    Raises:
        Exception: DB 저장 중 예외 발생 시 상위로 전파합니다.
    """
    user = User.objects.create_user(username=user_id, password=password)

    UserProfile.objects.create(
        user=user,
        maple_nickname=maple_nickname,
        nexon_api_key=nexon_api_key if nexon_api_key else None,
    )

    logger.info(f"새 사용자 생성 완료: {user_id}")
    return user
