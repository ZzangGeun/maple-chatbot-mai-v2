# apps/chat/views.py
"""
챗봇 API 뷰 (표준 Django JsonResponse + StreamingHttpResponse)

비즈니스 로직은 apps.chat.services로 분리되었습니다.
HTTP 인터페이스 처리와 라우팅만 담당합니다.
"""

import json
import logging
import uuid

from django.http import JsonResponse, StreamingHttpResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from apps.chat.models import ChatSession
from apps.chat.services import send_message_sync, stream_message_generator
from common.exceptions.chat import InvalidSessionId, SessionNotFound

logger = logging.getLogger(__name__)


def _get_session_or_raise(session_id: str) -> ChatSession:
    """세션을 안전하게 조회하고 없을 경우 커스텀 예외를 발생시킵니다."""
    try:
        session_uuid = uuid.UUID(session_id)
    except ValueError:
        raise InvalidSessionId()

    session = ChatSession.objects.filter(session_id=session_uuid).first()
    if not session:
        raise SessionNotFound(session_id)
    
    return session


# ---------------------------------------------------------------------------
# 세션 관련 엔드포인트
# ---------------------------------------------------------------------------


@require_http_methods(["GET"])
def get_sessions(request) -> JsonResponse:
    """
    채팅 세션 목록 조회.

    GET /api/chat/sessions/
    """
    if request.user.is_authenticated:
        sessions = ChatSession.objects.filter(user=request.user)
    else:
        sessions = ChatSession.objects.none()

    sessions = sessions.order_by("-created_at")
    session_list = []

    for session in sessions:
        first_message = session.messages.order_by("created_at").first()
        last_message = session.messages.order_by("-created_at").first()

        if first_message and first_message.user_message:
            title = (
                first_message.user_message[:20] + "..."
                if len(first_message.user_message) > 20
                else first_message.user_message
            )
        else:
            title = "새로운 대화"

        session_list.append(
            {
                "id": str(session.session_id),
                "created_at": session.created_at.isoformat(),
                "title": title,
                "last_message": last_message.user_message if last_message else "대화 없음",
                "message_count": session.messages.count(),
            }
        )
    return JsonResponse(session_list, safe=False, status=200)


@csrf_exempt
@require_http_methods(["POST"])
def create_session(request) -> JsonResponse:
    """
    새로운 채팅 세션 생성.

    POST /api/chat/sessions/create/
    """
    user_profile = request.user if request.user.is_authenticated else None

    session = ChatSession.objects.create(user=user_profile)
    logger.info(f"새로운 세션 생성: {session.session_id}")

    return JsonResponse(
        {
            "id": str(session.session_id),
            "created_at": session.created_at.isoformat(),
            "last_message": None,
            "message_count": 0,
        },
        status=201,
    )


@require_http_methods(["GET"])
def get_messages(request, session_id: str) -> JsonResponse:
    """
    특정 세션의 메시지 목록 조회.

    GET /api/chat/sessions/<session_id>/messages/
    """
    session = _get_session_or_raise(session_id)
    messages = session.messages.all().order_by("created_at")

    message_list = []
    for msg in messages:
        if msg.user_message:
            message_list.append(
                {
                    "role": "user",
                    "content": msg.user_message,
                    "created_at": msg.created_at.isoformat(),
                    "thinking": "",
                }
            )
        if msg.ai_response:
            message_list.append(
                {
                    "role": "assistant",
                    "content": msg.ai_response,
                    "created_at": msg.created_at.isoformat(),
                    "thinking": getattr(msg, "thinking", "") or "",
                }
            )

    return JsonResponse(message_list, safe=False, status=200)


@csrf_exempt
@require_http_methods(["POST"])
def send_message(request, session_id: str) -> JsonResponse:
    """
    세션에 메시지를 전송하고 AI 답변 수신 (동기).

    POST /api/chat/sessions/<session_id>/send/
    """
    session = _get_session_or_raise(session_id)

    try:
        body = json.loads(request.body)
        content = body.get("content", "").strip()
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "유효하지 않은 요청 형식입니다."}, status=400)

    if not content:
        return JsonResponse({"error": "Content is required"}, status=400)

    # 비즈니스 로직 호출 (DB 저장 및 통신)
    _, result_dict = send_message_sync(session, content)

    return JsonResponse(result_dict, status=200)


@csrf_exempt
@require_http_methods(["POST"])
def stream_message(request, session_id: str) -> StreamingHttpResponse:
    """
    세션에 메시지를 전송하고 AI 서버로부터 스트리밍 응답 수신 (SSE).

    POST /api/chat/sessions/<session_id>/stream/
    """
    session = _get_session_or_raise(session_id)

    try:
        body = json.loads(request.body)
        content = body.get("content", "").strip()
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "유효하지 않은 요청 형식입니다."}, status=400)

    # 제너레이터로 응답 스트리밍 (백그라운드에서 DB 저장됨)
    stream_generator = stream_message_generator(session, content)
    
    return StreamingHttpResponse(stream_generator, content_type="text/event-stream")


@csrf_exempt
@require_http_methods(["DELETE"])
def delete_session(request, session_id: str) -> JsonResponse:
    """
    특정 채팅 세션 삭제.

    DELETE /api/chat/sessions/<session_id>/delete/
    """
    session = _get_session_or_raise(session_id)
    session.delete()
    return JsonResponse({"status": "deleted", "session_id": session_id}, status=200)