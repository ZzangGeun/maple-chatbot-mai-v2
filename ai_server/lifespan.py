# ai_server/lifespan.py
"""
AI 서버 생명주기(Lifespan) 관리 모듈

startup 시 critical 인프라 초기화 실패는 예외를 전파해 앱 기동을 중단합니다.
shutdown 시에는 모든 인프라를 순서대로 정리하며, 개별 실패가 나머지 정리를 막지 않습니다.

Startup 핸들러:
  - LocalLLM    : 로컬 Qwen 모델을 VRAM에 적재합니다. (critical)
  - LLMWarmup   : 더미 추론을 실행해 CUDA 컨텍스트를 미리 워밍업합니다. (non-critical)
  - Scheduler   : 캐릭터 데이터 배치 임베딩 스케줄러를 가동합니다. (non-critical)

Shutdown 핸들러:
  - Scheduler   : APScheduler를 안전하게 종료합니다.
"""

import asyncio
import inspect
import logging
import os
from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager
from typing import Any, Awaitable, Union

from fastapi import FastAPI
from langgraph.checkpoint.redis.aio import AsyncRedisSaver
from ai_server.graph.builder.hybrid_builder import build_hybrid_graph

logger = logging.getLogger("AI_Server_Lifespan")


# ---------------------------------------------------------------------------
# 핸들러 타입 정의 (동기/비동기 모두 수용)
# ---------------------------------------------------------------------------
_HandlerFn = Callable[[], Union[Any, Awaitable[Any]]]

# ---------------------------------------------------------------------------
# 개별 startup / shutdown 함수
# ---------------------------------------------------------------------------

# APScheduler 인스턴스를 모듈 수준에서 관리하여 shutdown 시 참조할 수 있도록 합니다.
_scheduler = None


def _local_llm_startup() -> None:
    """로컬 LLM(Qwen)을 VRAM에 적재합니다."""
    from ai_server.llm.llm_loader import get_local_llm
    get_local_llm()


async def _llm_warmup_startup() -> None:
    """
    더미 추론을 실행하여 CUDA 컨텍스트와 파이프라인을 미리 활성화합니다.

    Thinking 모델은 max_new_tokens까지 토큰을 생성할 수 있으므로
    30초 타임아웃을 설정하여 서버 시작을 보장합니다.
    별도 스레드에서 실행하여 이벤트 루프 블로킹을 방지합니다.
    """
    from ai_server.llm.llm_loader import get_local_llm

    local_llm = get_local_llm()
    try:
        await asyncio.wait_for(
            asyncio.to_thread(local_llm.invoke, "안녕"),
            timeout=30,
        )
    except asyncio.TimeoutError:
        # 타임아웃은 치명적이지 않음 — 첫 요청 시 약간의 지연만 발생합니다.
        logger.warning(
            "LLM 웜업이 30초를 초과하여 건너뛰었습니다. "
            "첫 요청 시 약간의 지연이 발생할 수 있습니다."
        )


def _scheduler_startup() -> None:
    """캐릭터 데이터 배치 임베딩 스케줄러를 가동합니다."""
    global _scheduler

    from apscheduler.schedulers.background import BackgroundScheduler
    from ai_server.rag.character_batch import run_character_embedding_batch

    _scheduler = BackgroundScheduler(timezone="Asia/Seoul")
    _scheduler.add_job(
        run_character_embedding_batch,
        trigger="cron",
        hour=4,
        minute=0,
        id="character_embedding_job",
        name="매일 새벽 4시 캐릭터 데이터 pgvector 임베딩 적재",
    )
    _scheduler.start()


def _scheduler_shutdown() -> None:
    """APScheduler를 안전하게 종료합니다."""
    global _scheduler

    if _scheduler is not None:
        _scheduler.shutdown()
        _scheduler = None


# ---------------------------------------------------------------------------
# 핸들러 등록 (이름, 함수, critical 여부)
# critical=True  : 실패 시 앱 기동을 중단합니다.
# critical=False : 실패해도 경고만 남기고 나머지 초기화를 계속합니다.
# ---------------------------------------------------------------------------
_STARTUP_HANDLERS: list[tuple[str, _HandlerFn, bool]] = [
    ("LocalLLM", _local_llm_startup, True),
    ("LLMWarmup", _llm_warmup_startup, False),
    ("Scheduler", _scheduler_startup, False),
]

_SHUTDOWN_HANDLERS: list[tuple[str, _HandlerFn]] = [
    ("Scheduler", _scheduler_shutdown),
]


# ---------------------------------------------------------------------------
# Lifespan 컨텍스트 매니저
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """FastAPI 애플리케이션 라이프사이클 컨텍스트 매니저."""
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    logger.info("LangGraph 체크포인트를 위한 Redis 연결 시도: %s", redis_url)

    try:
        # AsyncRedisSaver를 비동기 컨텍스트 매니저로 사용하여 리소스를 안전하게 관리합니다.
        async with AsyncRedisSaver.from_conn_string(redis_url) as checkpointer:
            # Redis 인덱스 자동 생성
            await checkpointer.asetup()
            logger.info("LangGraph Redis Checkpointer (AsyncRedisSaver) 설정 완료.")

            # 컴파일된 그래프를 FastAPI app.state에 바인딩
            app.state.graph = build_hybrid_graph(checkpointer=checkpointer)
            logger.info("하이브리드 에이전트 그래프 빌드 및 앱 상태 바인딩 완료.")

            await _startup()
            yield
            await _shutdown()
    except Exception as e:
        logger.critical("Redis Checkpointer 또는 애플리케이션 초기화 중 치명적 에러 발생: %s", e, exc_info=True)
        raise



async def _startup() -> None:
    """등록된 startup 핸들러를 순서대로 실행합니다."""
    logger.info("=== Application startup sequence initiated ===")
    for name, fn, critical in _STARTUP_HANDLERS:
        try:
            result = fn()
            # 비동기 핸들러인 경우 await로 실행합니다.
            if inspect.isawaitable(result):
                await result
            logger.info("[%s] 초기화 완료", name)
        except Exception as e:
            if critical:
                logger.critical(
                    "[%s] startup 실패 (CRITICAL): %s", name, e, exc_info=True
                )
                raise
            logger.warning(
                "[%s] startup 실패 (non-critical): %s", name, e, exc_info=True
            )
    logger.info("=== Application startup sequence completed ===")


async def _shutdown() -> None:
    """등록된 shutdown 핸들러를 순서대로 실행합니다. 개별 실패가 나머지를 막지 않습니다."""
    logger.info("=== Application shutdown sequence initiated ===")
    for name, fn in _SHUTDOWN_HANDLERS:
        try:
            if fn is not None:
                result = fn()
                if inspect.isawaitable(result):
                    await result
                logger.info("[%s] 안전하게 종료됨", name)
        except Exception as e:
            logger.error("[%s] shutdown 실패: %s", name, e, exc_info=True)
    logger.info("=== Application shutdown sequence completed ===")
