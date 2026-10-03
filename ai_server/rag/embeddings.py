# -*- coding: utf-8 -*-
"""
임베딩 생성 서비스

Qwen3-Embedding-0.6B를 sentence-transformers로 불러옵니다.
모델은 처음 임베딩할 때 한 번만 로드하고(프로세스당 하나), 질문은 모델이 권장하는
검색용 지시문(prompt_name="query")을 붙여 임베딩합니다.
"""

import logging
import threading
from typing import Any, List

from langchain_core.embeddings import Embeddings

logger = logging.getLogger(__name__)

MODEL_NAME = "Qwen/Qwen3-Embedding-0.6B"

_model: Any = None
_lock = threading.Lock()


def _get_model() -> Any:
    """SentenceTransformer 모델을 지연 로드합니다. (torch 의존성도 이때 import)"""
    global _model
    with _lock:
        if _model is None:
            import torch
            from sentence_transformers import SentenceTransformer

            device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"임베딩 모델 로드: {MODEL_NAME} ({device})")
            _model = SentenceTransformer(MODEL_NAME, trust_remote_code=True, device=device)
    return _model


class QwenEmbeddings(Embeddings):
    """LangChain 임베딩 인터페이스 구현."""

    def embed_documents(self, documents: List[str]) -> List[List[float]]:
        """문서(청크) 임베딩."""
        embeddings = _get_model().encode(
            documents,
            batch_size=16,
            show_progress_bar=len(documents) > 64,
            normalize_embeddings=True,
        )
        return embeddings.tolist()

    def embed_query(self, text: str) -> List[float]:
        """질문 임베딩. 모델에 검색용 지시문이 정의되어 있으면 함께 사용합니다."""
        model = _get_model()
        prompt_name = "query" if "query" in (getattr(model, "prompts", None) or {}) else None
        embedding = model.encode(text, prompt_name=prompt_name, normalize_embeddings=True)
        return embedding.tolist()
