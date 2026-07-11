# apps/character/services.py
"""캐릭터 연동 본인 인증 비즈니스 로직 모듈

뷰(views.py)에 흩어져 있던 비즈니스 로직을 분리하여 비비동기 흐름을 제어합니다.
세션 기반 임시 코드 검증, 넥슨 Open API 조회 및 모델 매니저를 통한 DB 갱신을 수행합니다.
"""

import logging
import secrets
from typing import Any

import aiohttp
from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser
from django.db import DatabaseError

from apps.character.models import CharacterLink
from apps.character.nexon.client import (
    build_headers,
    fetch_character_basic_info,
    fetch_character_ocid,
)

logger = logging.getLogger(__name__)


def _verification_session_key(character_name: str) -> str:
    return f"verify_code_{character_name}"


def _serialize_character_link(character_link: CharacterLink) -> dict[str, Any]:
    return {
        "character_name": character_link.character_name,
        "world_name": character_link.world_name,
        "ocid": character_link.ocid,
        "is_main": character_link.is_main,
    }


async def _save_character_link(
    user: AbstractBaseUser,
    character_name: str,
    ocid: str,
    world_name: str,
) -> dict[str, Any]:
    is_first = await CharacterLink.objects.is_first_link_async(user)
    character_link, _ = await CharacterLink.objects.update_or_create_link_async(
        user=user,
        character_name=character_name,
        ocid=ocid,
        world_name=world_name,
        is_main=is_first,
    )
    return _serialize_character_link(character_link)


def _consume_verification_code(session: Any, character_name: str) -> None:
    del session[_verification_session_key(character_name)]
    session.modified = True


def generate_verification_code(session: Any, character_name: str) -> str:
    """캐릭터 연동 본인 인증을 위한 1회성 6자리 인증 코드를 생성하여 세션에 보관합니다.

    Args:
        session: Django Request Session 객체.
        character_name: 메이플스토리 캐릭터 이름.

    Returns:
        생성된 인증 코드 문자열 (형식: MAI-XXXX).
    """
    character_name = character_name.strip()
    rand_num = secrets.randbelow(9000) + 1000
    verification_code: str = f"MAI-{rand_num}"

    # 캐릭터명과 매핑하여 세션에 보관 (이후 대조 및 세션 스푸핑 방지 목적)
    session[_verification_session_key(character_name)] = verification_code
    session.modified = True

    logger.info("캐릭터 연동 코드 발급 완료: %s", character_name)
    return verification_code


async def verify_and_link_character(
    user: AbstractBaseUser,
    session: Any,
    character_name: str,
    verification_code: str,
) -> tuple[bool, str, dict[str, Any] | None]:
    """임시 세션 인증 코드를 대조하고 넥슨 Open API 조회를 통해 실제 본인 소유의 캐릭터인지 검증 및 연동합니다.

    Args:
        user: 로그인한 Django 사용자 객체.
        session: Django Request Session 객체.
        character_name: 메이플스토리 캐릭터 이름.
        verification_code: 사용자가 입력한 인증 코드.

    Returns:
        (성공여부, 에러코드/메시지, 연동완료된 캐릭터 정보 딕셔너리) 튜플.
    """
    # 1. 세션에 기록된 임시 인증 코드 유효성 확인
    character_name = character_name.strip()
    verification_code = verification_code.strip()
    cached_code = session.get(_verification_session_key(character_name))
    if not cached_code or cached_code != verification_code:
        logger.warning("인증 코드 검증 실패: %s", character_name)
        return False, "VERIFICATION_FAILED", None

    nexon_api_key = getattr(settings, "NEXON_API_KEY", "")

    # 2-1. 개발/디버깅 환경 대응 (NEXON_API_KEY가 없고 DEBUG 모드인 경우 Mock 처리)
    if settings.DEBUG and not nexon_api_key:
        logger.warning("NEXON_API_KEY가 설정되지 않아 디버깅 모드로 가상 연동을 성공 처리합니다.")
        character_info = await _save_character_link(
            user,
            character_name,
            f"mock_ocid_{secrets.token_hex(6)}",
            "루나",
        )
        _consume_verification_code(session, character_name)
        return True, "SUCCESS", character_info

    # 2-2. 넥슨 Open API 호출 및 게임 내 프로필 검증
    headers = build_headers(nexon_api_key)

    try:
        async with aiohttp.ClientSession() as http_session:
            # OCID(식별자) 조회
            ocid = await fetch_character_ocid(http_session, character_name, headers)
            if not ocid:
                logger.warning("캐릭터 OCID 조회 실패: %s", character_name)
                return False, "CHARACTER_NOT_FOUND", None

            # 기본 프로필 조회
            basic_info = await fetch_character_basic_info(
                http_session,
                ocid,
                headers,
            )

            character_desc = basic_info.get("character_description", "") or ""
            world_name = basic_info.get("world_name", "알 수 없음")

            # 게임 내 캐릭터 소개글에 발급된 인증 코드가 삽입되었는지 비교 검증
            if verification_code not in character_desc:
                logger.warning("인게임 소개글 내 인증코드 불일치: %s", character_name)
                return False, "CODE_MISMATCH", None

            character_info = await _save_character_link(
                user,
                character_name,
                ocid,
                world_name,
            )

        _consume_verification_code(session, character_name)
        logger.info(
            "캐릭터 본인인증 및 연동 성공: %s -> %s",
            character_name,
            user.username,
        )
        return True, "SUCCESS", character_info

    except aiohttp.ClientError as e:
        logger.error("넥슨 Open API 통신 장애: %s", e)
        return False, "API_COMMUNICATION_ERROR", None
    except (DatabaseError, KeyError, TypeError, ValueError) as e:
        logger.error("캐릭터 연동 처리 중 서버 오류: %s", e)
        return False, "SERVER_ERROR", None
