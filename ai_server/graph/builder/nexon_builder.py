# ai_server/graph/builder/nexon_builder.py
"""
넥슨 API 서브 그래프 조립 모듈.
"""

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from ai_server.graph.state.nexon_state import NexonState
from ai_server.graph.nodes.nexon_nodes import gemini_intent_extract_node, nexon_api_tool_node
from ai_server.graph.nodes.common_nodes import local_generate_rag_node


def build_nexon_graph() -> CompiledStateGraph:
    workflow = StateGraph(NexonState)

    # 노드 등록
    workflow.add_node("gemini_intent_extract", gemini_intent_extract_node)
    workflow.add_node("nexon_api", nexon_api_tool_node)
    workflow.add_node("local_generate", local_generate_rag_node)

    # 엣지 연결
    workflow.add_edge(START, "gemini_intent_extract")
    workflow.add_edge("gemini_intent_extract", "nexon_api")
    workflow.add_edge("nexon_api", "local_generate")
    workflow.add_edge("local_generate", END)

    return workflow.compile()

# 모듈 로드 시 조립
nexon_graph = build_nexon_graph()
