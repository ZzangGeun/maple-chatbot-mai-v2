import json
import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage

from ai_server.api.deps import get_graph
from ai_server.schemas.chat import ChatResponse, QueryRequest
from ai_server.services.chat import build_langchain_config, parse_thinking_response

logger = logging.getLogger("AI_Server.ChatRouter")
router = APIRouter()

# lifespan에서 app.state에 바인딩된 컴파일된 LangGraph를 주입받는 타입 별칭
Graph = Annotated[Any, Depends(get_graph)]


@router.post("/generate", response_model=ChatResponse)
async def generate_response(request: QueryRequest, graph: Graph) -> ChatResponse:
    """
    동기 방식 AI 답변 생성 엔드포인트.

    Returns:
        ChatResponse: 최종 답변(response)과 사고 과정(thinking).
    """
    try:
        logger.info(f"요청 수신 (Session: {request.session_id}): {request.message}")

        config = build_langchain_config(request.session_id)
        input_message = HumanMessage(content=request.message)

        output = await graph.ainvoke(
            {"messages": [input_message]},
            config=config,
        )

        ai_full_response = output["messages"][-1].content
        thinking, answer = parse_thinking_response(ai_full_response)

        return ChatResponse(response=answer, thinking=thinking)

    except ValueError as e:
        logger.error(f"값 오류 발생: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"에러 발생: {e}")
        raise HTTPException(status_code=500, detail="내부 서버 오류가 발생했습니다.")


@router.post("/stream")
async def stream_response(request: QueryRequest, graph: Graph) -> StreamingResponse:
    """
    SSE(Server-Sent Events) 스트리밍 답변 생성 엔드포인트.

    최종 생성 노드의 토큰만 전송하고 중간 과정 노드의 출력은 숨깁니다.
    """
    try:
        logger.info(
            f"스트리밍 요청 수신 (Session: {request.session_id}): {request.message}"
        )

        config = build_langchain_config(request.session_id)
        input_message = HumanMessage(content=request.message)

        async def event_generator():
            try:
                async for event in graph.astream_events(
                    {"messages": [input_message]},
                    config=config,
                    version="v2",
                ):
                    event_type = event["event"]

                    if event_type == "on_chat_model_stream":
                        node_name = event.get("metadata", {}).get("langgraph_node", "")

                        if node_name in ("local_generate", "chat_node"):
                            chunk = event["data"]["chunk"]
                            if chunk.content:
                                payload = {"type": "token", "content": chunk.content}
                                yield f"data: {json.dumps(payload)}\n\n"

            except Exception as e:
                logger.error(f"스트리밍 중 에러: {e}")
                payload = {"type": "error", "content": "내부 서버 오류가 발생했습니다."}
                yield f"data: {json.dumps(payload)}\n\n"

            yield "data: [DONE]\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")

    except ValueError as e:
        logger.error(f"잘못된 요청 값으로 인한 스트리밍 시작 실패: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"스트리밍 시작 실패: {e}")
        raise HTTPException(
            status_code=500, detail="스트리밍 서버 오류가 발생했습니다."
        )
