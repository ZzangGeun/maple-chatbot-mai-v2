# ai_server/graph/builder/rag_builder.py
"""
RAG 서브 그래프 조립 모듈.
"""

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import RetryPolicy

from ai_server.graph.state.rag_state import RagState
from ai_server.graph.nodes.rag_nodes import gemini_rewrite_node, local_retrieve_node
from ai_server.graph.nodes.common_nodes import local_generate_rag_node

# LLM/외부 자원 호출 노드용 재시도 정책 — 일시적 네트워크/API 오류에 지수 백오프로 재시도합니다.
_retry_policy = RetryPolicy(max_attempts=3, initial_interval=0.5, backoff_factor=2.0)


def build_rag_graph() -> CompiledStateGraph:
    workflow = StateGraph(RagState)

    # 노드 등록 (LLM/검색 호출 노드는 재시도 정책 적용)
    workflow.add_node("gemini_rewrite", gemini_rewrite_node, retry_policy=_retry_policy)
    workflow.add_node("local_retrieve", local_retrieve_node, retry_policy=_retry_policy)
    workflow.add_node("local_generate", local_generate_rag_node, retry_policy=_retry_policy)

    # 엣지 연결
    workflow.add_edge(START, "gemini_rewrite")
    workflow.add_edge("gemini_rewrite", "local_retrieve")
    workflow.add_edge("local_retrieve", "local_generate")
    workflow.add_edge("local_generate", END)

    # 서브 그래프는 주로 메인 그래프의 Checkpointer를 상속받거나 공유하므로,
    # 여기서는 별도의 메모리 세이버를 달지 않고 컴파일합니다.
    return workflow.compile()

# 모듈 로드 시 조립 (필요 시 사용)
rag_graph = build_rag_graph()
