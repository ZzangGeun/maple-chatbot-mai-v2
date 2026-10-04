# apps/chat/services.py
"""
채팅 비즈니스 로직 서비스

뷰(View)에서 분리된 AI 서버 통신, 세션 관리 및 DB 저장 로직을 담당합니다.

AI 서버는 대화 기록을 저장하지 않습니다(stateless).
매 요청마다 최근 대화(history)와 사용자 정보(user_context)를 함께 보냅니다.
"""

import json
import logging
import time
from typing import Any

import aiohttp
from django.conf import settings

from apps.auth.models import UserProfile
from apps.character.models import CharacterLink
from apps.chat.models import ChatMessage, ChatSession, MessageMetadata
from common.exceptions.chat import AiServerUnavailable

logger = logging.getLogger(__name__)

AI_REQUEST_TIMEOUT_SEC = 120
AI_STREAM_TIMEOUT_SEC = 60

# AI 서버에 함께 보낼 이전 대화 메시지 수 (AI 서버도 자체 설정으로 한 번 더 자릅니다)
HISTORY_MAX_MESSAGES = 10

# 현재 프론트엔드는 error 이벤트를 화면에 표시하지 않으므로,
# 실패 시 사용자에게 보일 안내 문구를 token 이벤트로도 보냅니다. (DB에는 저장하지 않습니다)
FAILURE_NOTICE = "답변을 만드는 중 문제가 생겼어요. 잠시 후 다시 시도해 주세요."


def _ai_headers() -> dict[str, str]:
    """AI 서버 내부 호출 토큰 헤더. 토큰을 설정하지 않았으면 빈 헤더를 보냅니다."""
    token = getattr(settings, "AI_SERVER_TOKEN", "")
    return {"X-Internal-Token": token} if token else {}


def get_ai_urls() -> tuple[str, str]:
    """AI 서버 generate/stream 엔드포인트 URL을 반환합니다."""
    ai_base = getattr(settings, "AI_SERVER_BASE_URL", "http://127.0.0.1:8001").rstrip(
        "/"
    )
    return f"{ai_base}/generate", f"{ai_base}/stream"


async def get_recent_history(session: ChatSession) -> list[dict[str, str]]:
    """세션의 최근 대화를 오래된 순으로 반환합니다. 내용이 빈 메시지는 제외합니다."""
    recent = [
        message
        async for message in session.messages.filter(role__in=("user", "assistant"))
        .exclude(content__isnull=True)
        .exclude(content="")
        .order_by("-created_at", "-id")[:HISTORY_MAX_MESSAGES]
    ]
    return [
        {"role": message.role, "content": message.content}
        for message in reversed(recent)
    ]


async def get_user_context(user: Any) -> dict[str, Any]:
    """로그인 사용자의 대표 캐릭터 정보를 반환합니다.

    본인 인증으로 연동한 대표 캐릭터(CharacterLink)를 우선 사용하고,
    없으면 회원가입 시 넥슨 API 키로 확인한 메이플 닉네임을 사용합니다.
    """
    if user is None or not user.is_authenticated:
        return {}

    link = await CharacterLink.objects.filter(user=user, is_main=True).afirst()
    if link:
        return {
            "main_character": {
                "character_name": link.character_name,
                "world_name": link.world_name,
                "ocid": link.ocid,
            }
        }

    profile = await UserProfile.objects.filter(user=user).afirst()
    if profile and profile.maple_nickname:
        return {"main_character": {"character_name": profile.maple_nickname}}

    return {}


async def build_ai_payload(
    session: ChatSession, content: str, user: Any = None
) -> dict[str, Any]:
    """AI 서버 요청 본문을 만듭니다. 현재 메시지를 저장하기 전에 호출해야 합니다."""
    return {
        "session_id": str(session.session_id),
        "message": content,
        "history": await get_recent_history(session),
        "user_context": await get_user_context(user),
    }


async def send_message_async(
    session: ChatSession, content: str, user: Any = None
) -> tuple[ChatMessage, ChatMessage, dict]:
    """
    AI 서버로 메시지를 비동기 전송하고 DB에 저장합니다.
    """
    start_time = time.monotonic()
    payload = await build_ai_payload(session, content, user)

    generate_url, _ = get_ai_urls()

    try:
        timeout = aiohttp.ClientTimeout(total=AI_REQUEST_TIMEOUT_SEC)
        async with aiohttp.ClientSession(timeout=timeout) as client:
            async with client.post(generate_url, json=payload, headers=_ai_headers()) as response:
                if response.status == 200:
                    ai_data = await response.json()
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

    ai_text = ai_data.get("response", "")
    response_time = int((time.monotonic() - start_time) * 1000)

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
        message=assistant_msg,
        response_time_ms=response_time,
        route=ai_data.get("route", ""),
        sources=ai_data.get("sources") or [],
    )

    result_dict = {
        "user_message": {
            "role": "user",
            "content": content,
            "created_at": user_msg.created_at.isoformat(),
        },
        "ai_message": {
            "role": "assistant",
            "content": ai_text,
            "created_at": assistant_msg.created_at.isoformat(),
        },
    }

    return user_msg, assistant_msg, result_dict


