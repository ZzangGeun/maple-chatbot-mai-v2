import logging
from typing import Annotated

from fastapi import APIRouter, Depends

from ai_server.api.deps import get_character_name
from ai_server.schemas.user import RecommendQuestionsResponse
from ai_server.services.user import build_recommended_questions

logger = logging.getLogger("AI_Server.UserRouter")
router = APIRouter()


@router.get("/recommend-questions", response_model=RecommendQuestionsResponse)
async def recommend_questions(
    character_name: Annotated[str, Depends(get_character_name)],
) -> RecommendQuestionsResponse:
    """
    맞춤형 추천 질문 생성 API 엔드포인트.

    JWT 토큰에서 추출한 대표 캐릭터명을 기반으로 추천 질문을 구성합니다.
    """
    recommended = build_recommended_questions(character_name)

    return RecommendQuestionsResponse(
        character_name=character_name,
        recommended_questions=recommended,
    )
