# ai_server/llm/factory.py
"""
LLM 팩토리 모듈

환경변수 LLM_PROVIDER에 따라 적절한 LLM 인스턴스를 반환합니다.
각 로더 모듈은 자체 모듈 수준 싱글턴을 관리하므로
factory는 단순히 올바른 함수를 호출하는 역할만 합니다.

  "gemini" → get_gemini_llm()
  "local"  → get_local_llm() (기본값)
"""

import logging
from typing import Any

from ai_server.config import settings

logger = logging.getLogger("LLMFactory")


def get_llm() -> Any:
    """
    환경변수 LLM_PROVIDER에 맞는 LLM 인스턴스를 반환합니다.

    로더 모듈이 모듈 수준 싱글턴을 보장하므로
    이 함수를 여러 번 호출해도 모델이 재로드되지 않습니다.

    Returns:
        LangChain BaseChatModel 인스턴스.
    """
    provider = settings.model.provider
    logger.info(f"LLM Provider: {provider}")

    if provider == "gemini":
        from ai_server.llm.gemini_loader import get_gemini_llm
        return get_gemini_llm()

    if provider == "local":
        from ai_server.llm.llm_loader import get_local_llm
        return get_local_llm()

    logger.warning(f"알 수 없는 provider '{provider}'. 로컬 LLM으로 폴백합니다.")
    from ai_server.llm.llm_loader import get_local_llm
    return get_local_llm()
