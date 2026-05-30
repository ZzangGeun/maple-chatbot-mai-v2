# ai_server/prompts/__init__.py
"""
프롬프트 패키지

- templates.py : PromptTemplate Enum — 모든 프롬프트를 중앙 관리
- loader.py    : get_prompt() — Enum 또는 문자열 키로 프롬프트 조회
"""

from ai_server.prompts.templates import PromptTemplate
from ai_server.prompts.loader import get_prompt

__all__ = ["PromptTemplate", "get_prompt"]
