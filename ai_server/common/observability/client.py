# -*- coding: utf-8 -*-
"""
Langfuse 기반 옵저버빌리티 클라이언트 구현 모듈

Langfuse SDK를 사용한 애플리케이션 모니터링 클라이언트를 구현하며,
환경변수를 수동 바인딩하여 Langfuse SDK 초기화 타이밍을 조율합니다.
"""

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING

from ai_server.common.observability.base import BaseObservabilityClient
from ai_server.config import settings

if TYPE_CHECKING:
    from langchain_core.callbacks import BaseCallbackHandler

logger = logging.getLogger("ObservabilityClient")

# 모듈 로드 시점에 환경변수 세팅
# Langfuse SDK는 import 혹은 get_client() 호출 시점에 환경변수를 캐싱하므로,
# 관련 설정 인스턴스에서 읽어와 프로세스 레벨 환경변수에 먼저 밀어넣어 바인딩을 보장해야 합니다.
if settings.langfuse.enabled:
    os.environ["LANGFUSE_PUBLIC_KEY"] = settings.langfuse.public_key or ""
    os.environ["LANGFUSE_SECRET_KEY"] = settings.langfuse.secret_key or ""
    os.environ["LANGFUSE_HOST"] = settings.langfuse.base_url or ""


class LangfuseClient(BaseObservabilityClient):
    """Langfuse 기반 LLM 옵저버빌리티 클라이언트.

    설정 상 비활성화되어 있거나 Langfuse 패키지가 미설치된 환경에서는 
    예외 없이 안전하게 무동작(None 반환 및 패스)하도록 예외 차단 설계를 적용했습니다.
    """

    def startup(self) -> None:
        """Langfuse SDK를 구동하고 서버와의 기초 통신을 타임아웃 검증합니다.
        
        애플리케이션 가동 시점에 딱 1회 호출되어 로깅 인스턴스를 초기화합니다.
        """
        if not settings.langfuse.enabled:
            logger.info("[Langfuse] 활성화 설정(enabled=False)이 꺼져 있어 관측 클라이언트를 구동하지 않습니다.")
            return
        try:
            from langfuse import get_client

            get_client()  # SDK 로드 및 최초 계정 세션 초기화
            logger.info("[Langfuse] 모니터링 클라이언트 연결 및 SDK 구동 완료.")
        except Exception as e:
            logger.warning("[Langfuse] SDK 초기화 실패 (모니터링 없이 서버는 구동됩니다): %s", e)

    def shutdown(self) -> None:
        """Langfuse 백그라운드 큐에 저장되어 있는 모든 추적(Trace) 이벤트들을 
        원격 수집기 서버로 비동기 플러시(flush)합니다.
        """
        if not settings.langfuse.enabled:
            return
        try:
            from langfuse import get_client

            get_client().flush()
            logger.info("[Langfuse] 미전송된 모니터링 이벤트를 성공적으로 플러시(flush) 완료했습니다.")
        except Exception as e:
            logger.warning("[Langfuse] 이벤트 플러시 실패: %s", e)

    def get_callback(self) -> BaseCallbackHandler | None:
        """LangChain의 각 LLM/Chain/Graph 동작에 부착할 CallbackHandler를 생성합니다.
        
        Returns:
            Langfuse CallbackHandler 인스턴스. 비활성화 시 None 반환.
        """
        if not settings.langfuse.enabled:
            return None
        try:
            # langfuse.langchain은 langfuse SDK 모듈 내 의존성이 필요하므로 지연 로딩 처리합니다.
            from langfuse.langchain import CallbackHandler

            return CallbackHandler()
        except Exception as e:
            logger.warning("[Langfuse] CallbackHandler 생성 중 에러 발생: %s", e)
            return None


# 패키지 레벨 싱글톤 객체
_client = LangfuseClient()


def get_observability_client() -> BaseObservabilityClient:
    """초기화된 옵저버빌리티 싱글톤 클라이언트를 반환합니다."""
    return _client


def startup() -> None:
    """옵저버빌리티 모니터링을 시작합니다. lifespan.py에서 호출되도록 의도되었습니다."""
    _client.startup()


def shutdown() -> None:
    """옵저버빌리티를 안전하게 닫습니다. lifespan.py에서 호출되도록 의도되었습니다."""
    _client.shutdown()


def get_langfuse_callback() -> BaseCallbackHandler | None:
    """LangChain 콜백 핸들러를 획득하기 위한 단축 헬퍼 메서드."""
    return _client.get_callback()
