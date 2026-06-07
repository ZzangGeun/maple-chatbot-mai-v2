# ai_server/main.py
"""
FastAPI AI 서버 진입점

엔드포인트 라우팅과 비즈니스 로직은 api/routes 및 services 디렉토리로 분리되었습니다.
"""

import logging
import uvicorn
from fastapi import FastAPI

from ai_server.api.router import api_router
from ai_server.lifespan import lifespan

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AI_Server")

app = FastAPI(title="MapleStory AI Server (LangGraph)", lifespan=lifespan)

# 모든 API 라우터를 등록합니다.
app.include_router(api_router)

if __name__ == "__main__":
    # 프로젝트 루트에서 실행해야 절대경로 import가 정상 동작합니다.
    # 실행 명령: python -m ai_server.main
    uvicorn.run(app, host="0.0.0.0", port=8001)
