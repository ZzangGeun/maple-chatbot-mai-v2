# tests/test_core_services.py
"""Redis 장애 중 공지·랭킹 캐시의 대체 저장소와 재연결 동작을 검증합니다.

Redis와 넥슨 API는 대역으로 교체하며, 만료·재시도 시간은 가짜 시계로 진행합니다.
"""

import json
import logging
from threading import Lock
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, call

import pytest
import redis
from django.core.cache.backends import base as cache_base
from django.core.cache.backends import locmem as cache_locmem

from apps.core import services


class _Clock:
    """다른 이벤트 루프의 시계에 영향을 주지 않는 테스트용 시계입니다."""

    def __init__(self) -> None:
        self.now = 1000.0

    def monotonic(self) -> float:
        return self.now

    def time(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


@pytest.fixture(autouse=True)
def cache_state(monkeypatch: pytest.MonkeyPatch):
    """각 테스트의 캐시·장애 상태를 격리하고 실제 네트워크 호출을 금지합니다."""
    clock = _Clock()
    client = Mock()
    client.get.return_value = None
    client.setex.return_value = True
    api = AsyncMock(side_effect=AssertionError("넥슨 API 대역을 설정해야 합니다."))

    monkeypatch.setattr(services, "time", clock)
    monkeypatch.setattr(cache_base, "time", clock)
    monkeypatch.setattr(cache_locmem, "time", clock)
    monkeypatch.setattr(services, "redis_client", client)
    monkeypatch.setattr(services, "get_api_data", api)
    monkeypatch.setattr(services, "_redis_retry_at", 0.0)
    monkeypatch.setattr(services, "_redis_state_lock", Lock())
    services._fallback_cache.clear()

    yield SimpleNamespace(clock=clock, redis=client, api=api)

    services._fallback_cache.clear()


def test_notice_api_returns_data_and_reuses_cache_when_redis_is_down(cache_state) -> None:
    """Redis 연결이 끊겨도 공지를 반환하고 재조회에서 API 요청을 반복하지 않습니다."""
    cache_state.redis.get.side_effect = redis.ConnectionError("연결 거부")
    notice_parts = [
        {"notice": [{"title": "일반 공지"}]},
        {"event_notice": [{"title": "이벤트 공지"}]},
        {"cashshop_notice": [{"title": "캐시샵 공지"}]},
        {"update_notice": [{"title": "업데이트 공지"}]},
    ]
    cache_state.api.side_effect = notice_parts

    first = services.get_notice_list()
    second = services.get_notice_list()

    assert first == {
        "notice_general": notice_parts[0],
        "notice_event": notice_parts[1],
        "notice_cashshop": notice_parts[2],
        "notice_update": notice_parts[3],
    }
    assert second == first
    assert cache_state.api.await_args_list == [
        call("/notice"), call("/notice-event"),
        call("/notice-cashshop"), call("/notice-update"),
    ]
    cache_state.redis.get.assert_called_once_with("cache:notice_list")
    cache_state.redis.setex.assert_not_called()


def test_ranking_api_returns_top_50_and_reuses_cache_when_redis_is_down(cache_state) -> None:
    cache_state.redis.get.side_effect = redis.ConnectionError("연결 거부")
    rankings = [{"ranking": i, "character_name": f"캐릭터{i}"} for i in range(1, 61)]
    cache_state.api.side_effect = None
    cache_state.api.return_value = {"ranking": rankings}

    first = services.get_ranking_list()
    second = services.get_ranking_list()

    assert first == {"overall_ranking": rankings[:50]}
    assert second == first
    cache_state.api.assert_awaited_once_with("/ranking/overall")
    cache_state.redis.get.assert_called_once_with("cache:ranking_list")
    cache_state.redis.setex.assert_not_called()


@pytest.mark.parametrize("data", [{"value": "Redis 데이터"}, [{"value": 1}]])
def test_valid_redis_hit_takes_priority_over_local_fallback(cache_state, data) -> None:
    services.save_data_to_redis("key", {"value": "대체 데이터"})
    cache_state.redis.get.return_value = json.dumps(data, ensure_ascii=False)

    assert services.load_data_from_redis("key") == data
    cache_state.redis.get.assert_called_once_with("key")
    cache_state.api.assert_not_awaited()


def test_redis_miss_returns_locally_saved_data(cache_state) -> None:
    data = {"title": "메이플 공지"}

    services.save_data_to_redis("key", data)

    cache_state.redis.setex.assert_called_once_with(
        "key", services.CACHE_DURATION, json.dumps(data, ensure_ascii=False)
    )
    assert services.load_data_from_redis("key") == data


def test_read_failure_pauses_reads_and_writes_then_recovers(cache_state, caplog) -> None:
    """첫 읽기 장애 이후에는 연결을 유예하고, 유예 시간이 끝나면 Redis를 다시 읽습니다."""
    caplog.set_level(logging.WARNING, logger=services.logger.name)
    fallback = {"value": "대체 데이터"}
    recovered = {"value": "복구된 Redis 데이터"}
    services.save_data_to_redis("key", fallback)
    cache_state.redis.setex.reset_mock()
    cache_state.redis.get.side_effect = [
        redis.ConnectionError("연결 거부"), json.dumps(recovered),
    ]

    assert services.load_data_from_redis("key") == fallback
    services.save_data_to_redis("second-key", {"value": 2})
    cache_state.clock.advance(services.REDIS_RETRY_AFTER_SECONDS - 1)
    assert services.load_data_from_redis("key") == fallback
    cache_state.redis.get.assert_called_once_with("key")
    cache_state.redis.setex.assert_not_called()

    cache_state.clock.advance(1)
    assert services.load_data_from_redis("key") == recovered
    assert cache_state.redis.get.call_count == 2
    warnings = [record for record in caplog.records if record.name == services.logger.name]
    assert len(warnings) == 1


def test_write_failure_keeps_fallback_and_resumes_after_cooldown(cache_state, caplog) -> None:
    caplog.set_level(logging.WARNING, logger=services.logger.name)
    cache_state.redis.setex.side_effect = [redis.ConnectionError("연결 거부"), True]
    first = {"value": 1}
    updated = {"value": 2}

    services.save_data_to_redis("key", first)
    assert services.load_data_from_redis("key") == first
    services.save_data_to_redis("key", updated)
    assert services.load_data_from_redis("key") == updated
    assert cache_state.redis.setex.call_count == 1
    cache_state.redis.get.assert_not_called()

    cache_state.clock.advance(services.REDIS_RETRY_AFTER_SECONDS)
    services.save_data_to_redis("key", updated)
    assert cache_state.redis.setex.call_count == 2
    assert services.load_data_from_redis("key") == updated
    cache_state.redis.get.assert_called_once_with("key")
    warnings = [record for record in caplog.records if record.name == services.logger.name]
    assert len(warnings) == 1


def test_fallback_expires_without_reads_extending_its_ttl(cache_state) -> None:
    """대체 캐시는 저장 시점부터 한 시간 뒤에 만료됩니다."""
    data = {"value": 1}
    services.save_data_to_redis("key", data)

    cache_state.clock.advance(services.CACHE_DURATION - 1)
    assert services.load_data_from_redis("key") == data
    cache_state.clock.advance(1)
    assert services.load_data_from_redis("key") is None


def test_redis_hit_does_not_refresh_fallback_ttl(cache_state) -> None:
    """Redis 읽기 성공이 이전 대체 데이터의 유효 기간을 늘리지 않아야 합니다."""
    services.save_data_to_redis("key", {"value": "이전 데이터"})
    cache_state.clock.advance(services.CACHE_DURATION - 1)
    cache_state.redis.get.return_value = json.dumps({"value": "Redis 데이터"})
    assert services.load_data_from_redis("key") == {"value": "Redis 데이터"}

    cache_state.clock.advance(1)
    cache_state.redis.get.side_effect = redis.ConnectionError("연결 거부")
    assert services.load_data_from_redis("key") is None


@pytest.mark.parametrize("raw", ["잘못된 JSON", "null", "42", '"문자열"'])
def test_invalid_redis_json_uses_fallback_without_entering_cooldown(cache_state, raw) -> None:
    """캐시 데이터 오류는 연결 장애로 처리하지 않고 다음 읽기도 정상 시도합니다."""
    fallback = {"value": "대체 데이터"}
    services.save_data_to_redis("key", fallback)
    cache_state.redis.get.return_value = raw

    assert services.load_data_from_redis("key") == fallback
    assert services.load_data_from_redis("key") == fallback
    assert cache_state.redis.get.call_count == 2

    cache_state.redis.get.return_value = json.dumps({"value": "정상 데이터"})
    assert services.load_data_from_redis("key") == {"value": "정상 데이터"}
    assert cache_state.redis.get.call_count == 3
