# ai_server/llm/llm_loader.py
"""
로컬 LLM(HuggingFace) 로더 모듈

모듈 수준 싱글턴 패턴:
  파이썬은 모듈을 최초 import 시 한 번만 실행하므로
  `_loader` 인스턴스는 프로세스 생애 주기 동안 단 하나만 생성됩니다.
  `__new__` 오버라이드 없이도 동일한 효과를 얻을 수 있습니다.

사용법:
  from ai_server.llm.llm_loader import get_local_llm
  llm = get_local_llm()
"""

import logging
import os

import torch
from dotenv import load_dotenv
from langchain_huggingface import HuggingFacePipeline
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

load_dotenv()

logger = logging.getLogger("LocalLLMLoader")

MODEL_PATH = os.getenv("MODEL_PATH")
BASE_MODEL = os.getenv("BASE_MODEL")


class LocalLLMLoader:
    """로컬 LLM을 메모리(VRAM)에 로드하는 클래스."""

    def __init__(self) -> None:
        self._llm: HuggingFacePipeline | None = None
        self._load_model()

    def _load_model(self) -> None:
        """
        모델을 VRAM에 로드합니다.

        모듈 import 시 한 번만 호출되므로 매 요청마다 재로드하지 않습니다.
        """
        try:
            tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
            model = AutoModelForCausalLM.from_pretrained(
                MODEL_PATH,
                torch_dtype=torch.float16,
                device_map="cuda",
            )

            pipe = pipeline(
                "text-generation",
                model=model,
                tokenizer=tokenizer,
                max_new_tokens=1024,
                do_sample=True,
                temperature=0.7,
                top_p=0.9,
                top_k=40,
                repetition_penalty=1.1,  # 반복 방지
                return_full_text=False,  # 질문을 포함하지 않고 답변만 반환
            )

            self._llm = HuggingFacePipeline(pipeline=pipe)
            logger.info("로컬 LLM 로드 완료.")
        except Exception as e:
            logger.error(f"로컬 LLM 로드 실패: {e}")
            raise

    def get_llm(self) -> HuggingFacePipeline:
        return self._llm


# ---------------------------------------------------------------------------
# 모듈 수준 싱글턴 — import 시 딱 한 번 인스턴스를 생성합니다.
# ---------------------------------------------------------------------------
_loader = LocalLLMLoader()


def get_local_llm() -> HuggingFacePipeline:
    """
    로컬 LLM 인스턴스를 반환합니다.

    Returns:
        HuggingFacePipeline 인스턴스.
    """
    return _loader.get_llm()
