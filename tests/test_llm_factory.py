# tests/test_llm_factory.py
"""
LLM 팩토리 테스트

LLM_PROVIDER / ANSWER_LLM_PROVIDER 설정에 따라 용도별 모델이 올바르게 선택되는지 검증합니다.
실제 API는 호출하지 않고 모델 인스턴스의 설정만 확인합니다.
"""

import pytest
from langchain_deepseek import ChatDeepSeek
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from pydantic import ValidationError

from ai_server.config import ModelSettings, settings
from ai_server.graph.nodes.route_nodes import RouteDecision
from ai_server.llm import factory, gemini_loader


@pytest.fixture(autouse=True)
def _isolated_llm_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    """테스트마다 캐시와 키 설정을 초기화합니다."""
    monkeypatch.setattr(factory, "_deepseek_cache", {})
    monkeypatch.setattr(factory, "_local_llm", None)
    monkeypatch.setattr(gemini_loader, "_llm_cache", {})
    monkeypatch.setattr(settings.api, "google_api_key", "test-google-key")
    monkeypatch.setattr(settings.api, "deepseek_api_key", "test-deepseek-key")
    monkeypatch.setattr(settings.model, "provider", "gemini")
    monkeypatch.setattr(settings.model, "answer_provider", "gemini")


def _use(monkeypatch: pytest.MonkeyPatch, provider: str, answer_provider: str) -> None:
    monkeypatch.setattr(settings.model, "provider", provider)
    monkeypatch.setattr(settings.model, "answer_provider", answer_provider)


def test_gemini_is_default_for_both_roles() -> None:
    utility = factory.get_utility_llm()
    answer = factory.get_answer_llm()

    assert isinstance(utility, ChatGoogleGenerativeAI)
    assert utility.temperature == factory.UTILITY_TEMPERATURE
    # 보조 호출은 사고(thinking)를 생략해 지연을 줄입니다.
    assert utility.thinking_budget == 0
    assert isinstance(answer, ChatGoogleGenerativeAI)
    assert answer.temperature == factory.ANSWER_TEMPERATURE


def test_deepseek_for_both_roles(monkeypatch: pytest.MonkeyPatch) -> None:
    _use(monkeypatch, "deepseek", "deepseek")

    utility = factory.get_utility_llm()
    answer = factory.get_answer_llm()

    assert isinstance(utility, ChatDeepSeek) and isinstance(answer, ChatDeepSeek)
    assert utility.temperature == factory.UTILITY_TEMPERATURE
    assert answer.temperature == factory.ANSWER_TEMPERATURE
    assert answer.model_name == settings.model.deepseek_model


def test_deepseek_structured_output_uses_function_calling(monkeypatch: pytest.MonkeyPatch) -> None:
    """DeepSeek은 json_schema 응답 형식을 지원하지 않으므로 노드의 구조화 출력이 tool 호출로 바뀌어야 합니다."""
    _use(monkeypatch, "deepseek", "deepseek")

    structured = factory.get_utility_llm().with_structured_output(RouteDecision)

    bound_kwargs = structured.first.kwargs
    assert "tools" in bound_kwargs
    assert "response_format" not in bound_kwargs


def test_answer_provider_can_differ_from_utility_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    _use(monkeypatch, "gemini", "deepseek")

    assert isinstance(factory.get_utility_llm(), ChatGoogleGenerativeAI)
    assert isinstance(factory.get_answer_llm(), ChatDeepSeek)


def test_deepseek_requires_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    _use(monkeypatch, "deepseek", "deepseek")
    monkeypatch.setattr(settings.api, "deepseek_api_key", "")

    with pytest.raises(ValueError, match="DEEPSEEK_API_KEY"):
        factory.get_utility_llm()


def test_local_answer_model_requires_base_url(monkeypatch: pytest.MonkeyPatch) -> None:
    _use(monkeypatch, "gemini", "local")
    monkeypatch.setattr(settings.model, "local_llm_base_url", "")

    with pytest.raises(ValueError, match="LOCAL_LLM_BASE_URL"):
        factory.get_answer_llm()

    monkeypatch.setattr(settings.model, "local_llm_base_url", "http://localhost:8002/v1")
    answer = factory.get_answer_llm()

    assert isinstance(answer, ChatOpenAI)
    assert answer.openai_api_base == "http://localhost:8002/v1"
    assert answer.extra_body == {"chat_template_kwargs": {"enable_thinking": False}}


def test_answer_provider_defaults_to_llm_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "DeepSeek")
    monkeypatch.delenv("ANSWER_LLM_PROVIDER", raising=False)

    model_settings = ModelSettings()

    assert model_settings.provider == "deepseek"
    assert model_settings.answer_provider == "deepseek"


@pytest.mark.parametrize(
    ("env", "value"),
    [("LLM_PROVIDER", "openai"), ("LLM_PROVIDER", "local"), ("ANSWER_LLM_PROVIDER", "claude")],
)
def test_unsupported_provider_fails_at_startup(
    monkeypatch: pytest.MonkeyPatch, env: str, value: str
) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    monkeypatch.setenv(env, value)

    with pytest.raises(ValidationError):
        ModelSettings()
