# -*- coding: utf-8 -*-
"""
프롬프트 로더 모듈

PromptTemplate Enum을 통해 프롬프트를 조회합니다.
용도와 역할 기반으로 변경된 Enum 구조에 대응하며, 모델 구분을 명시적으로 분리하였습니다.
기존 모델 접두사가 포함된 문자열 키 조회도 하위 호환을 위해 유지합니다.
"""

import logging

from ai_server.prompts.templates import PromptTemplate

logger = logging.getLogger(__name__)


def get_prompt(template: PromptTemplate | str, model: str = "gemini") -> str:
    """
    프롬프트 템플릿을 조회하여 반환합니다.

    PromptTemplate Enum 멤버를 직접 전달하는 것을 권장하며,
    하위 호환을 위해 모델 접두사가 포함된 문자열 키(예: 'gemini_rag_system')도 함께 지원합니다.

    Args:
        template: 조회할 프롬프트. PromptTemplate Enum 멤버 또는 문자열 키.
        model: 조회 대상 LLM 종류 ('gemini' 또는 'local'). 기본값은 'gemini'.

    Returns:
        프롬프트 텍스트 문자열.

    Raises:
        KeyError: 유효하지 않은 문자열 키가 전달되었거나 해당 모델의 템플릿이 정의되지 않은 경우.
    """
    # 모델 매개변수 소문자 및 공백 처리
    model_key = model.lower().strip()

    # Enum 멤버가 직접 전달된 경우 — 권장 방식
    if isinstance(template, PromptTemplate):
        logger.info(f"[{template.name}] Enum으로부터 '{model_key}' 프롬프트를 로드했습니다.")
        try:
            return template.value[model_key]
        except KeyError as e:
            err_msg = f"프롬프트 '{template.name}'에 모델 '{model_key}'용 템플릿이 존재하지 않습니다."
            logger.error(err_msg)
            raise KeyError(err_msg) from e

    # 하위 호환: 문자열 키를 대문자로 변환하여 Enum 조회 시도
    raw_key = template.upper().strip()
    
    # 예: 'GEMINI_CHAT_SYSTEM'이나 'LOCAL_CHAT_SYSTEM'처럼 기존 접두사가 있는 경우 파싱
    if raw_key.startswith("GEMINI_"):
        model_key = "gemini"
        enum_key = raw_key[len("GEMINI_"):]
    elif raw_key.startswith("LOCAL_"):
        model_key = "local"
        enum_key = raw_key[len("LOCAL_"):]
    else:
        enum_key = raw_key

    try:
        matched = PromptTemplate[enum_key]
        logger.info(f"[{enum_key}] 문자열 키로부터 '{model_key}' 프롬프트를 로드했습니다.")
        return matched.value[model_key]
    except KeyError as e:
        err_msg = (
            f"프롬프트 '{template}' (모델: '{model_key}')을 찾을 수 없습니다. "
            f"유효한 키: {[t.name for t in PromptTemplate]}"
        )
        logger.error(err_msg)
        raise KeyError(err_msg) from e
