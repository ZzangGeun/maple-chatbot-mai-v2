# ai_server/graph/builder/hybrid_builder.py
"""
하이브리드 에이전트 그래프 조립 모듈 (역할 반전 적용)

그래프 흐름:
  START
    ↓
  [Gemini] gemini_route_node (3-way 초고속 조건 분기)
    ↓               ↓                  ↓
 "gemini_rewrite" "gemini_intent_extract" "gemini_chat"
    ↓               ↓                  ↓
  [Gemini]        [Gemini]             END
  rewrite         intent_extract       
    ↓               ↓
  [로컬]          [API]
  retrieve        nexon_api
    ↓               ↓
  [로컬]          [로컬]
  local_generate_rag  local_generate_rag
    ↓               ↓
   END             END

설계 의도:
  - Gemini    → 빠른 라우팅, 엔티티 추출, 쿼리 재작성 (전처리 에이전트) 및 단순 대화
  - 넥슨 API  → 실시간 캐릭터 전적 데이터 수집
  - 로컬 LLM  → 깊이 있는 도메인 답변 생성 및 추론 (생성 에이전트)
  - local_generate_rag_node는 RAG 경로와 넥슨 API 경로 양쪽에서 재사용됩니다.
"""

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph


from ai_server.graph.nodes.gemini_nodes import (
    gemini_chat_node,
    gemini_intent_extract_node,
    gemini_rewrite_node,
    gemini_route_node,
)
from ai_server.graph.nodes.local_nodes import (
    local_generate_rag_node,
    local_retrieve_node,
)
from ai_server.graph.nodes.nexon_nodes import nexon_api_tool_node
from ai_server.graph.state import GraphState


def build_hybrid_graph(checkpointer: BaseCheckpointSaver | None = None) -> CompiledStateGraph:
    workflow = StateGraph(GraphState)

    # --- 노드 등록 ---

    # [Gemini 노드] 전처리 파이프라인
    workflow.add_node("gemini_rewrite", gemini_rewrite_node)
    workflow.add_node("gemini_intent_extract", gemini_intent_extract_node)
    workflow.add_node("gemini_chat", gemini_chat_node)

    # [로컬 LLM 노드] 검색 및 최종 도메인 답변 생성
    workflow.add_node("local_retrieve", local_retrieve_node)
    workflow.add_node("local_generate_rag", local_generate_rag_node)

    # [넥슨 API 노드] 실시간 캐릭터 정보 수집
    workflow.add_node("nexon_api", nexon_api_tool_node)

    # --- 엣지 연결 ---

    # START → gemini_route_node (3-way 조건 분기)
    workflow.add_conditional_edges(
        START,
        gemini_route_node,
        {
            "gemini_rewrite":        "gemini_rewrite",        # RAG 경로
            "gemini_intent_extract": "gemini_intent_extract", # 캐릭터 전적 경로
            "gemini_chat":           "gemini_chat",           # 일반 대화 경로
        },
    )

    # [RAG 경로] Gemini 전처리 → 로컬 RAG 답변
    workflow.add_edge("gemini_rewrite", "local_retrieve")
    workflow.add_edge("local_retrieve", "local_generate_rag")

    # [캐릭터 전적 경로] Gemini 전처리 → 넥슨 API 조회 → 로컬 RAG 답변
    workflow.add_edge("gemini_intent_extract", "nexon_api")
    workflow.add_edge("nexon_api", "local_generate_rag")

    # [공통] 최종 생성 → END
    workflow.add_edge("local_generate_rag", END)
    workflow.add_edge("gemini_chat", END)

    # MemorySaver: thread_id(세션) 단위로 대화 히스토리를 메모리에 유지합니다.
    if checkpointer is None:
        checkpointer = MemorySaver()
    return workflow.compile(checkpointer=checkpointer)


# 모듈 import 시 한 번만 그래프를 조립합니다. (기본 메모리 세이버 사용, 하위 호환용)
app_graph = build_hybrid_graph()

