# chat/views.py
"""
챗봇 API 뷰 (표준 Django JsonResponse + StreamingHttpResponse)

Django Ninja Router에서 표준 Django 뷰로 전환합니다.
AI 서버(FastAPI)와의 통신은 requests 라이브러리를 사용합니다.
"""

import json
import logging
import time
import uuid

import requests
from django.conf import settings
from django.http import JsonResponse, StreamingHttpResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from chat.models import ChatSession, ChatMessage

logger = logging.getLogger(__name__)

# AI 서버 주소: settings.py에서 관리하며, 없을 경우 기본값을 사용합니다.
_AI_BASE = getattr(settings, "AI_SERVER_BASE_URL", "http://127.0.0.1:8001")
AI_SERVER_URL = f"{_AI_BASE}/generate"
AI_SERVER_STREAM_URL = f"{_AI_BASE}/stream"


def _get_session_or_404(session_id: uuid.UUID) -> ChatSession:
    """세션을 안전하게 조회하고 없을 경우 404를 반환합니다."""
    return get_object_or_404(ChatSession, session_id=session_id)


# ---------------------------------------------------------------------------
# 세션 관련 엔드포인트
# ---------------------------------------------------------------------------


@require_http_methods(["GET"])
def get_sessions(request) -> JsonResponse:
    """
    채팅 세션 목록 조회.

    GET /api/chat/sessions/
    """
    try:
        if request.user.is_authenticated:
            # ChatSession.user는 auth.User를 직접 FK로 참조하므로 request.user를 사용
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

    except Exception as e:
        logger.error(f"세션 조회 중 오류 발생: {e}")
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def create_session(request) -> JsonResponse:
    """
    새로운 채팅 세션 생성.

    POST /api/chat/sessions/create/
    """
    try:
        # ChatSession.user는 auth.User를 직접 FK로 참조 (null 허용)
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

    except Exception as e:
        logger.error(f"세션 생성 중 오류 발생: {e}")
        return JsonResponse({"error": str(e)}, status=500)


@require_http_methods(["GET"])
def get_messages(request, session_id: str) -> JsonResponse:
    """
    특정 세션의 메시지 목록 조회.

    GET /api/chat/sessions/<session_id>/messages/
    """
    try:
        session_uuid = uuid.UUID(session_id)
    except ValueError:
        return JsonResponse({"error": "유효하지 않은 세션 ID입니다."}, status=400)

    session = _get_session_or_404(session_uuid)
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
    try:
        session_uuid = uuid.UUID(session_id)
    except ValueError:
        return JsonResponse({"error": "유효하지 않은 세션 ID입니다."}, status=400)

    try:
        body = json.loads(request.body)
        content = body.get("content", "").strip()
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "유효하지 않은 요청 형식입니다."}, status=400)

    if not content:
        return JsonResponse({"error": "Content is required"}, status=400)

    session = _get_session_or_404(session_uuid)
    start_time = time.time()

    try:
        payload = {"session_id": str(session.session_id), "message": content}
        response = requests.post(AI_SERVER_URL, json=payload, timeout=1200)

        if response.status_code == 200:
            ai_data = response.json()
            ai_text = ai_data.get("response", "")
            ai_thinking = ai_data.get("thinking", "")
        else:
            logger.error(f"AI 서버 에러: {response.status_code} - {response.text}")
            return JsonResponse({"error": f"AI Server Error: {response.status_code}"}, status=500)

    except requests.exceptions.RequestException as e:
        logger.error(f"AI 서버 연결 실패: {e}")
        return JsonResponse({"error": "AI 서버에 연결할 수 없습니다."}, status=500)

    response_time = int((time.time() - start_time) * 1000)

    saved_msg = ChatMessage.objects.create(
        session_id=session,
        user_message=content,
        ai_response=ai_text,
        thinking=ai_thinking,
        response_time=response_time,
    )

    return JsonResponse(
        {
            "user_message": {
                "role": "user",
                "content": content,
                "created_at": saved_msg.created_at.isoformat(),
                "thinking": "",
            },
            "ai_message": {
                "role": "assistant",
                "content": ai_text,
                "thinking": ai_thinking,
                "created_at": saved_msg.created_at.isoformat(),
            },
        },
        status=200,
    )


@csrf_exempt
@require_http_methods(["POST"])
def stream_message(request, session_id: str) -> StreamingHttpResponse:
    """
    세션에 메시지를 전송하고 AI 서버로부터 스트리밍 응답 수신 (SSE).

    POST /api/chat/sessions/<session_id>/stream/
    """
    try:
        session_uuid = uuid.UUID(session_id)
    except ValueError:
        return JsonResponse({"error": "유효하지 않은 세션 ID입니다."}, status=400)

    try:
        body = json.loads(request.body)
        content = body.get("content", "").strip()
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "유효하지 않은 요청 형식입니다."}, status=400)

    session = _get_session_or_404(session_uuid)

    # 사용자 메시지 임시 저장 (ai_response는 스트리밍 종료 후 업데이트)
    ChatMessage.objects.create(
        session_id=session,
        user_message=content,
        ai_response="",
    )

    def event_stream():
        """SSE 이벤트 스트림 제너레이터."""
        ai_accumulated_text: list[str] = []
        payload = {"session_id": str(session.session_id), "message": content}

        try:
            with requests.post(
                AI_SERVER_STREAM_URL, json=payload, stream=True, timeout=60
            ) as r:
                if r.status_code != 200:
                    yield f"data: {json.dumps({'type': 'error', 'content': f'AI Server Error: {r.status_code}'})}\n\n"
                    return

                for line in r.iter_lines():
                    if line:
                        decoded_line = line.decode("utf-8")
                        yield decoded_line + "\n\n"

                        if decoded_line.startswith("data: "):
                            try:
                                json_str = decoded_line[6:]
                                if json_str.strip() == "[DONE]":
                                    continue
                                chunk_data = json.loads(json_str)
                                if chunk_data.get("type") == "token":
                                    ai_accumulated_text.append(chunk_data.get("content", ""))
                            except Exception:
                                pass

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

        # 스트리밍 종료 후 전체 AI 답변을 DB에 업데이트
        final_text = "".join(ai_accumulated_text)
        try:
            last_msg = (
                ChatMessage.objects.filter(session_id=session)
                .order_by("-created_at")
                .first()
            )
            if last_msg:
                last_msg.ai_response = final_text
                last_msg.save()
        except Exception as e:
            logger.error(f"스트리밍 DB 업데이트 실패: {e}")

    return StreamingHttpResponse(event_stream(), content_type="text/event-stream")


@csrf_exempt
@require_http_methods(["DELETE"])
def delete_session(request, session_id: str) -> JsonResponse:
    """
    특정 채팅 세션 삭제.

    DELETE /api/chat/sessions/<session_id>/delete/
    """
    try:
        session_uuid = uuid.UUID(session_id)
    except ValueError:
        return JsonResponse({"error": "유효하지 않은 세션 ID입니다."}, status=400)

    try:
        session = _get_session_or_404(session_uuid)
        session.delete()
        return JsonResponse({"status": "deleted", "session_id": session_id}, status=200)
    except Exception as e:
        logger.error(f"세션 삭제 중 오류 발생: {e}")
        return JsonResponse({"error": str(e)}, status=404)