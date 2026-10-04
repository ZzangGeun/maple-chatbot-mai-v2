from fastapi import APIRouter, Depends, HTTPException, Request

from ai_server.api.deps import verify_internal_token
from ai_server.api.routes import chat, rag, user

api_router = APIRouter()

# 챗·AI 기능 라우터는 Django만 부르는 내부 API이므로 내부 호출 토큰을 검사합니다.
internal = [Depends(verify_internal_token)]

# 챗 관련 라우터는 루트 경로에 바로 바인딩 (원래 main.py와 동일하게 유지)
api_router.include_router(chat.router, tags=["chat"], dependencies=internal)

# RAG, User, 등 AI 기능 라우터는 /api/v1/ai 접두어를 사용
v1_ai_router = APIRouter(prefix="/api/v1/ai", dependencies=internal)
v1_ai_router.include_router(rag.router, tags=["rag"])
v1_ai_router.include_router(user.router, tags=["user"])

# 최종 병합
api_router.include_router(v1_ai_router)


@api_router.get("/health", tags=["health"])
async def health(request: Request) -> dict:
    """컨테이너 헬스체크용. 그래프가 준비되었는지만 확인합니다. (토큰 불필요)"""
    if getattr(request.app.state, "graph", None) is None:
        raise HTTPException(status_code=503, detail="starting")
    return {"status": "ok"}
