# ai_server/rag/evaluation/retrieval_eval.py
"""
검색 품질 평가 (LLM 호출 없음)

testset.json의 질문마다 정답 문서(expected_doc_ids)가 검색 결과 상위에 나오는지 측정합니다.
    hit@1, hit@k : 정답 문서가 1위 / k위 안에 있는 질문 비율
    MRR          : 정답 문서 순위의 역수 평균

    python -m ai_server.rag.evaluation.retrieval_eval                 # 메모리 인덱스, 키워드 검색만
    python -m ai_server.rag.evaluation.retrieval_eval --index pg      # 운영 인덱스 (pgvector + 키워드)
    python -m ai_server.rag.evaluation.retrieval_eval --verbose       # 틀린 질문 목록 출력

메모리 인덱스는 임베딩 모델 없이 공략 문서(초안 포함)를 적재해 키워드 검색 경로만 평가합니다.
검색 방식이나 공략 문서를 바꿀 때 변경 전후 수치를 비교하세요.
"""

import argparse
import json
from dataclasses import dataclass, field
from pathlib import Path

from ai_server.config import settings
from ai_server.rag.index import InMemoryIndex
from ai_server.rag.ingest import sync_documents
from ai_server.rag.retriever import HybridRetriever
from ai_server.rag.sources import load_guides

TESTSET_PATH = Path(__file__).with_name("testset.json")


@dataclass
class EvalResult:
    total: int = 0
    hit_at_1: float = 0.0
    hit_at_k: float = 0.0
    mrr: float = 0.0
    misses: list[dict] = field(default_factory=list)

    def __str__(self) -> str:
        return (
            f"질문 {self.total}개 | hit@1 {self.hit_at_1:.2%} | hit@k {self.hit_at_k:.2%} | MRR {self.mrr:.3f}"
        )


def load_testset(path: Path = TESTSET_PATH) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def evaluate(retriever: HybridRetriever, testset: list[dict], k: int = 5) -> EvalResult:
    """질문마다 검색해 정답 문서의 순위를 집계합니다. (같은 문서의 청크는 한 번만 셉니다)"""
    result = EvalResult(total=len(testset))
    hits_1 = hits_k = reciprocal_sum = 0.0

    for case in testset:
        expected = set(case["expected_doc_ids"])
        doc_ids: list[str] = []
        for chunk in retriever.search(case["question"], k=k * 3):
            if chunk.doc_id not in doc_ids:
                doc_ids.append(chunk.doc_id)
        doc_ids = doc_ids[:k]

        rank = next((i + 1 for i, doc_id in enumerate(doc_ids) if doc_id in expected), None)
        if rank == 1:
            hits_1 += 1
        if rank:
            hits_k += 1
            reciprocal_sum += 1 / rank
        else:
            result.misses.append({"question": case["question"], "expected": sorted(expected), "got": doc_ids})

    if testset:
        result.hit_at_1 = hits_1 / len(testset)
        result.hit_at_k = hits_k / len(testset)
        result.mrr = reciprocal_sum / len(testset)
    return result


def build_memory_retriever(guides_dir: Path | None = None) -> HybridRetriever:
    """공략 문서(초안 포함)를 메모리 인덱스에 적재한 키워드 검색 전용 검색기를 만듭니다."""
    index = InMemoryIndex()
    sync_documents(index, load_guides(guides_dir or Path(settings.rag.guides_dir), include_drafts=True))
    return HybridRetriever(index)


def main() -> None:
    parser = argparse.ArgumentParser(description="RAG 검색 품질 평가")
    parser.add_argument("--index", choices=["memory", "pg"], default="memory")
    parser.add_argument("--k", type=int, default=5)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    if args.index == "pg":
        from ai_server.rag.vectorstore import get_index

        retriever = HybridRetriever(get_index())
    else:
        retriever = build_memory_retriever()

    result = evaluate(retriever, load_testset(), k=args.k)
    print(result)
    if args.verbose:
        for miss in result.misses:
            print(f"  ✗ {miss['question']} | 정답 {miss['expected']} | 결과 {miss['got']}")


if __name__ == "__main__":
    main()
