# core/views.py
"""
코어 뷰 모듈 (표준 Django JsonResponse)

- React SPA 서빙 (serve_react)
- 공지사항/랭킹/홈 통합 데이터 API

Django Ninja Router(core/api/views.py)를 이 파일로 통합합니다.
"""

import logging
import os
from typing import Any

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods

from apps.core.services import (
    get_notice_list,
    get_ranking_list,
    load_notice_data_from_redis,
    load_ranking_data_from_redis,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# React SPA 서빙
# ---------------------------------------------------------------------------


def serve_react(request) -> HttpResponse:
    """
    React 빌드 결과물(index.html)을 서빙합니다.
    SPA 클라이언트 라우팅을 위해 모든 알 수 없는 경로에서 호출됩니다.
    """
    try:
        with open(
            os.path.join(settings.BASE_DIR, "static", "dist", "index.html"),
            encoding="utf-8",
        ) as f:
            return HttpResponse(f.read())
    except FileNotFoundError:
        return HttpResponse(
            "React build not found. Please run 'npm run build' in frontend directory.",
            status=501,
        )


# ---------------------------------------------------------------------------
# 홈 통합 데이터 API
# ---------------------------------------------------------------------------


def _extract_list(data: Any, keys: list[str]) -> list:
    """dict에서 지정 키 순서로 리스트를 추출합니다."""
    if not data:
        return []
    if isinstance(data, dict):
        for key in keys:
            if key in data and isinstance(data[key], list):
                return data[key]
    return []


@require_http_methods(["GET"])
def home_data(request) -> JsonResponse:
    """
    메인 페이지용 통합 데이터(공지 5건씩 + 랭킹 10건)를 반환합니다.

    GET /api/v1/core/home/data/
    """
    empty_response = {
        "notices": {"updates": [], "events": [], "cashshop": []},
        "ranking": [],
    }

    try:
        notice = get_notice_list() or {}
        ranking = get_ranking_list() or {}

        notice_events = _extract_list(notice.get("notice_event"), ["event_notice"])
        notice_updates = _extract_list(notice.get("notice_update"), ["update_notice"])
        notice_cashshops = _extract_list(notice.get("notice_cashshop"), ["cashshop_notice"])
        ranking_list = ranking.get("overall_ranking", [])

        return JsonResponse(
            {
                "notices": {
                    "updates": notice_updates[:5],
                    "events": notice_events[:5],
                    "cashshop": notice_cashshops[:5],
                },
                "ranking": ranking_list[:10],
            },
            status=200,
        )

    except Exception as e:
        logger.error(f"Home API 오류: {e}")
        return JsonResponse(empty_response, status=200)


# ---------------------------------------------------------------------------
# 공지사항 API
# ---------------------------------------------------------------------------


@require_http_methods(["GET"])
def get_notices_json(request) -> JsonResponse:
    """
    캐시된 Redis에서 공지사항 전체 데이터를 로드합니다.

    GET /api/v1/core/notices/json/
    """
    data = load_notice_data_from_redis()
    return JsonResponse({"status": "success", "data": data}, status=200)


@require_http_methods(["GET"])
def get_event_notices(request) -> JsonResponse:
    """
    이벤트 공지사항을 조회합니다.

    GET /api/v1/core/notices/event/
    """
    notice = get_notice_list() or {}
    data = notice.get("notice_event", {}).get("event_notice", [])
    return JsonResponse({"status": "success", "data": data}, status=200)


@require_http_methods(["GET"])
def get_update_notices(request) -> JsonResponse:
    """
    업데이트 공지사항을 조회합니다.

    GET /api/v1/core/notices/update/
    """
    notice = get_notice_list() or {}
    data = notice.get("notice_update", {}).get("update_notice", [])
    return JsonResponse({"status": "success", "data": data}, status=200)


@require_http_methods(["GET"])
def get_cashshop_notices(request) -> JsonResponse:
    """
    캐시샵 공지사항을 조회합니다.

    GET /api/v1/core/notices/cashshop/
    """
    notice = get_notice_list() or {}
    data = notice.get("notice_cashshop", {}).get("cashshop_notice", [])
    return JsonResponse({"status": "success", "data": data}, status=200)


# ---------------------------------------------------------------------------
# 랭킹 API
# ---------------------------------------------------------------------------


@require_http_methods(["GET"])
def get_ranking_json(request) -> JsonResponse:
    """
    캐시된 Redis에서 랭킹 전체 데이터를 로드합니다.

    GET /api/v1/core/ranking/json/
    """
    data = load_ranking_data_from_redis()
    return JsonResponse({"status": "success", "data": data}, status=200)


@require_http_methods(["GET"])
def get_overall_ranking(request) -> JsonResponse:
    """
    종합 랭킹 상위 50위를 조회합니다.

    GET /api/v1/core/ranking/overall/
    """
    ranking = get_ranking_list() or {}
    data = ranking.get("overall_ranking", [])
    return JsonResponse({"status": "success", "data": data}, status=200)
