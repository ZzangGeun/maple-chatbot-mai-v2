import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from ai_server.api.deps import get_graph
from ai_server.schemas.chat import ChatResponse, QueryRequest
from ai_server.services.chat import generate_chat_response, stream_chat_events

logger = logging.getLogger("AI_Server.ChatRouter")
router = APIRouter()

# lifespan에서 app.state에 바인딩된 컴파일된 LangGraph를 주입받는 타입 별칭
Graph = Annotated[Any, Depends(get_graph)]


def _log_request(kind: str, request: QueryRequest) -> None:
    logger.info(
        f"{kind} 요청 수신 (Session: {request.session_id}, "
        f"이전 대화 {len(request.history)}건): {request.message[:50]}"
    )


@router.post("/generate", response_model=ChatResponse)
async def generate_response(request: QueryRequest, graph: Graph) -> ChatResponse:
    """
    동기 방식 AI 답변 생성 엔드포인트.

    Returns:
        ChatResponse: 최종 답변(response), 질문 분류 결과(route), 근거 문서(sources).
    """
    _log_request("동기", request)
    try:
        return await generate_chat_response(graph, request)
    except Exception as e:
        logger.error(f"답변 생성 실패: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="내부 서버 오류가 발생했습니다.")


@router.post("/stream")
async def stream_response(request: QueryRequest, graph: Graph) -> StreamingResponse:
    """
    SSE(Server-Sent Events) 스트리밍 답변 생성 엔드포인트.

    이벤트 규격은 ai_server.services.chat 모듈 docstring을 참고하세요.
    """
    _log_request("스트리밍", request)
    return StreamingResponse(
        stream_chat_events(graph, request),
        media_type="text/event-stream",
        # 프록시(Nginx 등)가 응답을 모아서 보내지 않도록 버퍼링을 끕니다.
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
