# common/nexon/cache.py
"""
넥슨 Open API 응답 캐시 (Redis)

Django와 AI 서버가 같은 Redis를 바라보므로 한쪽에서 조회한 캐릭터 정보를 다른 쪽이 재사용합니다.

두 서버는 서로 다른 이벤트 루프에서 동작하므로(Django는 요청마다 루프가 바뀔 수 있음),
루프에 묶이지 않는 동기 redis 클라이언트를 스레드에서 호출합니다.
Redis에 연결할 수 없으면 캐시 없이 동작하고(fail-open), 잠시 동안은 재연결을 시도하지 않습니다.
"""

import asyncio
import json
import logging
import time
from datetime import timedelta
from typing import Any

import redis

logger = logging.getLogger(__name__)

KEY_PREFIX = "nexon:"
# Redis 장애 시 재연결을 다시 시도하기까지 기다리는 시간(초)
RETRY_AFTER_SECONDS = 60


class NexonCache:
    """넥슨 API 응답을 JSON으로 저장하는 Redis 캐시."""

    def __init__(self, redis_url: str = "", client: Any = None) -> None:
        """
        Args:
            redis_url: Redis 접속 주소. client를 넘기면 무시됩니다.
            client: get/setex를 제공하는 동기 Redis 클라이언트 (테스트용 주입).
        """
        self._client = client or redis.Redis.from_url(
            redis_url,
            decode_responses=True,
            socket_connect_timeout=1,
            socket_timeout=1,
        )
        self._disabled_until = 0.0

    def _available(self) -> bool:
        return time.monotonic() >= self._disabled_until

    def _disable(self, error: Exception) -> None:
        self._disabled_until = time.monotonic() + RETRY_AFTER_SECONDS
        logger.warning(
            f"Redis 캐시를 사용할 수 없어 {RETRY_AFTER_SECONDS}초 동안 캐시 없이 동작합니다: {error}"
        )

    async def get(self, key: str) -> Any | None:
        """캐시된 값을 반환합니다. 없거나 Redis 장애면 None."""
        if not self._available():
            return None
        try:
            raw = await asyncio.to_thread(self._client.get, KEY_PREFIX + key)
        except redis.RedisError as e:
            self._disable(e)
            return None
        if not raw:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return None

    async def set(self, key: str, value: Any, ttl: timedelta) -> None:
        """값을 ttl 동안 저장합니다. Redis 장애는 무시합니다."""
        if not self._available():
            return
        try:
            await asyncio.to_thread(
                self._client.setex,
                KEY_PREFIX + key,
                int(ttl.total_seconds()),
                json.dumps(value, ensure_ascii=False),
            )
        except redis.RedisError as e:
            self._disable(e)
