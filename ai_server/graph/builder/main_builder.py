# ai_server/graph/builder/main_builder.py
"""
메인 그래프 조립 모듈.

route(질문 분류) → [knowledge | character | 둘 다 병렬 | 바로 생성] → generate(답변 생성)

AI 서버는 대화 기록을 저장하지 않으므로(stateless) 체크포인터 없이 컴파일합니다.
이전 대화는 매 요청마다 Django가 messages로 전달합니다.
"""

from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from ai_server.graph.builder.nexon_builder import nexon_graph
from ai_server.graph.builder.rag_builder import rag_graph
from ai_server.graph.nodes.generate_nodes import generate_node
from ai_server.graph.nodes.route_nodes import route_node, select_branches
from ai_server.graph.state.main_state import MainState

# 서브 그래프는 노드 함수 안에서 호출합니다.
# 컴파일된 서브 그래프를 노드로 직접 등록하면 astream_events 실행 시 output_schema가 무시되어,
# 병렬 분기(character_knowledge)에서 두 서브 그래프가 공용 키(user_context 등)를
# 같은 스텝에 다시 쓰면서 InvalidUpdateError가 발생합니다.
# 노드 함수에서 ainvoke하면 output_schema에 정의된 키만 반환되고, 내부 노드 이벤트도 그대로 전달됩니다.


async def knowledge_node(state: MainState, config: RunnableConfig) -> dict:
    """지식 검색(RAG) 서브 그래프를 실행합니다."""
    return await rag_graph.ainvoke(state, config)


async def character_node(state: MainState, config: RunnableConfig) -> dict:
    """캐릭터 정보 조회(넥슨 API) 서브 그래프를 실행합니다."""
    return await nexon_graph.ainvoke(state, config)


def build_main_graph() -> CompiledStateGraph:
    workflow = StateGraph(MainState)

    workflow.add_node("route", route_node)
    workflow.add_node("knowledge", knowledge_node)
    workflow.add_node("character", character_node)
    workflow.add_node("generate", generate_node)

    workflow.add_edge(START, "route")
    # 분류 결과에 따라 하나 또는 두 개(병렬)의 분기로 이동합니다.
    workflow.add_conditional_edges(
        "route", select_branches, ["knowledge", "character", "generate"]
    )
    # 병렬 분기는 같은 스텝에 끝나므로 generate는 한 번만 실행됩니다.
    workflow.add_edge("knowledge", "generate")
    workflow.add_edge("character", "generate")
    workflow.add_edge("generate", END)

    return workflow.compile()
