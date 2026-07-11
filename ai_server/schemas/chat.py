from pydantic import BaseModel


class QueryRequest(BaseModel):
    """챗 API 요청 스키마."""

    session_id: str
    message: str


class ChatResponse(BaseModel):
    """동기 챗 API 응답 스키마."""

    response: str
    thinking: str = ""
