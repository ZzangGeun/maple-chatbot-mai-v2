# ai_server/graph/state/rag_state.py
"""
RAG 서브 그래프 전용 상태 모듈.
메인 상태(MainState)를 상속받아 RAG 처리에 필요한 필드를 추가합니다.
"""

from typing import Any

from typing_extensions import TypedDict

from ai_server.graph.state.main_state import MainState


class RagState(MainState, total=False):
    """RAG 서브 그래프에서 사용하는 상태 타입."""

    # 재구성된 검색 쿼리
    query: str


class RagOutput(TypedDict, total=False):
    """RAG 서브 그래프가 메인 그래프로 돌려주는 값."""

    knowledge_context: str
    sources: list[dict[str, Any]]
