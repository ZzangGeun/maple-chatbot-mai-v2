# apps/chat/services.py
"""
채팅 비즈니스 로직 서비스

뷰(View)에서 분리된 AI 서버 통신, 세션 관리 및 DB 저장 로직을 담당합니다.
"""

import json
import logging
import time

import aiohttp
from django.conf import settings

from apps.chat.models import ChatMessage, ChatSession
from common.exceptions.chat import AiServerUnavailable

logger = logging.getLogger(__name__)

AI_REQUEST_TIMEOUT_SEC = 120
AI_STREAM_TIMEOUT_SEC = 60


def get_ai_urls() -> tuple[str, str]:
    """AI 서버 generate/stream 엔드포인트 URL을 반환합니다."""
    ai_base = getattr(settings, "AI_SERVER_BASE_URL", "http://127.0.0.1:8001").rstrip(
        "/"
    )
    return f"{ai_base}/generate", f"{ai_base}/stream"


async def send_message_async(
    session: ChatSession, content: str
) -> tuple[ChatMessage, ChatMessage, dict]:
    """
    AI 서버로 메시지를 비동기 전송하고 DB에 저장합니다.
    """
    from apps.chat.models import MessageMetadata

    start_time = time.time()
    payload = {"session_id": str(session.session_id), "message": content}

    ai_text = ""
    ai_thinking = ""
    generate_url, _ = get_ai_urls()

    try:
        timeout = aiohttp.ClientTimeout(total=AI_REQUEST_TIMEOUT_SEC)
        async with aiohttp.ClientSession(timeout=timeout) as client:
            async with client.post(generate_url, json=payload) as response:
                if response.status == 200:
                    ai_data = await response.json()
                    ai_text = ai_data.get("response", "")
                    ai_thinking = ai_data.get("thinking", "")
                else:
                    text = await response.text()
                    logger.error(f"AI 서버 에러: {response.status} - {text}")
                    raise AiServerUnavailable()

    except aiohttp.ClientError as e:
        logger.error(f"AI 서버 연결 실패: {e}")
        raise AiServerUnavailable()
    except TimeoutError:
        logger.error("AI 서버 응답 타임아웃")
        raise AiServerUnavailable()

    response_time = int((time.time() - start_time) * 1000)

    # DB 저장
    user_msg = await ChatMessage.objects.acreate(
        session=session,
        role="user",
        content=content,
    )

    assistant_msg = await ChatMessage.objects.acreate(
        session=session,
        role="assistant",
        content=ai_text,
    )

    await MessageMetadata.objects.acreate(
        message=assistant_msg, thinking=ai_thinking, response_time_ms=response_time
    )

    result_dict = {
        "user_message": {
            "role": "user",
            "content": content,
            "created_at": user_msg.created_at.isoformat(),
            "thinking": "",
        },
        "ai_message": {
            "role": "assistant",
            "content": ai_text,
            "thinking": ai_thinking,
            "created_at": assistant_msg.created_at.isoformat(),
        },
    }

    return user_msg, assistant_msg, result_dict


async def stream_message_generator(session: ChatSession, content: str):
    """
    AI 서버로부터 SSE 스트리밍 응답을 비동기적으로 받고 완료 후 DB에 저장합니다.
    """
    # 사용자 메시지 먼저 DB에 저장
    await ChatMessage.objects.acreate(
        session=session,
        role="user",
        content=content,
    )

    assistant_msg = await ChatMessage.objects.acreate(
        session=session,
        role="assistant",
        content="",
    )

    ai_accumulated_text: list[str] = []
    payload = {"session_id": str(session.session_id), "message": content}
    _, stream_url = get_ai_urls()

    try:
        timeout = aiohttp.ClientTimeout(total=AI_STREAM_TIMEOUT_SEC)
        async with aiohttp.ClientSession(timeout=timeout) as client:
            async with client.post(stream_url, json=payload) as r:
                if r.status != 200:
                    error_msg = {
                        "type": "error",
                        "content": f"AI Server Error: {r.status}",
                    }
                    yield f"data: {json.dumps(error_msg)}\n\n"
                    return

                async for line in r.content:
                    if line:
                        decoded_line = line.decode("utf-8").strip()
                        if not decoded_line:
                            continue

                        yield decoded_line + "\n\n"

                        if decoded_line.startswith("data: "):
                            try:
                                json_str = decoded_line[6:]
                                if json_str.strip() == "[DONE]":
                                    continue
                                chunk_data = json.loads(json_str)
                                if chunk_data.get("type") == "token":
                                    ai_accumulated_text.append(
                                        chunk_data.get("content", "")
                                    )
                            except Exception as e:
                                logger.debug(f"스트리밍 JSON 파싱 에러: {e}")

    except TimeoutError:
        logger.error("AI 서버 스트리밍 응답 타임아웃")
        yield f"data: {json.dumps({'type': 'error', 'content': 'AI 서버 응답이 지연되고 있습니다.'})}\n\n"
    except Exception as e:
        logger.error(f"AI 서버 통신 중 오류 발생: {e}")
        yield f"data: {json.dumps({'type': 'error', 'content': 'AI 서버 통신 중 오류가 발생했습니다.'})}\n\n"

    # 스트리밍이 끝나면 최종 생성된 AI 답변을 DB 업데이트
    final_text = "".join(ai_accumulated_text)
    try:
        assistant_msg.content = final_text
        await assistant_msg.asave(update_fields=["content"])
    except Exception as e:
        logger.error(f"스트리밍 DB 업데이트 실패: {e}")