def _sse(payload: dict[str, Any] | str) -> str:
    """SSE data 라인을 생성합니다."""
    data = payload if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False)
    return f"data: {data}\n\n"


class StreamRelay:
    """AI 서버의 SSE 이벤트를 읽어 저장할 답변과 메타데이터를 모읍니다."""

    def __init__(self) -> None:
        self.tokens: list[str] = []
        self.route = ""
        self.sources: list[dict[str, Any]] = []
        self.failed = False  # AI 서버가 error 이벤트를 보냈는지
        self.done = False  # AI 서버가 [DONE]을 보냈는지

    @property
    def text(self) -> str:
        return "".join(self.tokens)

    def consume(self, line: str) -> None:
        """SSE 라인 하나를 해석해 상태에 반영합니다."""
        if not line.startswith("data: "):
            return

        data = line[len("data: "):].strip()
        if data == "[DONE]":
            self.done = True
            return

        try:
            event = json.loads(data)
        except json.JSONDecodeError as e:
            logger.debug(f"스트리밍 JSON 파싱 에러: {e}")
            return

        event_type = event.get("type")
        if event_type == "token":
            self.tokens.append(event.get("content", ""))
        elif event_type == "route":
            self.route = event.get("route", "")
        elif event_type == "sources":
            self.sources = event.get("sources") or []
        elif event_type == "error":
            self.failed = True

    def failure_notice(self) -> str:
        """사용자에게 보일 실패 안내 문구. 이미 받은 답변이 있으면 뒤에 덧붙입니다."""
        return f"\n\n({FAILURE_NOTICE})" if self.text else FAILURE_NOTICE


async def _save_stream_result(
    session: ChatSession, relay: StreamRelay, started_at: float
) -> None:
    """스트리밍으로 받은 답변과 메타데이터를 저장합니다. 받은 토큰이 없으면 저장하지 않습니다."""
    if not relay.text:
        return

    try:
        assistant_msg = await ChatMessage.objects.acreate(
            session=session,
            role="assistant",
            content=relay.text,
        )
        await MessageMetadata.objects.acreate(
            message=assistant_msg,
            response_time_ms=int((time.monotonic() - started_at) * 1000),
            route=relay.route,
            sources=relay.sources,
        )
    except Exception as e:
        logger.error(f"스트리밍 답변 저장 실패: {e}")


async def stream_message_generator(session: ChatSession, content: str, user: Any = None):
    """
    AI 서버의 SSE 스트림을 클라이언트에 그대로 전달하고, 끝나면 답변을 DB에 저장합니다.

    어떤 경우에도 마지막에 data: [DONE]을 한 번 보냅니다.
    """
    started_at = time.monotonic()
    payload = await build_ai_payload(session, content, user)

    # 사용자 메시지는 AI 응답 성공 여부와 관계없이 먼저 저장합니다.
    await ChatMessage.objects.acreate(
        session=session,
        role="user",
        content=content,
    )

    relay = StreamRelay()
    error_message = ""
    _, stream_url = get_ai_urls()

    try:
        try:
            timeout = aiohttp.ClientTimeout(total=AI_STREAM_TIMEOUT_SEC)
            async with aiohttp.ClientSession(timeout=timeout) as client:
                async with client.post(stream_url, json=payload, headers=_ai_headers()) as r:
                    if r.status != 200:
                        logger.error(f"AI 서버 스트리밍 에러: {r.status}")
                        error_message = "AI 서버 오류가 발생했습니다."
                    else:
                        async for raw_line in r.content:
                            line = raw_line.decode("utf-8").strip()
                            if not line:
                                continue

                            was_failed = relay.failed
                            relay.consume(line)
                            if relay.done:
                                # [DONE]은 아래에서 직접 보냅니다.
                                break

                            yield line + "\n\n"
                            if relay.failed and not was_failed:
                                yield _sse({"type": "token", "content": relay.failure_notice()})

        except TimeoutError:
            logger.error("AI 서버 스트리밍 응답 타임아웃")
            error_message = "AI 서버 응답이 지연되고 있습니다."
        except Exception as e:
            logger.error(f"AI 서버 통신 중 오류 발생: {e}")
            error_message = "AI 서버 통신 중 오류가 발생했습니다."

        if not relay.done and not relay.failed and not error_message:
            logger.error("AI 서버 스트림이 종료 신호 없이 끊겼습니다.")
            error_message = "AI 서버 응답이 중간에 끊겼습니다."

        # AI 서버가 이미 error 이벤트를 보냈다면 안내 문구를 보냈으므로 중복으로 보내지 않습니다.
        if error_message and not relay.failed:
            yield _sse({"type": "error", "content": error_message})
            yield _sse({"type": "token", "content": relay.failure_notice()})

        yield _sse("[DONE]")

    finally:
        # 클라이언트가 중간에 연결을 끊어도 받은 만큼은 저장합니다.
        await _save_stream_result(session, relay, started_at)
