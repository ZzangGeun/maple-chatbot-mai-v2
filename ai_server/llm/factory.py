# ai_server/llm/factory.py
"""
LLM 팩토리 모듈

용도별 채팅 모델을 설정(ai_server.config.ModelSettings)에 따라 반환합니다.
그래프 노드는 특정 프로바이더를 직접 import하지 않고 이 모듈만 사용합니다.

  get_utility_llm(): 질문 분류·검색어 재작성·캐릭터명 추출 (LLM_PROVIDER)
                     구조화 출력을 쓰며 temperature 0으로 결정적으로 동작합니다.
  get_answer_llm() : 최종 답변 생성 (ANSWER_LLM_PROVIDER, 비우면 LLM_PROVIDER)

프로바이더:
  "gemini"  → Gemini API
  "deepseek"→ DeepSeek의 OpenAI 호환 Chat Completions API
              (ChatDeepSeek의 function calling 구조화 출력으로 기존 노드를 유지합니다)
  "local"   → OpenAI 호환 API로 서빙되는 로컬 모델 (답변 생성 전용)
              (예: vllm serve fine_tuned_model/merged_qwen --served-model-name merged_qwen)

모든 프로바이더가 채팅 모델(BaseChatModel)이므로 토큰 스트리밍 이벤트
(on_chat_model_stream)가 동일하게 발생합니다.
"""

import logging

from langchain_core.language_models import BaseChatModel

from ai_server.config import settings
from ai_server.llm.gemini_loader import get_gemini_llm

logger = logging.getLogger("LLMFactory")

# 보조 호출은 결정적 출력이 필요합니다.
UTILITY_TEMPERATURE = 0.0
# 사실 기반 답변의 일관성을 위해 생성용 기본값(0.8)보다 낮게 둡니다.
ANSWER_TEMPERATURE = 0.5

# (temperature, 사고 모드)별 DeepSeek 인스턴스 캐시
_deepseek_cache: dict[tuple[float, bool], BaseChatModel] = {}
_local_llm: BaseChatModel | None = None


def _get_deepseek_llm(
    temperature: float, thinking_enabled: bool = False
) -> BaseChatModel:
    """DeepSeek API 모델을 온도와 사고 모드별로 재사용합니다."""
    key = (temperature, thinking_enabled)
    if key not in _deepseek_cache:
        api_key = settings.api.deepseek_api_key
        if not api_key:
            raise ValueError("DEEPSEEK_API_KEY가 환경변수에 설정되지 않았습니다.")

        from langchain_deepseek import ChatDeepSeek

        _deepseek_cache[key] = ChatDeepSeek(
            model=settings.model.deepseek_model,
            api_key=api_key,
            api_base=settings.model.deepseek_api_base,
            # 사고 모드에서는 temperature가 적용되지 않습니다.
            temperature=None if thinking_enabled else temperature,
            # deepseek-flash의 기본 사고 모드를 요청마다 명시적으로 선택합니다.
            extra_body={
                "thinking": {"type": "enabled" if thinking_enabled else "disabled"}
            },
        )
        logger.info(
            "DeepSeek LLM 생성 완료. (model=%s, temperature=%s, thinking=%s)",
            settings.model.deepseek_model,
            _deepseek_cache[key].temperature,
            thinking_enabled,
        )
    return _deepseek_cache[key]


def _get_local_llm() -> BaseChatModel:
    """OpenAI 호환 API로 서빙되는 로컬 모델 클라이언트를 반환합니다."""
    global _local_llm

    if _local_llm is None:
        base_url = settings.model.local_llm_base_url
        if not base_url:
            raise ValueError(
                "ANSWER_LLM_PROVIDER=local을 사용하려면 LOCAL_LLM_BASE_URL"
                "(OpenAI 호환 서버 주소, 예: http://localhost:8002/v1)이 필요합니다."
            )

        from langchain_openai import ChatOpenAI

        _local_llm = ChatOpenAI(
            base_url=base_url,
            api_key="EMPTY",  # vLLM 등 로컬 서버는 API 키를 검사하지 않습니다.
            model=settings.model.local_llm_model,
            temperature=ANSWER_TEMPERATURE,
            # Qwen3의 사고 과정(<think>) 출력을 끄고 답변만 받습니다. (vLLM chat_template_kwargs)
            extra_body={"chat_template_kwargs": {"enable_thinking": False}},
        )
        logger.info(f"로컬 LLM 클라이언트 생성 완료: {base_url}")

    return _local_llm


def get_utility_llm() -> BaseChatModel:
    """질문 분류·검색어 재작성·캐릭터명 추출에 사용할 채팅 모델을 반환합니다."""
    if settings.model.provider == "deepseek":
        return _get_deepseek_llm(UTILITY_TEMPERATURE)
    # 단순한 판단 작업이므로 사고(thinking)를 생략해 응답 지연을 줄입니다.
    return get_gemini_llm(temperature=UTILITY_TEMPERATURE, thinking_budget=0)


def get_answer_llm() -> BaseChatModel:
    """최종 답변 생성에 사용할 채팅 모델을 반환합니다."""
    provider = settings.model.answer_provider
    if provider == "local":
        return _get_local_llm()
    if provider == "deepseek":
        return _get_deepseek_llm(
            ANSWER_TEMPERATURE,
            thinking_enabled=settings.model.deepseek_thinking_enabled,
        )
    return get_gemini_llm(temperature=ANSWER_TEMPERATURE)
