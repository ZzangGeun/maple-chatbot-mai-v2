# ai_server/graph/state/nexon_state.py
"""
넥슨 API 서브 그래프 전용 상태 모듈.
메인 상태(MainState)를 상속받아 캐릭터 정보 조회에 필요한 필드를 추가합니다.
"""

from typing_extensions import TypedDict

from ai_server.graph.state.main_state import MainState


class CharacterQuery(TypedDict, total=False):
    """
    질문에서 추출한 캐릭터 조회 조건.

    total=False: 모든 필드가 선택적입니다.
    존재하지 않는 필드는 노드에서 .get()으로 안전하게 접근합니다.
    """

    character_name: str | None  # 조회할 캐릭터명 (질문 또는 직전 대화에서)
    refers_to_self: bool  # '내 캐릭터'처럼 사용자 본인의 캐릭터를 묻는지
    aspects: list[str]  # 필요한 정보 종류 (character_context.ASPECT_PATHS의 키)


class NexonState(MainState, total=False):
    """넥슨 API 서브 그래프에서 사용하는 상태 타입."""

    character_query: CharacterQuery


class NexonOutput(TypedDict, total=False):
    """넥슨 API 서브 그래프가 메인 그래프로 돌려주는 값."""

    character_context: str
