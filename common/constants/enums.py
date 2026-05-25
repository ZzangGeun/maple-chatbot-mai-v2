# common/constants/enums.py
"""
프로젝트 전역에서 사용하는 Enum 정의

하드코딩된 문자열 상수를 Enum으로 대체하여
오타 방지 및 자동완성을 지원합니다.
"""

from enum import Enum


class Role(str, Enum):
    """채팅 메시지의 역할 구분."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class MessageType(str, Enum):
    """SSE 스트리밍 이벤트 타입."""

    TOKEN = "token"
    ERROR = "error"
    DONE = "done"


class LlmProvider(str, Enum):
    """LLM 제공자 구분."""

    GEMINI = "gemini"
    LOCAL = "local"
    OPENAI = "openai"


class NoticeCategory(str, Enum):
    """Nexon 공지사항 카테고리."""

    GENERAL = "notice_general"
    EVENT = "notice_event"
    CASHSHOP = "notice_cashshop"
    UPDATE = "notice_update"
