from fastapi import APIRouter

from ai_server.api.routes import chat, rag, user

api_router = APIRouter()

# 챗 관련 라우터는 루트 경로에 바로 바인딩 (원래 main.py와 동일하게 유지)
api_router.include_router(chat.router, tags=["chat"])

# RAG, User, 등 AI 기능 라우터는 /api/v1/ai 접두어를 사용
v1_ai_router = APIRouter(prefix="/api/v1/ai")
v1_ai_router.include_router(rag.router, tags=["rag"])
v1_ai_router.include_router(user.router, tags=["user"])

# 최종 병합
api_router.include_router(v1_ai_router)
