# ai_server/rag/retriever.py
"""
하이브리드 문서 검색기

벡터 검색(pgvector, 의미 유사도)과 BM25 키워드 검색(kiwipiepy 형태소)을 따로 수행한 뒤
RRF(Reciprocal Rank Fusion)로 순위를 합칩니다. 한쪽 검색이 실패해도 다른 쪽 결과로 답합니다.

'이번 이벤트', '진행 중인 공지'처럼 시점을 묻는 질문은 끝난 이벤트를 빼고 최근 문서를 우대합니다.
"""

import asyncio
import logging
import threading
import time
from collections.abc import Callable
from datetime import date, timedelta

from rank_bm25 import BM25Okapi

from ai_server.rag.documents import Chunk
from ai_server.rag.index import ChunkIndex
from ai_server.rag.tokenizer import tokenize

logger = logging.getLogger(__name__)

# RRF 상수: 순위가 낮은 결과의 영향이 너무 작아지지 않도록 하는 표준값
RRF_K = 60

# 시점을 묻는 질문의 단서
TIME_WORDS = ("이번", "현재", "지금", "요즘", "최근", "진행 중", "진행중", "오늘", "새로 나온", "신규")
# 시점을 묻는 질문에서 '최근'으로 볼 기간과 그때 주는 가중치
RECENT_DAYS = 30
RECENT_BOOST = 1.5


def is_time_sensitive(query: str) -> bool:
    return any(word in query for word in TIME_WORDS)


def _parse_date(value: str | None) -> date | None:
    """'2026-05-27T16:49+09:00' 같은 값에서 날짜만 꺼냅니다."""
    try:
        return date.fromisoformat(str(value)[:10]) if value else None
    except ValueError:
        return None


class HybridRetriever:
    """벡터 검색 + BM25 키워드 검색 하이브리드 검색기."""

    def __init__(
        self,
        index: ChunkIndex,
        *,
        vector_k: int = 20,
        keyword_k: int = 20,
        refresh_seconds: float = 300,
        today: Callable[[], date] = date.today,
    ) -> None:
        """
        Args:
            index: 청크 인덱스
            vector_k / keyword_k: 각 검색에서 합치기 전에 가져올 후보 수
            refresh_seconds: BM25 인덱스를 다시 만드는 주기 (새로 적재한 문서 반영)
            today: 오늘 날짜를 돌려주는 함수 (테스트용 주입)
        """
        self._index = index
        self._vector_k = vector_k
        self._keyword_k = keyword_k
        self._refresh_seconds = refresh_seconds
        self._today = today

        self._lock = threading.Lock()
        self._bm25: BM25Okapi | None = None
        self._corpus: list[Chunk] = []
        self._token_sets: list[set[str]] = []
        self._loaded_at = float("-inf")

    # ------------------------------------------------------------------
    # 키워드 검색
    # ------------------------------------------------------------------

    def refresh(self) -> None:
        """인덱스의 모든 청크로 BM25를 다시 만듭니다."""
        chunks = self._index.all_chunks()
        tokenized = [tokenize(c.text) for c in chunks]
        bm25 = BM25Okapi(tokenized) if chunks else None
        token_sets = [set(tokens) for tokens in tokenized]
        with self._lock:
            self._corpus, self._bm25, self._token_sets = chunks, bm25, token_sets
            self._loaded_at = time.monotonic()
        logger.info(f"BM25 인덱스 갱신: 청크 {len(chunks)}개")

    def _ensure_fresh(self) -> None:
        if time.monotonic() - self._loaded_at >= self._refresh_seconds:
            try:
                self.refresh()
            except Exception as e:
                # 갱신에 실패하면 이전 인덱스를 계속 쓰고, 잠시 후 다시 시도합니다.
                logger.error(f"BM25 인덱스 갱신 실패: {e}")
                with self._lock:
                    self._loaded_at = time.monotonic()

    def keyword_search(self, query: str, k: int) -> list[Chunk]:
        self._ensure_fresh()
        with self._lock:
            bm25, corpus, token_sets = self._bm25, self._corpus, self._token_sets
        tokens = tokenize(query)
        if bm25 is None or not tokens:
            return []
        # 문서가 적으면 BM25 점수(IDF)가 0 이하가 될 수 있으므로,
        # 후보는 질의 형태소가 하나라도 겹치는 청크로 정하고 순서만 점수로 매깁니다.
        query_tokens = set(tokens)
        candidates = [i for i, token_set in enumerate(token_sets) if query_tokens & token_set]
        scores = bm25.get_scores(tokens)
        ranked = sorted(candidates, key=lambda i: scores[i], reverse=True)
        return [corpus[i] for i in ranked[:k]]

    # ------------------------------------------------------------------
    # 하이브리드 검색
    # ------------------------------------------------------------------

    def _vector_search(self, query: str) -> list[Chunk]:
        try:
            return self._index.vector_search(query, self._vector_k)
        except Exception as e:
            logger.error(f"벡터 검색 실패, 키워드 검색 결과만 사용합니다: {e}")
            return []

    def _adjust_for_time(self, scores: dict[str, float], chunks: dict[str, Chunk]) -> None:
        """끝난 이벤트는 빼고, 최근 문서는 점수를 높입니다."""
        today = self._today()
        for chunk_id in list(scores):
            meta = chunks[chunk_id].metadata
            period_end = _parse_date(meta.get("period_end"))
            if period_end and period_end < today:
                del scores[chunk_id]
                continue
            posted = _parse_date(meta.get("date"))
            period_start = _parse_date(meta.get("period_start"))
            ongoing = period_start is not None and period_start <= today and (period_end is None or today <= period_end)
            recent = posted is not None and today - posted <= timedelta(days=RECENT_DAYS)
            if ongoing or recent:
                scores[chunk_id] *= RECENT_BOOST

    def search(self, query: str, k: int = 5) -> list[Chunk]:
        """질의와 관련된 청크를 관련도 순으로 최대 k개 반환합니다."""
        try:
            keyword = self.keyword_search(query, self._keyword_k)
        except Exception as e:
            logger.error(f"키워드 검색 실패, 벡터 검색 결과만 사용합니다: {e}")
            keyword = []
        ranked_lists = [self._vector_search(query), keyword]

        scores: dict[str, float] = {}
        chunks: dict[str, Chunk] = {}
        for ranked in ranked_lists:
            for rank, chunk in enumerate(ranked):
                chunks[chunk.chunk_id] = chunk
                scores[chunk.chunk_id] = scores.get(chunk.chunk_id, 0.0) + 1.0 / (RRF_K + rank + 1)

        if is_time_sensitive(query):
            self._adjust_for_time(scores, chunks)

        best = sorted(scores, key=scores.get, reverse=True)[:k]
        return [chunks[chunk_id] for chunk_id in best]

    async def asearch(self, query: str, k: int = 5) -> list[Chunk]:
        """search를 스레드에서 실행합니다. (임베딩·DB 조회가 이벤트 루프를 막지 않도록)"""
        return await asyncio.to_thread(self.search, query, k)
