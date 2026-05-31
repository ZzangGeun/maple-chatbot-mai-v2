# ai_server/llm/gemini_loader.py
"""
Gemini LLM 로더 모듈

모듈 수준 싱글턴 패턴:
  파이썬은 모듈을 최초 import 시 한 번만 실행하므로
  `_loader` 인스턴스는 프로세스 생애 주기 동안 단 하나만 생성됩니다.

사용법:
  from ai_server.llm.gemini_loader import get_gemini_llm
  llm = get_gemini_llm()
"""

import logging

from langchain_google_genai import ChatGoogleGenerativeAI

from ai_server.config import settings

logger = logging.getLogger("GeminiLoader")


class GeminiLoader:
    """Gemini API LLM을 초기화하는 클래스."""

    def __init__(self) -> None:
        self._llm: ChatGoogleGenerativeAI | None = None
        self._load_model()

    def _load_model(self) -> None:
        """
        Gemini API 모델을 초기화합니다.

        모듈 import 시 한 번만 호출되므로 API 클라이언트를 매 요청마다 재생성하지 않습니다.
        """
        try:
            api_key = settings.api.google_api_key
            if not api_key:
                raise ValueError("GOOGLE_API_KEY가 환경변수에 설정되지 않았습니다.")

            self._llm = ChatGoogleGenerativeAI(
                model="gemini-2.5-flash",
                google_api_key=api_key,
                temperature=0.8,
            )
            logger.info("Gemini LLM 로드 완료.")
        except Exception as e:
            logger.error(f"Gemini LLM 로드 실패: {e}")
            raise

    def get_llm(self) -> ChatGoogleGenerativeAI:
        return self._llm


# ---------------------------------------------------------------------------
# 모듈 수준 싱글턴 — import 시 딱 한 번 인스턴스를 생성합니다.
# ---------------------------------------------------------------------------
_loader = GeminiLoader()


def get_gemini_llm() -> ChatGoogleGenerativeAI:
    """
    Gemini LLM 인스턴스를 반환합니다.

    Returns:
        ChatGoogleGenerativeAI 인스턴스.
    """
    return _loader.get_llm()
