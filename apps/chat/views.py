# apps/chat/views.py
"""챗봇 API 뷰 (표준 Django JsonResponse + StreamingHttpResponse)

비즈니스 로직은 apps.chat.services로 분리되었습니다.
HTTP 인터페이스 처리와 라우팅만 담당합니다.
"""

import logging

from django.conf import settings
from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.http import require_http_methods

from apps.chat.models import ChatSession
from apps.chat.services import send_message_async, stream_message_generator
from common import ratelimit
from common.utils.request_helpers import parse_json_body

logger = logging.getLogger(__name__)


def _extract_message_content(body: dict) -> str:
    """파싱된 요청 데이터에서 메시지 본문을 추출합니다."""
    return body.get("message_content", "").strip() or body.get("content", "").strip()


def _error(status: int, error_code: str, message: str) -> JsonResponse:
    return JsonResponse(
        {"success": False, "error_code": error_code, "message": message}, status=status
    )


async def _owned_session(request, session_id: str) -> ChatSession:
    """요청한 사람(로그인 사용자 또는 비로그인 브라우저)이 소유한 세션을 반환합니다."""
    user = await request.auser()
    return await ChatSession.objects.aget_owned_or_raise(
        session_id, user, request.session.session_key
    )


async def _check_new_message(request, body: dict) -> tuple[str, JsonResponse | None]:
    """새 메시지의 본문을 검사하고 전송 횟수 제한을 적용합니다.

    Returns:
        (메시지 본문, 거절할 때의 오류 응답 또는 None)
    """
    content = _extract_message_content(body)
    if not content:
        return content, _error(
            400, "CONTENT_REQUIRED", "메시지 본문(message_content)이 준비되어야 합니다."
        )

    max_chars = settings.CHAT_MESSAGE_MAX_CHARS
    if len(content) > max_chars:
        return content, _error(
            400, "MESSAGE_TOO_LONG", f"메시지는 {max_chars}자 이하로 보내 주세요."
        )

    # 로그인 사용자는 계정 기준, 비로그인 사용자는 IP 기준으로 더 낮은 한도를 적용합니다.
    user = await request.auser()
    if user.is_authenticated:
        scope, ident, spec = "chat:user", str(user.pk), settings.CHAT_RATE_LIMIT_USER
    else:
        scope, ident, spec = "chat:anon", ratelimit.client_ip(request), settings.CHAT_RATE_LIMIT_ANON
    if not await ratelimit.ahit(scope, ident, ratelimit.parse_rate_limits(spec)):
        logger.warning(f"채팅 요청 한도 초과: {scope}:{ident}")
        return content, _error(
            429, "RATE_LIMITED", "질문이 너무 많아요. 잠시 후 다시 시도해 주세요."
        )

    return content, None


# ---------------------------------------------------------------------------
# 세션 관련 엔드포인트
# ---------------------------------------------------------------------------


async def get_sessions(request) -> JsonResponse:
    """
    채팅 세션 목록 조회.

    GET /api/v1/chat/rooms
    """
    user = await request.auser()
    if user.is_authenticated:
        # filter는 sync, 하지만 비동기 반복 가능
        sessions = [
            s
            async for s in ChatSession.objects.filter(user=user).order_by(
                "-created_at"
            )
        ]
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
                "created_at": session.created_at.isoformat(),  # 설계서 스펙 (create_session과 계약 일치)
            }
        )
    return JsonResponse({"success": True, "rooms": session_list}, status=200)


async def create_session(request) -> JsonResponse:
    """
    새로운 채팅 세션 생성.

    POST /api/v1/chat/rooms
    """
    user = await request.auser()

    body, parse_error = parse_json_body(request)
    room_name = "새로운 대화"
    if parse_error is None:
        room_name = str(body.get("room_name", room_name)).strip() or room_name

    if user.is_authenticated:
        session = await ChatSession.objects.acreate(user=user)
    else:
        # 비로그인 세션은 이 브라우저의 Django 세션 키로 주인을 구분합니다.
        if not request.session.session_key:
            await request.session.acreate()
        session = await ChatSession.objects.acreate(owner_key=request.session.session_key)
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
    session = await _owned_session(request, session_id)
    # select_related를 통해 metadata 조인을 미리 수행합니다.
    messages = [
        msg
        async for msg in session.messages.select_related("metadata")
        .all()
        .order_by("created_at")
    ]

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
            metadata = getattr(msg, "metadata", None)
            message_list.append(
                {
                    "id": msg.id,
                    "sender_type": "assistant",
                    "message_content": msg.content,
                    "thinking": (metadata.thinking or "") if metadata else "",
                    "sources": metadata.sources if metadata else [],
                    "sent_at": msg.created_at.isoformat(),
                }
            )

    return JsonResponse({"success": True, "messages": message_list}, status=200)


