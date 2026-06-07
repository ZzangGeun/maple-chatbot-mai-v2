import logging
from fastapi import APIRouter, Header

from ai_server.services.user import get_recommended_questions

logger = logging.getLogger("AI_Server.UserRouter")
router = APIRouter()

@router.get("/recommend-questions")
async def recommend_questions(authorization: str | None = Header(default=None)):
    """
    맞춤형 추천 질문 생성 API 엔드포인트.
    """
    character_name, recommended = get_recommended_questions(authorization)
    
    return {
        "success": True,
        "character_name": character_name,
        "recommended_questions": recommended,
    }
