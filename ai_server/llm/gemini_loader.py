# ai_server/llm/gemini_loader.py
"""
Gemini LLM 로더 모듈

temperature별 캐싱 패턴:
  용도(생성/분류/추출)에 따라 서로 다른 temperature 인스턴스가 필요하므로
  temperature를 키로 인스턴스를 캐싱합니다.
  같은 temperature 요청은 항상 동일한 인스턴스를 재사용합니다.

사용법:
  from ai_server.llm.gemini_loader import get_gemini_llm
  llm = get_gemini_llm()               # 생성용 (기본 temperature=0.8)
  llm = get_gemini_llm(temperature=0.0)  # 분류/추출용 (결정적 출력)
"""

import logging

from langchain_google_genai import ChatGoogleGenerativeAI

from ai_server.config import settings

logger = logging.getLogger("GeminiLoader")


# ---------------------------------------------------------------------------
# temperature별 인스턴스 캐시 — 같은 temperature는 항상 동일 인스턴스를 재사용합니다.
# ---------------------------------------------------------------------------
_llm_cache: dict[float, ChatGoogleGenerativeAI] = {}


def _create_llm(temperature: float) -> ChatGoogleGenerativeAI:
    """Gemini API 모델 인스턴스를 생성합니다."""
    try:
        api_key = settings.api.google_api_key
        if not api_key:
            raise ValueError("GOOGLE_API_KEY가 환경변수에 설정되지 않았습니다.")

        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=api_key,
            temperature=temperature,
        )
        logger.info(f"Gemini LLM 로드 완료. (temperature={temperature})")
        return llm
    except Exception as e:
        logger.error(f"Gemini LLM 로드 실패: {e}")
        raise


def get_gemini_llm(temperature: float = 0.8) -> ChatGoogleGenerativeAI:
    """
    Gemini LLM 인스턴스를 반환합니다.

    Args:
        temperature: 샘플링 온도.
                     답변 생성은 기본값(0.8), 분류/구조화 추출은 0.0을 권장합니다.

    Returns:
        ChatGoogleGenerativeAI 인스턴스 (temperature별 캐싱).
    """
    if temperature not in _llm_cache:
        _llm_cache[temperature] = _create_llm(temperature)
    return _llm_cache[temperature]
