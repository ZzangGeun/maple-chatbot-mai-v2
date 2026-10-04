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
    # 워커는 1개로 고정합니다. 임베딩 모델·검색 인덱스·스케줄러를 프로세스마다 따로 띄우지 않기 위해서입니다.
    # (uvicorn은 WEB_CONCURRENCY 환경 변수를 워커 수로 읽는데, 이 값은 Django 워커 수 용도입니다)
    uvicorn.run(app, host="0.0.0.0", port=8001, workers=1)
