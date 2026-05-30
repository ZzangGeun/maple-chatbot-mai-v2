# ai_server/lifespan.py
"""
AI 서버 생명주기(Lifespan) 관리 모듈

FastAPI 서버의 시작(Startup) 및 종료(Shutdown) 시점에 실행될 작업을 정의합니다.
- 시작 시 로컬 LLM을 VRAM에 적재하고 초기 웜업(Warm-up)을 수행합니다.
- 시작 시 매일 새벽 4시에 캐릭터 데이터를 인덱싱하는 백그라운드 스케줄러를 구동합니다.
- 종료 시 백그라운드 스케줄러를 안전하게 닫습니다.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from apscheduler.schedulers.background import BackgroundScheduler
from ai_server.rag.character_batch import run_character_embedding_batch

logger = logging.getLogger("AI_Server_Lifespan")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI 서버의 생명주기 이벤트를 처리하는 비동기 컨텍스트 매니저.
    """
    # Startup 1: 로컬 LLM 사전 로딩 및 웜업 (Eager Loading & Warm-up)
    # 첫 사용자 질문 시 GPU CUDA 컨텍스트 초기화 등으로 인한 응답 지연을 완벽히 방지합니다.
    logger.info("🤖 로컬 LLM 모델 사전 적재를 시작합니다...")
    try:
        from ai_server.llm.llm_loader import get_local_llm
        local_llm = get_local_llm()
        logger.info("🤖 로컬 LLM 모델 적재 성공! CUDA 및 파이프라인 활성화를 위한 웜업을 진행합니다...")
        
        # 더미 질문을 실행하여 첫 번째 추론 지연을 미리 제거합니다.
        local_llm.invoke("안녕")
        logger.info("🤖 로컬 LLM 모델 웜업 완료!")
    except Exception as e:
        logger.error(f"🤖 로컬 LLM 모델 적재 및 웜업 중 실패 발생: {e}")

    # Startup 2: 백그라운드 스케줄러 가동 (새벽 4시 배치 작업)
    scheduler = BackgroundScheduler(timezone="Asia/Seoul")
    scheduler.add_job(
        run_character_embedding_batch,
        trigger="cron",
        hour=4,
        minute=0,
        id="character_embedding_job",
        name="매일 새벽 4시 캐릭터 데이터 pgvector 임베딩 적재"
    )
    scheduler.start()
    logger.info("⏰ 백그라운드 스케줄러가 성공적으로 시작되었습니다. (매일 04:00 실행)")
    
    yield
    
    # Shutdown: 서비스 종료 시 백그라운드 스케줄러를 안전하게 해제합니다.
    scheduler.shutdown()
    logger.info("⏰ 백그라운드 스케줄러가 안전하게 종료되었습니다.")
