# apps/chat/views.py
"""챗봇 API 뷰 (표준 Django JsonResponse + StreamingHttpResponse)

비즈니스 로직은 apps.chat.services로 분리되었습니다.
HTTP 인터페이스 처리와 라우팅만 담당합니다.
"""

import json
import logging

from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from apps.chat.models import ChatSession
from apps.chat.services import send_message_sync, stream_message_generator

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 세션 관련 엔드포인트
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# 세션 관련 엔드포인트 (설계서 chat-api.md 기준 리팩토링)
# ---------------------------------------------------------------------------


def get_sessions(request) -> JsonResponse:
    """
    채팅 세션 목록 조회.

    GET /api/v1/chat/rooms
    """
    if request.user.is_authenticated:
        sessions = ChatSession.objects.filter(user=request.user)
    else:
        sessions = ChatSession.objects.none()

    sessions = sessions.order_by("-created_at")
    session_list = []

    for session in sessions:
        first_message = session.messages.order_by("created_at").first()
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
                "room_name": title,  # 설계서 스펙
                "updated_at": session.created_at.isoformat(),  # 설계서 스펙
            }
        )
    return JsonResponse({"success": True, "rooms": session_list}, status=200)


def create_session(request) -> JsonResponse:
    """
    새로운 채팅 세션 생성.

    POST /api/v1/chat/rooms
    """
    user_profile = request.user if request.user.is_authenticated else None

    # 요청 바디에서 room_name 추출
    try:
        body = json.loads(request.body)
        room_name = body.get("room_name", "새로운 대화").strip()
    except Exception:
        room_name = "새로운 대화"

    session = ChatSession.objects.create(user=user_profile)
    logger.info(f"새로운 세션 생성: {session.session_id}")

    return JsonResponse(
        {
            "success": True,
            "room": {
                "id": str(session.session_id),
                "room_name": room_name,
                "created_at": session.created_at.isoformat(),
            },
        },
        status=201,
    )


def get_messages(request, session_id: str) -> JsonResponse:
    """특정 세션의 메시지 목록 조회.

    GET /api/v1/chat/rooms/{room_id}/messages
    """
    session = ChatSession.objects.get_by_uuid_or_raise(session_id)
    messages = session.messages.all().order_by("created_at")

    message_list = []
    for msg in messages:
        # DB의 ChatMessage 한 행(user_message와 ai_response 한 쌍)을
        # 설계서의 개별 메시지 스트림으로 평탄화(Flatten)하여 변환합니다.
        if msg.user_message:
            message_list.append(
                {
                    "id": msg.id * 2,
                    "sender_type": "user",
                    "message_content": msg.user_message,
                    "sent_at": msg.created_at.isoformat(),
                }
            )
        if msg.ai_response:
            message_list.append(
                {
                    "id": msg.id * 2 + 1,
                    "sender_type": "assistant",
                    "message_content": msg.ai_response,
                    "thinking": msg.thinking or "",
                    "sent_at": msg.created_at.isoformat(),
                }
            )

    return JsonResponse({"success": True, "messages": message_list}, status=200)


def send_message(request, session_id: str) -> JsonResponse:
    """세션에 메시지를 전송하고 AI 답변 수신 (동기).

    POST /api/v1/chat/rooms/{room_id}/messages
    """
    session = ChatSession.objects.get_by_uuid_or_raise(session_id)

    try:
        body = json.loads(request.body)
        content = body.get("message_content", "").strip() or body.get("content", "").strip()
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"success": False, "error_code": "INVALID_FORMAT", "message": "유효하지 않은 요청 형식입니다."}, status=400)

    if not content:
        return JsonResponse({"success": False, "error_code": "CONTENT_REQUIRED", "message": "메시지 본문(message_content)이 유비되어야 합니다."}, status=400)

    # 비즈니스 로직 호출
    saved_msg, _ = send_message_sync(session, content)

    return JsonResponse(
        {
            "success": True,
            "user_message": {
                "id": saved_msg.id * 2,
                "sender_type": "user",
                "message_content": content,
                "sent_at": saved_msg.created_at.isoformat(),
            },
            "assistant_message": {
                "id": saved_msg.id * 2 + 1,
                "sender_type": "assistant",
                "message_content": saved_msg.ai_response,
                "sent_at": saved_msg.created_at.isoformat(),
            },
        },
        status=200,
    )


def delete_session(request, session_id: str) -> JsonResponse:
    """특정 채팅 세션 삭제.

    DELETE /api/v1/chat/rooms/{room_id}
    """
    session = ChatSession.objects.get_by_uuid_or_raise(session_id)
    session.delete()
    return JsonResponse({"success": True, "message": "대화방이 삭제되었습니다."}, status=200)


# ---------------------------------------------------------------------------
# HTTP Method Dispatchers (설계서 API 규격 맵핑 목적)
# ---------------------------------------------------------------------------


@csrf_exempt
def rooms_dispatch(request) -> JsonResponse:
    """/api/v1/chat/rooms 경로의 GET/POST 분기 처리"""
    if request.method == "GET":
        return get_sessions(request)
    elif request.method == "POST":
        return create_session(request)
    return JsonResponse({"detail": "Method not allowed"}, status=405)


@csrf_exempt
def messages_dispatch(request, session_id: str) -> JsonResponse:
    """/api/v1/chat/rooms/{session_id}/messages 경로의 GET/POST 분기 처리"""
    if request.method == "GET":
        return get_messages(request, session_id)
    elif request.method == "POST":
        return send_message(request, session_id)
    return JsonResponse({"detail": "Method not allowed"}, status=405)


@csrf_exempt
def room_detail_dispatch(request, session_id: str) -> JsonResponse:
    """/api/v1/chat/rooms/{session_id} 경로의 DELETE 분기 처리"""
    if request.method == "DELETE":
        return delete_session(request, session_id)
    return JsonResponse({"detail": "Method not allowed"}, status=405)


# (참고) SSE 스트리밍 엔드포인트
@csrf_exempt
@require_http_methods(["POST"])
def stream_message(request, session_id: str) -> StreamingHttpResponse:
    """세션에 메시지를 전송하고 AI 서버로부터 스트리밍 응답 수신 (SSE).

    POST /api/v1/chat/sessions/<session_id>/stream/
    """
    session = ChatSession.objects.get_by_uuid_or_raise(session_id)

    try:
        body = json.loads(request.body)
        content = body.get("message_content", "").strip() or body.get("content", "").strip()
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "유효하지 않은 요청 형식입니다."}, status=400)

    stream_generator = stream_message_generator(session, content)
    return StreamingHttpResponse(stream_generator, content_type="text/event-stream")