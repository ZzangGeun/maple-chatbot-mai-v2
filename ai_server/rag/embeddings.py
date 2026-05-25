# -*- coding: utf-8 -*-
"""
임베딩 생성 서비스
"""

from typing import List, Any
from langchain_core.embeddings import Embeddings
from sentence_transformers import SentenceTransformer
import torch
import logging

logger = logging.getLogger(__name__)

class QwenEmbeddings(Embeddings):
    model_name: str = "Qwen/Qwen3-Embedding-0.6B"
    def __init__(self, **kwargs):

        super().__init__(**kwargs)
        # 3. 디바이스 설정 (Private 변수 _device 사용)
        if torch.cuda.is_available():
            self._device = "cuda"
        else:
            self._device = "cpu"
            
        self._model = SentenceTransformer(
            self.model_name, 
            trust_remote_code=True, 
            device=self._device
        )

    def embed_documents(self, documents: List[str]) -> List[List[float]]:
        """
        문서 벡터화(학습용)
        """
        embeddings = self._model.encode(
            documents, 
            batch_size=16, 
            show_progress_bar=True, 
            normalize_embeddings=True
        )

        return embeddings.tolist()  

    def embed_query(self, text: str) -> List[float]:
        """
        사용자 질문 벡터화(검색용)
        """
        embedding = self._model.encode(
            text, 
            normalize_embeddings=True
        )
        return embedding.tolist()
