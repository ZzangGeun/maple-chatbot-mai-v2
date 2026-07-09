# ai_server/graph/builder/nexon_builder.py
"""
넥슨 API 서브 그래프 조립 모듈.
"""

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import RetryPolicy

from ai_server.graph.state.nexon_state import NexonState
from ai_server.graph.nodes.nexon_nodes import gemini_intent_extract_node, nexon_api_tool_node
from ai_server.graph.nodes.common_nodes import local_generate_rag_node

# LLM/외부 API 호출 노드용 재시도 정책 — 일시적 네트워크/API 오류에 지수 백오프로 재시도합니다.
_retry_policy = RetryPolicy(max_attempts=3, initial_interval=0.5, backoff_factor=2.0)


def build_nexon_graph() -> CompiledStateGraph:
    workflow = StateGraph(NexonState)

    # 노드 등록 (LLM/외부 API 호출 노드는 재시도 정책 적용)
    workflow.add_node("gemini_intent_extract", gemini_intent_extract_node, retry_policy=_retry_policy)
    workflow.add_node("nexon_api", nexon_api_tool_node, retry_policy=_retry_policy)
    workflow.add_node("local_generate", local_generate_rag_node, retry_policy=_retry_policy)

    # 엣지 연결
    workflow.add_edge(START, "gemini_intent_extract")
    workflow.add_edge("gemini_intent_extract", "nexon_api")
    workflow.add_edge("nexon_api", "local_generate")
    workflow.add_edge("local_generate", END)

    return workflow.compile()

# 모듈 로드 시 조립
nexon_graph = build_nexon_graph()