async def send_message(request, session_id: str) -> JsonResponse:
    """세션에 메시지를 전송하고 AI 답변 수신 (비동기).

    POST /api/v1/chat/rooms/{room_id}/messages
    """
    session = await _owned_session(request, session_id)

    body, parse_error = parse_json_body(request)
    if parse_error:
        return _error(400, "INVALID_FORMAT", "유효하지 않은 요청 형식입니다.")
    content, rejection = await _check_new_message(request, body)
    if rejection:
        return rejection

    user = await request.auser()
    user_msg, assistant_msg, _ = await send_message_async(session, content, user)

    return JsonResponse(
        {
            "success": True,
            "user_message": {
                "id": user_msg.id,
                "sender_type": "user",
                "message_content": content,
                "sent_at": user_msg.created_at.isoformat(),
            },
            "assistant_message": {
                "id": assistant_msg.id,
                "sender_type": "assistant",
                "message_content": assistant_msg.content,
                "sent_at": assistant_msg.created_at.isoformat(),
            },
        },
        status=200,
    )


async def delete_session(request, session_id: str) -> JsonResponse:
    """특정 채팅 세션 삭제.

    DELETE /api/v1/chat/rooms/{room_id}
    """
    session = await _owned_session(request, session_id)
    await session.adelete()
    return JsonResponse(
        {"success": True, "message": "대화방이 삭제되었습니다."}, status=200
    )


# ---------------------------------------------------------------------------
# HTTP Method Dispatchers (설계서 API 규격 맵핑 목적)
# 세션 쿠키로 인증하므로 CSRF 검사를 적용합니다. (프론트는 X-CSRFToken 헤더를 보냅니다)
# ---------------------------------------------------------------------------


async def rooms_dispatch(request) -> JsonResponse:
    """/api/v1/chat/rooms 경로의 GET/POST 분기 처리"""
    if request.method == "GET":
        return await get_sessions(request)
    elif request.method == "POST":
        return await create_session(request)
    return JsonResponse({"detail": "Method not allowed"}, status=405)


async def messages_dispatch(request, session_id: str) -> JsonResponse:
    """/api/v1/chat/rooms/{session_id}/messages 경로의 GET/POST 분기 처리"""
    if request.method == "GET":
        return await get_messages(request, session_id)
    elif request.method == "POST":
        return await send_message(request, session_id)
    return JsonResponse({"detail": "Method not allowed"}, status=405)


async def room_detail_dispatch(request, session_id: str) -> JsonResponse:
    """/api/v1/chat/rooms/{session_id} 경로의 DELETE 분기 처리"""
    if request.method == "DELETE":
        return await delete_session(request, session_id)
    return JsonResponse({"detail": "Method not allowed"}, status=405)


# (참고) SSE 스트리밍 엔드포인트
@require_http_methods(["POST"])
async def stream_message(request, session_id: str) -> StreamingHttpResponse:
    """세션에 메시지를 전송하고 AI 서버로부터 스트리밍 응답 수신 (SSE).

    POST /api/v1/chat/rooms/<session_id>/stream/
    """
    session = await _owned_session(request, session_id)

    body, parse_error = parse_json_body(request)
    if parse_error:
        return _error(400, "INVALID_FORMAT", "유효하지 않은 요청 형식입니다.")
    content, rejection = await _check_new_message(request, body)
    if rejection:
        return rejection

    user = await request.auser()
    stream_generator = stream_message_generator(session, content, user)
    response = StreamingHttpResponse(stream_generator, content_type="text/event-stream")
    # 프록시(Nginx 등)가 응답을 모아서 보내지 않도록 버퍼링을 끕니다.
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"
    return response
