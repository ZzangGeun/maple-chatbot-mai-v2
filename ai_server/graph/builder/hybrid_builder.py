# ai_server/graph/builder/hybrid_builder.py
"""
하이브리드 에이전트 그래프 조립 모듈

그래프 흐름:
  START
    ↓
  [로컬 LLM] local_route_node (3-way 조건 분기)
    ↓               ↓                  ↓
 "local_rewrite" "character_lookup" "gemini_chat"
    ↓               ↓                  ↓
  [로컬] rewrite  [로컬] intent       [Gemini]
    ↓             extract             gemini_chat
  [로컬] retrieve   ↓                  ↓
    ↓             [API]              END
  [Gemini]        nexon_api
  gemini_rag        ↓
    ↓             [Gemini]
   END            gemini_rag (context = API 데이터)
                    ↓
                   END

설계 의도:
  - 로컬 LLM  → 라우팅, 엔티티 추출, 쿼리 재작성, RAG 검색 (전처리 에이전트)
  - 넥슨 API  → 실시간 캐릭터 전적 데이터 수집
  - Gemini    → 최종 고품질 답변 생성 (생성 에이전트)
  - gemini_generate_rag_node는 RAG 경로와 넥슨 API 경로 양쪽에서 재사용됩니다.
"""

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from ai_server.graph.nodes.gemini_nodes import (
    gemini_generate_chat_node,
    gemini_generate_rag_node,
)
from ai_server.graph.nodes.local_nodes import (
    local_intent_extract_node,
    local_retrieve_node,
    local_rewrite_node,
    local_route_node,
)
from ai_server.graph.nodes.nexon_nodes import nexon_api_tool_node
from ai_server.graph.state import GraphState


def build_hybrid_graph():
    """
    로컬 LLM + 넥슨 API + Gemini 하이브리드 StateGraph를 조립하고 컴파일합니다.

    Returns:
        컴파일된 CompiledGraph 객체 (MemorySaver 체크포인터 포함).
    """
    workflow = StateGraph(GraphState)

    # --- 노드 등록 ---

    # [로컬 LLM 노드] RAG 전처리 파이프라인
    workflow.add_node("local_rewrite", local_rewrite_node)
    workflow.add_node("local_retrieve", local_retrieve_node)

    # [로컬 LLM 노드] 캐릭터 전적 조회 전처리
    workflow.add_node("local_intent_extract", local_intent_extract_node)

    # [넥슨 API 노드] 실시간 캐릭터 정보 수집
    workflow.add_node("nexon_api", nexon_api_tool_node)

    # [Gemini 노드] 최종 답변 생성 (RAG 경로 + 넥슨 API 경로 공통 재사용)
    workflow.add_node("gemini_generate_rag", gemini_generate_rag_node)
    workflow.add_node("gemini_chat", gemini_generate_chat_node)

    # --- 엣지 연결 ---

    # START → local_route_node (3-way 조건 분기)
    workflow.add_conditional_edges(
        START,
        local_route_node,
        {
            "local_rewrite":    "local_rewrite",     # RAG 경로
            "character_lookup": "local_intent_extract",  # 캐릭터 전적 경로
            "gemini_chat":      "gemini_chat",        # 일반 대화 경로
        },
    )

    # [RAG 경로] 로컬 전처리 → Gemini 최종 생성
    workflow.add_edge("local_rewrite", "local_retrieve")
    workflow.add_edge("local_retrieve", "gemini_generate_rag")

    # [캐릭터 전적 경로] 로컬 엔티티 추출 → 넥슨 API 조회 → Gemini 최종 생성
    # nexon_api_tool_node가 state["context"]를 채우므로 gemini_generate_rag_node를 재사용합니다.
    workflow.add_edge("local_intent_extract", "nexon_api")
    workflow.add_edge("nexon_api", "gemini_generate_rag")

    # [공통] 최종 생성 → END
    workflow.add_edge("gemini_generate_rag", END)
    workflow.add_edge("gemini_chat", END)

    # MemorySaver: thread_id(세션) 단위로 대화 히스토리를 메모리에 유지합니다.
    memory = MemorySaver()
    return workflow.compile(checkpointer=memory)


# 모듈 import 시 한 번만 그래프를 조립합니다.
app_graph = build_hybrid_graph()
