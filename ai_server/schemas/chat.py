from typing import Literal

from pydantic import BaseModel, Field


class HistoryMessage(BaseModel):
    """이전 대화 메시지 (Django가 오래된 순으로 전달)."""

    role: Literal["user", "assistant"]
    content: str


class MainCharacter(BaseModel):
    """사용자의 대표 캐릭터 정보."""

    character_name: str
    world_name: str | None = None
    ocid: str | None = None


class UserContext(BaseModel):
    """Django가 전달하는 사용자 정보. 비로그인 사용자는 비어 있습니다."""

    main_character: MainCharacter | None = None


class QueryRequest(BaseModel):
    """챗 API 요청 스키마."""

    session_id: str
    message: str = Field(min_length=1)
    history: list[HistoryMessage] = Field(default_factory=list)
    user_context: UserContext | None = None


class Source(BaseModel):
    """답변 근거 문서. index는 답변 본문의 [n] 표시와 대응합니다."""

    index: int
    title: str
    url: str = ""
    category: str = ""
    date: str = ""


class ChatResponse(BaseModel):
    """동기 챗 API 응답 스키마."""

    response: str
    route: str = ""
    sources: list[Source] = Field(default_factory=list)
