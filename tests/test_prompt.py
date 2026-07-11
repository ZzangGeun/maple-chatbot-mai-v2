# -*- coding: utf-8 -*-
"""
프롬프트 로더 및 Enum 통합 테스트

개선된 PromptTemplate 구조와 get_prompt 함수의 하위 호환성을 검증합니다.
"""

import pytest

from ai_server.prompts import PromptTemplate, get_prompt


def test_prompt_template_enum_keys() -> None:
    """PromptTemplate Enum 멤버들이 용도_역할 패턴으로 명명되어 있는지 확인합니다."""
    # GEMINI_ 혹은 LOCAL_ 접두사가 없는지 검증
    for member in PromptTemplate:
        assert not member.name.startswith("GEMINI_"), f"접두사 GEMINI_가 포함됨: {member.name}"
        assert not member.name.startswith("LOCAL_"), f"접두사 LOCAL_가 포함됨: {member.name}"
        
        # 딕셔너리 구조 검증 ('gemini'와 'local' 키 존재)
        assert isinstance(member.value, dict), f"멤버의 값이 딕셔너리가 아님: {member.name}"
        assert "gemini" in member.value, f"'gemini' 키가 누락됨: {member.name}"
        assert "local" in member.value, f"'local' 키가 누락됨: {member.name}"


def test_get_prompt_with_enum() -> None:
    """PromptTemplate Enum 객체를 직접 get_prompt에 전달할 때 정상 작동하는지 검증합니다."""
    # CHAT_SYSTEM 프롬프트 조회 검증
    gemini_prompt = get_prompt(PromptTemplate.CHAT_SYSTEM, model="gemini")
    local_prompt = get_prompt(PromptTemplate.CHAT_SYSTEM, model="local")

    assert "돌의 정령" in gemini_prompt
    assert "<|im_start|>system" in local_prompt
    assert "돌의 정령" in local_prompt


def test_get_prompt_with_string_keys_backward_compatibility() -> None:
    """하위 호환성 문자열 키가 정상적으로 예전 방식과 새 방식 모두 매핑되는지 검증합니다."""
    # 1. 예전 스타일의 접두사가 있는 문자열 키
    prompt_gemini_legacy = get_prompt("gemini_chat_system")
    prompt_local_legacy = get_prompt("local_chat_system")

    assert "돌의 정령" in prompt_gemini_legacy
    assert "<|im_start|>system" in prompt_local_legacy

    # 2. 새로운 스타일의 접두사 없는 문자열 키 + model 파라미터 조합
    prompt_gemini_new = get_prompt("chat_system", model="gemini")
    prompt_local_new = get_prompt("chat_system", model="local")

    assert "돌의 정령" in prompt_gemini_new
    assert "<|im_start|>system" in prompt_local_new


def test_get_prompt_invalid_cases() -> None:
    """유효하지 않은 키나 모델 파라미터가 전달되었을 때 예외 처리가 정상 작동하는지 검증합니다."""
    # 유효하지 않은 문자열 키인 경우 KeyError 발생 확인
    with pytest.raises(KeyError):
        get_prompt("non_existent_template")

    # 유효하지 않은 모델명이 지정되었을 때 KeyError 발생 확인
    with pytest.raises(KeyError):
        get_prompt(PromptTemplate.CHAT_SYSTEM, model="invalid_model")
