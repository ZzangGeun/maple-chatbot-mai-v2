# ai_server/graph/state.py
"""
LangGraph 그래프 상태(State) 정의 모듈

GraphState를 한 곳에서 관리하여, 노드와 빌더가 같은 타입을 참조하도록 합니다.

ExtractedEntities 구조:
  - character_name : 캐릭터명 (넥슨 API 호출 키)
  - world          : 월드명 (스카니아, 베라 등)
  - item_name      : 아이템명 (장착 아이템 조회 시 사용)
"""

from typing import Annotated, List, Optional

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class ExtractedEntities(TypedDict, total=False):
    """
    로컬 LLM이 질문에서 추출한 메이플스토리 도메인 엔티티.

    total=False: 모든 필드가 선택적입니다.
    존재하지 않는 필드는 노드에서 .get()으로 안전하게 접근합니다.
    """

    character_name: str   # 캐릭터명 (넥슨 API 필수 키)
    world: str            # 월드명 (예: 스카니아, 베라, 리부트 등)
    item_name: str        # 아이템명


class GraphState(TypedDict):
    """챗봇 그래프 전체에서 공유되는 상태 타입."""

    # add_messages reducer: 메시지를 덮어쓰지 않고 누적합니다.
    messages: Annotated[List[BaseMessage], add_messages]
    # RAG 검색 결과 또는 넥슨 API 응답 컨텍스트 (최종 Gemini 노드에 주입)
    context: str
    # 재구성된 검색 쿼리
    query: str
    # 로컬 LLM이 추출한 캐릭터명/아이템명 등의 구조화된 엔티티
    extracted_entities: Optional[ExtractedEntities]
