# ai_server/graph/builder/rag_builder.py
"""
RAG 서브 그래프 조립 모듈.

rewrite(질문 재작성) → retrieve(문서 검색)를 실행하고,
output_schema(RagOutput)에 정의된 knowledge_context와 sources만 메인 그래프로 돌려줍니다.
"""

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from ai_server.graph.nodes.rag_nodes import retrieve_node, rewrite_node
from ai_server.graph.state.rag_state import RagOutput, RagState


def build_rag_graph() -> CompiledStateGraph:
    workflow = StateGraph(RagState, output_schema=RagOutput)

    workflow.add_node("rewrite", rewrite_node)
    workflow.add_node("retrieve", retrieve_node)

    workflow.add_edge(START, "rewrite")
    workflow.add_edge("rewrite", "retrieve")
    workflow.add_edge("retrieve", END)

    return workflow.compile()


# 모듈 로드 시 조립
rag_graph = build_rag_graph()
