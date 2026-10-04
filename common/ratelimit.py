# common/ratelimit.py
"""
요청 횟수 제한 (고정 시간 창 방식)

Django 캐시에 '시간 창별 카운터'를 두고, 한도를 넘으면 거절합니다.
운영에서는 캐시가 Redis라 여러 워커·컨테이너가 같은 카운터를 공유합니다.

한도 표기: "20/m,300/d" → 1분에 20회, 하루에 300회 (단위: s, m, h, d)
"""

import logging
import time
from dataclasses import dataclass

from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

_UNIT_SECONDS = {"s": 1, "m": 60, "h": 3600, "d": 86400}


@dataclass(frozen=True)
class RateLimit:
    limit: int
    seconds: int


def parse_rate_limits(spec: str) -> list[RateLimit]:
    """'20/m,300/d' 형식을 RateLimit 목록으로 바꿉니다. 비어 있으면 제한하지 않습니다."""
    limits = []
    for part in (spec or "").split(","):
        part = part.strip()
        if not part:
            continue
        count, _, unit = part.partition("/")
        limits.append(RateLimit(limit=int(count), seconds=_UNIT_SECONDS[unit.strip().lower()]))
    return limits


async def ahit(scope: str, ident: str, limits: list[RateLimit]) -> bool:
    """요청 1회를 기록합니다. 모든 한도 안이면 True, 하나라도 넘으면 False."""
    now = time.time()
    allowed = True
    for rule in limits:
        key = f"ratelimit:{scope}:{ident}:{rule.seconds}:{int(now // rule.seconds)}"
        await cache.aadd(key, 0, timeout=rule.seconds)
        try:
            count = await cache.aincr(key)
        except ValueError:
            # aadd와 aincr 사이에 키가 만료된 경우
            await cache.aset(key, 1, timeout=rule.seconds)
            count = 1
        if count > rule.limit:
            allowed = False
    return allowed


def client_ip(request) -> str:
    """요청한 클라이언트 IP. 리버스 프록시 뒤에서는 프록시가 넣은 X-Real-IP를 사용합니다."""
    if getattr(settings, "TRUST_X_REAL_IP", False):
        real_ip = request.META.get("HTTP_X_REAL_IP", "").strip()
        if real_ip:
            return real_ip
    return request.META.get("REMOTE_ADDR", "unknown")
