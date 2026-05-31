# apps/chat/services.py
"""
채팅 비즈니스 로직 서비스

뷰(View)에서 분리된 AI 서버 통신, 세션 관리 및 DB 저장 로직을 담당합니다.
"""

import json
import logging
import time
import uuid

import aiohttp
import requests
from django.conf import settings

from apps.chat.models import ChatSession, ChatMessage
from common.exceptions.chat import AiServerUnavailable

logger = logging.getLogger(__name__)

# AI 서버 주소: settings.py에서 관리하며, 없을 경우 기본값을 사용합니다.
_AI_BASE = getattr(settings, "AI_SERVER_BASE_URL", "http://127.0.0.1:8001")
AI_SERVER_URL = f"{_AI_BASE}/generate"
AI_SERVER_STREAM_URL = f"{_AI_BASE}/stream"


def send_message_sync(session: ChatSession, content: str) -> tuple[ChatMessage, dict]:
    """
    AI 서버로 메시지를 동기 전송하고 DB에 저장합니다.

    Args:
        session: 현재 활성화된 채팅 세션
        content: 유저가 보낸 메시지

    Returns:
        (저장된 메시지 객체, 응답용 딕셔너리)
    """
    start_time = time.time()
    payload = {"session_id": str(session.session_id), "message": content}

    try:
        response = requests.post(AI_SERVER_URL, json=payload, timeout=120)

        if response.status_code == 200:
            ai_data = response.json()
            ai_text = ai_data.get("response", "")
            ai_thinking = ai_data.get("thinking", "")
        else:
            logger.error(f"AI 서버 에러: {response.status_code} - {response.text}")
            raise AiServerUnavailable()

    except requests.exceptions.RequestException as e:
        logger.error(f"AI 서버 연결 실패: {e}")
        raise AiServerUnavailable()

    response_time = int((time.time() - start_time) * 1000)

    # DB 저장
    saved_msg = ChatMessage.objects.create(
        session_id=session,
        user_message=content,
        ai_response=ai_text,
        thinking=ai_thinking,
        response_time=response_time,
    )

    result_dict = {
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
    }

    return saved_msg, result_dict


def stream_message_generator(session: ChatSession, content: str):
    """
    AI 서버로부터 SSE 스트리밍 응답을 동기적으로 받고 완료 후 DB에 저장합니다.
    (Django WSGI 환경과의 호환성을 위해 requests 기반으로 작성)
    """
    # 사용자 메시지 먼저 DB에 임시 저장
    msg_obj = ChatMessage.objects.create(
        session_id=session,
        user_message=content,
        ai_response="",
    )

    ai_accumulated_text: list[str] = []
    payload = {"session_id": str(session.session_id), "message": content}

    try:
        # requests.post(stream=True)로 스트리밍 응답 받기
        with requests.post(AI_SERVER_STREAM_URL, json=payload, timeout=60, stream=True) as r:
            if r.status_code != 200:
                error_msg = {"type": "error", "content": f"AI Server Error: {r.status_code}"}
                yield f"data: {json.dumps(error_msg)}\n\n"
                return

            for line in r.iter_lines():
                if line:
                    decoded_line = line.decode("utf-8").strip()
                    if not decoded_line:
                        continue
                    
                    # 원본 형식 유지하면서 클라이언트에 전달
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

    # 스트리밍이 끝나면 최종 생성된 AI 답변을 DB 업데이트
    final_text = "".join(ai_accumulated_text)
    try:
        msg_obj.ai_response = final_text
        msg_obj.save()
    except Exception as e:
        logger.error(f"스트리밍 DB 업데이트 실패: {e}")
