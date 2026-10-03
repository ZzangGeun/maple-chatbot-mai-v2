# ai_server/llm/gemini_loader.py
"""
Gemini LLM 로더 모듈

설정별 캐싱 패턴:
  용도(생성/분류/추출)에 따라 서로 다른 temperature·사고(thinking) 설정이 필요하므로
  (temperature, thinking_budget)을 키로 인스턴스를 캐싱합니다.
  같은 설정 요청은 항상 동일한 인스턴스를 재사용합니다.

사용법:
  from ai_server.llm.gemini_loader import get_gemini_llm
  llm = get_gemini_llm()                                   # 생성용 (기본 temperature=0.8)
  llm = get_gemini_llm(temperature=0.0, thinking_budget=0)  # 분류/추출용 (결정적 출력, 사고 생략)
"""

import logging

from langchain_google_genai import ChatGoogleGenerativeAI

from ai_server.config import settings

logger = logging.getLogger("GeminiLoader")


# ---------------------------------------------------------------------------
# 설정별 인스턴스 캐시 — 같은 설정은 항상 동일 인스턴스를 재사용합니다.
# ---------------------------------------------------------------------------
_llm_cache: dict[tuple[float, int | None], ChatGoogleGenerativeAI] = {}


def _create_llm(temperature: float, thinking_budget: int | None) -> ChatGoogleGenerativeAI:
    """Gemini API 모델 인스턴스를 생성합니다."""
    try:
        api_key = settings.api.google_api_key
        if not api_key:
            raise ValueError("GOOGLE_API_KEY가 환경변수에 설정되지 않았습니다.")

        llm = ChatGoogleGenerativeAI(
            model=settings.model.gemini_model,
            google_api_key=api_key,
            temperature=temperature,
            thinking_budget=thinking_budget,
        )
        logger.info(
            f"Gemini LLM 로드 완료. (temperature={temperature}, thinking_budget={thinking_budget})"
        )
        return llm
    except Exception as e:
        logger.error(f"Gemini LLM 로드 실패: {e}")
        raise


def get_gemini_llm(
    temperature: float = 0.8, thinking_budget: int | None = None
) -> ChatGoogleGenerativeAI:
    """
    Gemini LLM 인스턴스를 반환합니다.

    Args:
        temperature: 샘플링 온도.
                     답변 생성은 기본값(0.8), 분류/구조화 추출은 0.0을 권장합니다.
        thinking_budget: 사고(thinking) 토큰 예산. None이면 모델 기본값(동적)을 따르고,
                         0이면 사고를 생략해 응답이 빨라집니다. 분류·추출·재작성처럼
                         단순한 호출에는 0을 권장합니다.

    Returns:
        ChatGoogleGenerativeAI 인스턴스 (설정별 캐싱).
    """
    key = (temperature, thinking_budget)
    if key not in _llm_cache:
        _llm_cache[key] = _create_llm(temperature, thinking_budget)
    return _llm_cache[key]
