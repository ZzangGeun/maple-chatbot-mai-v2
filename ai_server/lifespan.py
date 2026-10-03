# ai_server/lifespan.py
"""
AI 서버 생명주기(Lifespan) 관리 모듈

startup 시 critical 인프라 초기화 실패는 예외를 전파해 앱 기동을 중단합니다.
shutdown 시에는 모든 인프라를 순서대로 정리하며, 개별 실패가 나머지 정리를 막지 않습니다.

AI 서버는 대화 기록을 저장하지 않으므로(stateless) 체크포인터 없이 그래프를 빌드합니다.

Startup 핸들러:
  - Scheduler     : 공략 문서·넥슨 공지 지식 베이스 정기 적재를 가동합니다. (non-critical)
  - Observability : Langfuse 모니터링을 시작합니다. (non-critical)

Shutdown 핸들러:
  - Scheduler     : APScheduler를 안전하게 종료합니다.
  - Observability : 남은 모니터링 이벤트를 전송합니다.
"""

import inspect
import logging
from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager
from typing import Any, Awaitable, Union

from fastapi import FastAPI

from ai_server.common import observability
from ai_server.graph.builder.main_builder import build_main_graph

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


def _scheduler_startup() -> None:
    """공략 문서·공지 정기 적재 스케줄러를 가동합니다. (RAG_SYNC_INTERVAL_HOURS, 0이면 사용 안 함)"""
    global _scheduler

    from apscheduler.schedulers.asyncio import AsyncIOScheduler

    from ai_server.config import settings
    from ai_server.rag.ingest import run_scheduled_ingestion

    hours = settings.rag.sync_interval_hours
    if hours <= 0:
        logger.info("지식 베이스 정기 적재가 꺼져 있습니다. (RAG_SYNC_INTERVAL_HOURS=0)")
        return

    _scheduler = AsyncIOScheduler(timezone="Asia/Seoul")
    _scheduler.add_job(
        run_scheduled_ingestion,
        trigger="interval",
        hours=hours,
        id="knowledge_sync_job",
        name=f"{hours}시간마다 공략 문서·넥슨 공지 지식 베이스 적재",
        max_instances=1,
        coalesce=True,
    )
    _scheduler.start()


def _scheduler_shutdown() -> None:
    """APScheduler를 안전하게 종료합니다."""
    global _scheduler

    if _scheduler is not None:
        _scheduler.shutdown()
        _scheduler = None


def _observability_startup() -> None:
    """옵저버빌리티 모니터링 SDK를 연결 및 시작합니다."""
    observability.startup()


def _observability_shutdown() -> None:
    """옵저버빌리티 클라이언트 종료 및 남아있는 큐 데이터를 전송합니다."""
    observability.shutdown()


# ---------------------------------------------------------------------------
# 핸들러 등록 (이름, 함수, critical 여부)
# critical=True  : 실패 시 앱 기동을 중단합니다.
# critical=False : 실패해도 경고만 남기고 나머지 초기화를 계속합니다.
# ---------------------------------------------------------------------------
_STARTUP_HANDLERS: list[tuple[str, _HandlerFn, bool]] = [
    ("Scheduler", _scheduler_startup, False),
    ("Observability", _observability_startup, False),
]

_SHUTDOWN_HANDLERS: list[tuple[str, _HandlerFn]] = [
    ("Scheduler", _scheduler_shutdown),
    ("Observability", _observability_shutdown),
]


# ---------------------------------------------------------------------------
# Lifespan 컨텍스트 매니저
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """FastAPI 애플리케이션 라이프사이클 컨텍스트 매니저."""
    try:
        # 컴파일된 그래프를 FastAPI app.state에 바인딩
        app.state.graph = build_main_graph()
        logger.info("에이전트 그래프 빌드 및 앱 상태 바인딩 완료.")
    except Exception as e:
        logger.critical("그래프 초기화 중 치명적 에러 발생: %s", e, exc_info=True)
        raise

    await _startup()
    try:
        yield
    finally:
        await _shutdown()


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
