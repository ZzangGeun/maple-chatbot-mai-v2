# ai_server/graph/state/nexon_state.py
"""
넥슨 API 서브 그래프 전용 상태 모듈.
메인 상태(MainState)를 상속받아 캐릭터/아이템 정보 조회에 필요한 필드를 추가합니다.
"""

from typing import Optional
from typing_extensions import TypedDict

from ai_server.graph.state.main_state import MainState


class ExtractedEntities(TypedDict, total=False):
    """
    로컬 LLM이 질문에서 추출한 메이플스토리 도메인 엔티티.

    total=False: 모든 필드가 선택적입니다.
    존재하지 않는 필드는 노드에서 .get()으로 안전하게 접근합니다.
    """

    character_name: str   # 캐릭터명 (넥슨 API 필수 키)
    world: str            # 월드명 (예: 스카니아, 베라, 리부트 등)
    item_name: str        # 아이템명


class NexonState(MainState):
    """넥슨 API 서브 그래프에서 사용하는 상태 타입."""

    # 로컬 LLM이 추출한 캐릭터명/아이템명 등의 구조화된 엔티티
    extracted_entities: Optional[ExtractedEntities]
    
    # 넥슨 API 응답 컨텍스트 (마크다운 포맷)
    context: str
