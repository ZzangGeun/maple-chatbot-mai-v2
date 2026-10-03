# ai_server/graph/builder/nexon_builder.py
"""
넥슨 API 서브 그래프 조립 모듈.

extract_character(캐릭터명 추출) → fetch_character(넥슨 Open API 조회)를 실행하고,
output_schema(NexonOutput)에 정의된 character_context만 메인 그래프로 돌려줍니다.
"""

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from ai_server.graph.nodes.nexon_nodes import (
    extract_character_node,
    fetch_character_node,
)
from ai_server.graph.state.nexon_state import NexonOutput, NexonState


def build_nexon_graph() -> CompiledStateGraph:
    workflow = StateGraph(NexonState, output_schema=NexonOutput)

    workflow.add_node("extract_character", extract_character_node)
    workflow.add_node("fetch_character", fetch_character_node)

    workflow.add_edge(START, "extract_character")
    workflow.add_edge("extract_character", "fetch_character")
    workflow.add_edge("fetch_character", END)

    return workflow.compile()


# 모듈 로드 시 조립
nexon_graph = build_nexon_graph()
