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
from apps.chat.services import send_message_async, stream_message_generator


from django.contrib.auth.models import User
from asgiref.sync import sync_to_async

logger = logging.getLogger(__name__)


@sync_to_async
def get_request_user(request) -> User | None:
    """비동기 컨텍스트에서 안전하게 request.user 객체를 획득합니다.

    Django의 lazy user 평가는 동기 데이터베이스 쿼리를 수반하므로,
    비동기 뷰 스레드에서 직접 평가 시 SynchronousOnlyOperation 예외가 발생할 수 있습니다.
    따라서 sync_to_async를 사용하여 백그라운드 스레드에서 안전하게 로드합니다.

    Args:
        request: Django HTTP 요청 객체.

    Returns:
        인증된 경우 Django User 객체, 그렇지 않다면 None.
    """
    if request.user.is_authenticated:
        return request.user
    return None


# ---------------------------------------------------------------------------
# 세션 관련 엔드포인트
# ---------------------------------------------------------------------------


async def get_sessions(request) -> JsonResponse:
    """
    채팅 세션 목록 조회.

    GET /api/v1/chat/rooms
    """
    user = await get_request_user(request)
    if user:
        # filter는 sync, 하지만 비동기 반복 가능
        sessions = [s async for s in ChatSession.objects.filter(user=user).order_by("-created_at")]
    else:
        sessions = []

    session_list = []

    for session in sessions:
        first_message = await session.messages.order_by("created_at").afirst()
        if first_message and first_message.role == "user" and first_message.content:
            title = (
                first_message.content[:20] + "..."
                if len(first_message.content) > 20
                else first_message.content
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


async def create_session(request) -> JsonResponse:
    """
    새로운 채팅 세션 생성.

    POST /api/v1/chat/rooms
    """
    user_profile = await get_request_user(request)

    # 요청 바디에서 room_name 추출
    try:
        body = json.loads(request.body)
        room_name = body.get("room_name", "새로운 대화").strip()
    except Exception:
        room_name = "새로운 대화"

    session = await ChatSession.objects.acreate(user=user_profile)
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


async def get_messages(request, session_id: str) -> JsonResponse:
    """특정 세션의 메시지 목록 조회.

    GET /api/v1/chat/rooms/{room_id}/messages
    """
    session = await ChatSession.objects.aget_by_uuid_or_raise(session_id)
    # select_related를 통해 metadata 조인을 미리 수행합니다.
    messages = [msg async for msg in session.messages.select_related('metadata').all().order_by("created_at")]

    message_list = []
    for msg in messages:
        if msg.role == "user":
            message_list.append(
                {
                    "id": msg.id,
                    "sender_type": "user",
                    "message_content": msg.content,
                    "sent_at": msg.created_at.isoformat(),
                }
            )
        elif msg.role == "assistant":
            thinking = msg.metadata.thinking if hasattr(msg, 'metadata') and msg.metadata else ""
            message_list.append(
                {
                    "id": msg.id,
                    "sender_type": "assistant",
                    "message_content": msg.content,
                    "thinking": thinking,
                    "sent_at": msg.created_at.isoformat(),
                }
            )

    return JsonResponse({"success": True, "messages": message_list}, status=200)


async def send_message(request, session_id: str) -> JsonResponse:
    """세션에 메시지를 전송하고 AI 답변 수신 (비동기).

    POST /api/v1/chat/rooms/{room_id}/messages
    """
    session = await ChatSession.objects.aget_by_uuid_or_raise(session_id)

    try:
        body = json.loads(request.body)
        content = body.get("message_content", "").strip() or body.get("content", "").strip()
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"success": False, "error_code": "INVALID_FORMAT", "message": "유효하지 않은 요청 형식입니다."}, status=400)

    if not content:
        return JsonResponse({"success": False, "error_code": "CONTENT_REQUIRED", "message": "메시지 본문(message_content)이 유비되어야 합니다."}, status=400)

    # 비즈니스 로직 호출
    saved_msg, _ = await send_message_async(session, content)


    return JsonResponse(
        {
            "success": True,
            "user_message": {
                "id": saved_msg.id - 1, # 단순화를 위해 대략적인 ID 할당
                "sender_type": "user",
                "message_content": content,
                "sent_at": saved_msg.created_at.isoformat(),
            },
            "assistant_message": {
                "id": saved_msg.id,
                "sender_type": "assistant",
                "message_content": saved_msg.content,
                "sent_at": saved_msg.created_at.isoformat(),
            },
        },
        status=200,
    )


async def delete_session(request, session_id: str) -> JsonResponse:
    """특정 채팅 세션 삭제.

    DELETE /api/v1/chat/rooms/{room_id}
    """
    session = await ChatSession.objects.aget_by_uuid_or_raise(session_id)
    await session.adelete()
    return JsonResponse({"success": True, "message": "대화방이 삭제되었습니다."}, status=200)


# ---------------------------------------------------------------------------
# HTTP Method Dispatchers (설계서 API 규격 맵핑 목적)
# ---------------------------------------------------------------------------


@csrf_exempt
async def rooms_dispatch(request) -> JsonResponse:
    """/api/v1/chat/rooms 경로의 GET/POST 분기 처리"""
    if request.method == "GET":
        return await get_sessions(request)
    elif request.method == "POST":
        return await create_session(request)
    return JsonResponse({"detail": "Method not allowed"}, status=405)


@csrf_exempt
async def messages_dispatch(request, session_id: str) -> JsonResponse:
    """/api/v1/chat/rooms/{session_id}/messages 경로의 GET/POST 분기 처리"""
    if request.method == "GET":
        return await get_messages(request, session_id)
    elif request.method == "POST":
        return await send_message(request, session_id)
    return JsonResponse({"detail": "Method not allowed"}, status=405)


@csrf_exempt
async def room_detail_dispatch(request, session_id: str) -> JsonResponse:
    """/api/v1/chat/rooms/{session_id} 경로의 DELETE 분기 처리"""
    if request.method == "DELETE":
        return await delete_session(request, session_id)
    return JsonResponse({"detail": "Method not allowed"}, status=405)


# (참고) SSE 스트리밍 엔드포인트
@csrf_exempt
@require_http_methods(["POST"])
async def stream_message(request, session_id: str) -> StreamingHttpResponse:
    """세션에 메시지를 전송하고 AI 서버로부터 스트리밍 응답 수신 (SSE).

    POST /api/v1/chat/sessions/<session_id>/stream/
    """
    session = await ChatSession.objects.aget_by_uuid_or_raise(session_id)

    try:
        body = json.loads(request.body)
        content = body.get("message_content", "").strip() or body.get("content", "").strip()
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "유효하지 않은 요청 형식입니다."}, status=400)

    stream_generator = stream_message_generator(session, content)
    return StreamingHttpResponse(stream_generator, content_type="text/event-stream")