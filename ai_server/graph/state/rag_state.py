# ai_server/graph/state/rag_state.py
"""
RAG 서브 그래프 전용 상태 모듈.
메인 상태(MainState)를 상속받아 RAG 처리에 필요한 필드를 추가합니다.
"""

from ai_server.graph.state.main_state import MainState


class RagState(MainState):
    """RAG 서브 그래프에서 사용하는 상태 타입."""

    # 재구성된 검색 쿼리
    query: str
    
    # RAG 검색 결과 컨텍스트 (최종 Gemini 노드에 주입)
    context: str
