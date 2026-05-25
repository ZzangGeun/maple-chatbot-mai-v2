# ai_server/main.py
"""
FastAPI AI 서버 진입점

엔드포인트:
  POST /generate — 동기 방식 답변 생성
  POST /stream   — SSE 스트리밍 방식 답변 생성
"""

import json
import logging
import re

import os
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage
from pydantic import BaseModel

# hybrid_builder.py가 넥슨 API, Gemini, 로컬 LLM을 조합한 최종 그래프를 제공합니다.
from ai_server.graph.builder.hybrid_builder import app_graph

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AI_Server")

app = FastAPI(title="MapleStory AI Server (LangGraph)")


class QueryRequest(BaseModel):
    """API 요청 스키마."""

    session_id: str
    message: str


def get_langfuse_handler(session_id: str | None = None, user_id: str | None = None) -> Any | None:
    """
    환경 변수가 설정되어 있을 경우 Langfuse CallbackHandler를 반환합니다.
    (설정이 없으면 None 반환)
    """
    try:
        if os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY"):
            from langfuse.callback import CallbackHandler
            # 넘겨받은 session_id를 세션 추적 키로 연결합니다.
            langfuse_handler = CallbackHandler(session_id=session_id, user_id=user_id)
            return langfuse_handler
    except ImportError:
        logger.warning("langfuse 패키지가 설치되지 않았습니다. 추적을 비활성화합니다.")
    except Exception as e:
        logger.warning(f"Langfuse 초기화 실패 (추적 비활성화): {e}")
    
    return None


def parse_thinking_response(text: str) -> tuple[str, str]:
    """
    Qwen Thinking 모델의 출력에서 <think>...</think> 부분을 분리합니다.

    Args:
        text: LLM 원본 응답 텍스트.

    Returns:
        (thinking_process, final_answer) 튜플.
    """
    if "<think>" in text and "</think>" in text:
        think_match = re.search(r"<think>(.*?)</think>", text, re.DOTALL)
        thinking_process = think_match.group(1).strip() if think_match else ""
        final_answer = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
        return thinking_process, final_answer

    if "<think>" in text:
        # 닫는 태그 없이 <think>가 있는 비정상 케이스
        return "태그 파싱 에러", text.replace("<think>", "").strip()

    return "", text.strip()


@app.post("/generate")
async def generate_response(request: QueryRequest) -> dict:
    """
    동기 방식 AI 답변 생성 엔드포인트.

    Returns:
        {"response": 최종 답변, "thinking": 사고 과정(있을 경우)}
    """
    try:
        logger.info(f"요청 수신 (Session: {request.session_id}): {request.message}")

        config = {"configurable": {"thread_id": request.session_id}}
        
        # Langfuse 설정
        callbacks = []
        langfuse_handler = get_langfuse_handler(session_id=request.session_id)
        if langfuse_handler:
            callbacks.append(langfuse_handler)
            
        if callbacks:
            config["callbacks"] = callbacks

        input_message = HumanMessage(content=request.message)

        output = await app_graph.ainvoke(
            {"messages": [input_message]},
            config=config,
        )

        ai_full_response = output["messages"][-1].content
        thinking, answer = parse_thinking_response(ai_full_response)

        return {"response": answer, "thinking": thinking}

    except ValueError as e:
        logger.error(f"값 오류 발생: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"에러 발생: {e}")
        raise HTTPException(status_code=500, detail="내부 서버 오류가 발생했습니다.")


@app.post("/stream")
async def stream_response(request: QueryRequest) -> StreamingResponse:
    """
    SSE(Server-Sent Events) 스트리밍 답변 생성 엔드포인트.

    generate_node 또는 generate_chat 노드에서 생성된 토큰만 전송하고,
    route/rewrite 등 중간 과정 노드의 출력은 숨깁니다.
    """
    try:
        logger.info(f"스트리밍 요청 수신 (Session: {request.session_id}): {request.message}")

        config = {"configurable": {"thread_id": request.session_id}}
        
        # Langfuse 설정
        callbacks = []
        langfuse_handler = get_langfuse_handler(session_id=request.session_id)
        if langfuse_handler:
            callbacks.append(langfuse_handler)
            
        if callbacks:
            config["callbacks"] = callbacks

        input_message = HumanMessage(content=request.message)

        async def event_generator():
            try:
                async for event in app_graph.astream_events(
                    {"messages": [input_message]},
                    config=config,
                    version="v2",
                ):
                    event_type = event["event"]

                    if event_type == "on_chat_model_stream":
                        node_name = event.get("metadata", {}).get("langgraph_node", "")

                        # 하이브리드 그래프의 Gemini 최종 생성 노드에서만 토큰을 전송합니다.
                        # local_rewrite, local_retrieve 같은 전처리 노드는 스킵합니다.
                        if node_name in ("gemini_generate_rag", "gemini_chat"):
                            chunk = event["data"]["chunk"]
                            if chunk.content:
                                payload = {"type": "token", "content": chunk.content}
                                yield f"data: {json.dumps(payload)}\n\n"

            except Exception as e:
                logger.error(f"스트리밍 중 에러: {e}")
                payload = {"type": "error", "content": str(e)}
                yield f"data: {json.dumps(payload)}\n\n"

            yield "data: [DONE]\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")

    except ValueError as e:
        logger.error(f"잘못된 요청 값으로 인한 스트리밍 시작 실패: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"스트리밍 시작 실패: {e}")
        raise HTTPException(status_code=500, detail="스트리밍 서버 오류가 발생했습니다.")


if __name__ == "__main__":
    # 프로젝트 루트에서 실행해야 절대경로 import가 정상 동작합니다.
    # 실행 명령: python -m ai_server.main
    uvicorn.run(app, host="0.0.0.0", port=8001)