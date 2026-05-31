# ai_server/graph/builder/rag_builder.py
"""
RAG 서브 그래프 조립 모듈.
"""

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from ai_server.graph.state.rag_state import RagState
from ai_server.graph.nodes.rag_nodes import gemini_rewrite_node, local_retrieve_node
from ai_server.graph.nodes.common_nodes import local_generate_rag_node


def build_rag_graph() -> CompiledStateGraph:
    workflow = StateGraph(RagState)

    # 노드 등록
    workflow.add_node("gemini_rewrite", gemini_rewrite_node)
    workflow.add_node("local_retrieve", local_retrieve_node)
    workflow.add_node("local_generate", local_generate_rag_node)

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
