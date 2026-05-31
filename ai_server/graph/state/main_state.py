# ai_server/graph/state/main_state.py
"""
메인 그래프 상태 모듈.
모든 서브 그래프가 공통으로 참조할 수 있는 기본 상태를 정의합니다.
"""

from typing import Annotated, List
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class MainState(TypedDict):
    """메인 챗봇 그래프 전체에서 공유되는 기본 상태 타입."""

    # add_messages reducer: 메시지를 덮어쓰지 않고 누적합니다.
    messages: Annotated[List[BaseMessage], add_messages]
