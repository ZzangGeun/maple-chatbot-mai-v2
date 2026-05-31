# ai_server/graph/builder/main_builder.py
"""
메인 그래프 조립 모듈.
라우터를 통해 각 서브 그래프(RAG, Nexon) 또는 단일 노드(Chat)로 분기합니다.
"""

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from ai_server.graph.state.main_state import MainState
from ai_server.graph.nodes.route_nodes import gemini_route_node
from ai_server.graph.nodes.chat_nodes import gemini_chat_node

from ai_server.graph.builder.rag_builder import rag_graph
from ai_server.graph.builder.nexon_builder import nexon_graph


def build_main_graph(checkpointer: BaseCheckpointSaver | None = None) -> CompiledStateGraph:
    workflow = StateGraph(MainState)

    # 서브 그래프를 메인 그래프의 노드로 등록
    workflow.add_node("rag_graph", rag_graph)
    workflow.add_node("nexon_graph", nexon_graph)
    
    # 단일 노드(채팅) 등록
    workflow.add_node("chat_node", gemini_chat_node)

    # START -> 각 서브 그래프/노드로 조건부 라우팅
    workflow.add_conditional_edges(
        START,
        gemini_route_node,
        {
            "rag_graph": "rag_graph",
            "nexon_graph": "nexon_graph",
            "chat_node": "chat_node",
        }
    )

    # 서브 그래프 완료 -> END
    workflow.add_edge("rag_graph", END)
    workflow.add_edge("nexon_graph", END)
    workflow.add_edge("chat_node", END)

    # MemorySaver: thread_id 단위로 대화 히스토리를 유지
    if checkpointer is None:
        checkpointer = MemorySaver()
    return workflow.compile(checkpointer=checkpointer)

# 하위 호환 및 글로벌 참조용 (기본 메모리 세이버 사용)
app_graph = build_main_graph()
