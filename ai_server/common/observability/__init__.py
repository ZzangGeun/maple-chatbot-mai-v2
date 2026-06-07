# -*- coding: utf-8 -*-
"""
옵저버빌리티(Observability) 패키지 진입점

외부 패키지 및 lifespan 진입 지점에서 client 내부 모듈을 거치지 않고
진입점 메서드들을 일관되게 임포트할 수 있도록 노출합니다.
"""

from ai_server.common.observability.client import (
    get_langfuse_callback,
    get_observability_client,
    shutdown,
    startup,
)

__all__ = [
    "get_observability_client",
    "get_langfuse_callback",
    "startup",
    "shutdown",
]
