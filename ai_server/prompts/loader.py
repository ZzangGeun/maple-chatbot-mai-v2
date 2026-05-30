# -*- coding: utf-8 -*-
"""
프롬프트 로더 모듈

PromptTemplate Enum을 통해 프롬프트를 조회합니다.
기존 문자열 키 기반 조회도 하위 호환을 위해 유지합니다.
"""

import logging

from ai_server.prompts.templates import PromptTemplate

logger = logging.getLogger(__name__)


def get_prompt(template: PromptTemplate | str) -> str:
    """
    프롬프트 템플릿을 조회하여 반환합니다.

    PromptTemplate Enum 멤버를 직접 전달하는 것을 권장하며,
    하위 호환을 위해 문자열 키(예: 'gemini_rag_system')도 지원합니다.

    Args:
        template: 조회할 프롬프트. PromptTemplate Enum 멤버 또는 문자열 키.

    Returns:
        프롬프트 텍스트 문자열.

    Raises:
        KeyError: 유효하지 않은 문자열 키가 전달된 경우.
    """
    # Enum 멤버가 직접 전달된 경우 — 권장 방식
    if isinstance(template, PromptTemplate):
        logger.info(f"[{template.name}] Enum으로부터 프롬프트를 로드했습니다.")
        return template.value

    # 하위 호환: 문자열 키를 대문자로 변환하여 Enum 조회 시도
    enum_key = template.upper().strip()
    try:
        matched = PromptTemplate[enum_key]
        logger.info(f"[{enum_key}] 문자열 키로부터 프롬프트를 로드했습니다.")
        return matched.value
    except KeyError:
        err_msg = (
            f"프롬프트 '{template}'을 찾을 수 없습니다. "
            f"유효한 키: {[t.name for t in PromptTemplate]}"
        )
        logger.error(err_msg)
        raise KeyError(err_msg)
