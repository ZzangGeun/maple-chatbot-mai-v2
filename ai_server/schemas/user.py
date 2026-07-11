# ai_server/schemas/user.py
"""사용자 관련 API 요청/응답 스키마."""

from pydantic import BaseModel


class RecommendedQuestion(BaseModel):
    """추천 질문 단일 항목."""

    id: str
    question: str
    category: str


class RecommendQuestionsResponse(BaseModel):
    """맞춤형 추천 질문 응답 스키마."""

    success: bool = True
    character_name: str
    recommended_questions: list[RecommendedQuestion]
