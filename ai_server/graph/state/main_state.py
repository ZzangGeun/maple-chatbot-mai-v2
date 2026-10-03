# ai_server/graph/state/main_state.py
"""
메인 그래프 상태 모듈.
모든 서브 그래프가 공통으로 참조할 수 있는 기본 상태를 정의합니다.

AI 서버는 대화 기록을 저장하지 않습니다(stateless).
매 요청마다 Django가 보낸 최근 대화와 사용자 정보로 상태를 새로 구성합니다.
"""

from typing import Annotated, Any, Literal

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

# 질문 분류 결과
#   chat               : 인사/잡담
#   knowledge          : 게임 지식 검색 (RAG)
#   character          : 캐릭터 정보 조회 (넥슨 Open API)
#   character_knowledge: 캐릭터 정보 + 게임 지식 (두 서브 그래프 병렬 실행)
Route = Literal["chat", "knowledge", "character", "character_knowledge"]


class MainState(TypedDict, total=False):
    """메인 챗봇 그래프 전체에서 공유되는 상태 타입."""

    # 이전 대화 + 현재 질문. add_messages reducer로 생성된 답변이 누적됩니다.
    messages: Annotated[list[BaseMessage], add_messages]

    # Django가 전달한 사용자 정보 (예: {"main_character": {"character_name": "...", "world_name": "..."}})
    user_context: dict[str, Any]

    # 질문 분류 결과
    route: Route

    # 지식 검색 결과 컨텍스트와 근거 문서 목록 (RAG 서브 그래프가 채웁니다)
    knowledge_context: str
    sources: list[dict[str, Any]]

    # 캐릭터 정보 컨텍스트 (넥슨 API 서브 그래프가 채웁니다)
    character_context: str
