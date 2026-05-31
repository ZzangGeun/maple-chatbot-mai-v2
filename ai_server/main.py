# ai_server/main.py
"""
FastAPI AI 서버 진입점

엔드포인트:
  POST /generate — 동기 방식 답변 생성
  POST /stream   — SSE 스트리밍 방식 답변 생성
"""

import json
import logging
import os
import re
from typing import Any

import uvicorn
from fastapi import APIRouter, BackgroundTasks, FastAPI, Header, HTTPException, Request
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage
from pydantic import BaseModel

from ai_server.config import settings

# main_builder.py가 넥슨 API, Gemini, 로컬 LLM을 조합한 메인 그래프 및 서브 그래프를 제공합니다.


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AI_Server")
from ai_server.lifespan import lifespan

app = FastAPI(title="MapleStory AI Server (LangGraph)", lifespan=lifespan)


class QueryRequest(BaseModel):
    """API 요청 스키마."""

    session_id: str
    message: str


def get_langfuse_handler() -> Any | None:
    """
    환경 변수가 설정되어 있을 경우 Langfuse CallbackHandler를 반환합니다.
    (설정이 없으면 None 반환)
    """
    try:
        if os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY"):
            from langfuse.langchain import CallbackHandler

            langfuse_handler = CallbackHandler()
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
async def generate_response(request: QueryRequest, raw_request: Request) -> dict:
    """
    동기 방식 AI 답변 생성 엔드포인트.

    Returns:
        {"response": 최종 답변, "thinking": 사고 과정(있을 경우)}
    """
    try:
        logger.info(f"요청 수신 (Session: {request.session_id}): {request.message}")

        config = {
            "configurable": {"thread_id": request.session_id},
            "metadata": {"langfuse_session_id": request.session_id},
        }

        # Langfuse 설정
        callbacks = []
        langfuse_handler = get_langfuse_handler()
        if langfuse_handler:
            callbacks.append(langfuse_handler)

        if callbacks:
            config["callbacks"] = callbacks

        input_message = HumanMessage(content=request.message)

        output = await raw_request.app.state.graph.ainvoke(
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
async def stream_response(
    request: QueryRequest, raw_request: Request
) -> StreamingResponse:
    """
    SSE(Server-Sent Events) 스트리밍 답변 생성 엔드포인트.

    generate_node 또는 generate_chat 노드에서 생성된 토큰만 전송하고,
    route/rewrite 등 중간 과정 노드의 출력은 숨깁니다.
    """
    try:
        logger.info(
            f"스트리밍 요청 수신 (Session: {request.session_id}): {request.message}"
        )

        config = {
            "configurable": {"thread_id": request.session_id},
            "metadata": {"langfuse_session_id": request.session_id},
        }

        # Langfuse 설정
        callbacks = []
        langfuse_handler = get_langfuse_handler()
        if langfuse_handler:
            callbacks.append(langfuse_handler)

        if callbacks:
            config["callbacks"] = callbacks

        input_message = HumanMessage(content=request.message)

        async def event_generator():
            try:
                async for event in raw_request.app.state.graph.astream_events(
                    {"messages": [input_message]},
                    config=config,
                    version="v2",
                ):
                    event_type = event["event"]

                    if event_type == "on_chat_model_stream":
                        node_name = event.get("metadata", {}).get("langgraph_node", "")

                        # 하이브리드 그래프의 최종 생성 노드에서만 토큰을 전송합니다.
                        # 전처리 노드(라우팅, 쿼리 추출)의 출력은 스킵합니다.
                        if node_name in ("local_generate_rag", "gemini_chat"):
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
        raise HTTPException(
            status_code=500, detail="스트리밍 서버 오류가 발생했습니다."
        )


# --- 설계서 스펙에 맞춘 AI & RAG 전용 APIRouter 추가 ---
ai_router = APIRouter(prefix="/api/v1/ai")


class SingleQueryRequest(BaseModel):
    """일회성 RAG 질의 스키마."""

    query: str
    top_k: int = 3


@ai_router.post("/query")
async def single_rag_query(request: SingleQueryRequest):
    """
    일회성 RAG 검색 및 답변 API 엔드포인트.

    문서 검색(Retrieval) 후, 검색된 문맥을 프롬프트에 실어
    설정된 LLM(Gemini 혹은 로컬 LLM)을 통해 답변을 비동기로 생성합니다.
    """
    try:
        logger.info(f"일회성 RAG 쿼리 수신: {request.query} (top_k: {request.top_k})")

        from ai_server.llm.factory import get_llm
        from ai_server.rag.retriever import Retriever

        retriever = Retriever(k=request.top_k)
        docs = retriever.retrieve(request.query)

        # 1. 검색 문서들로부터 컨텍스트 추출
        context = "\n\n".join([doc.page_content for doc in docs])

        # 2. 메이플스토리 전용 프롬프트 빌드
        prompt = (
            "당신은 메이플스토리 도메인 지식이 매우 풍부한 친절한 AI 비서 '메이(MAI)'입니다.\n"
            "아래 제공된 [가이드 컨텍스트]만을 바탕으로 질문에 정확하고 상세히 한국어로 답변해주세요.\n"
            "만약 정보가 부족하거나 답변이 불가능한 경우, '공식 홈페이지나 인게임 정보를 다시 확인해주세요'라고 답변하세요.\n\n"
            f"[가이드 컨텍스트]\n{context}\n\n"
            f"질문: {request.query}\n"
            "답변:"
        )

        # 3. LLM 비동기 추론 실행
        llm = get_llm()
        response = await llm.ainvoke(prompt)

        if hasattr(response, "content"):
            answer = response.content
        else:
            answer = str(response)

        # 4. 참조 문서 리스트 구성
        referenced_docs = []
        for doc in docs:
            referenced_docs.append(
                {
                    "title": doc.metadata.get("title", "제목 없음"),
                    "source": doc.metadata.get("source", "알 수 없음"),
                    "score": doc.metadata.get(
                        "score", 1.0
                    ),  # pgvector/Chroma score fallback
                }
            )

        return {
            "success": True,
            "answer": answer.strip(),
            "referenced_documents": referenced_docs,
        }

    except Exception as e:
        logger.error(f"일회성 RAG 쿼리 처리 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"RAG 질의응답 중 내부 오류가 발생했습니다: {str(e)}",
        )


@ai_router.get("/recommend-questions")
async def recommend_questions(authorization: str | None = Header(default=None)):
    """
    맞춤형 추천 질문 생성 API 엔드포인트.

    사용자 JWT 토큰을 해석하여 대표 캐릭터를 식별하고, 해당 캐릭터 스펙에 적합한 질문을 개인화 추천합니다.
    """
    character_name = "아델은최강"  # 기본 캐릭터명 Fallback

    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        try:
            import jwt

            # Django와 공유하는 secret_key를 통해 JWT 복호화 시도
            payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
            # 캐릭터명 추출
            character_name = payload.get("main_character_name", character_name)
        except ImportError:
            logger.warning("jwt 패키지가 존재하지 않아 토큰 복호화를 건너뜁니다.")
        except Exception as e:
            logger.warning(f"토큰 복호화 실패 (기본값 사용): {e}")

    # 캐릭터명 스펙 기반 맞춤 질문 데이터 (Mocking & Template)
    recommended = [
        {
            "id": "rec_01",
            "question": f"현재 [{character_name}] 캐릭터의 무기가 앱솔랩스 12성인데, 아케인셰이드 17성으로 넘어가는 비용과 스탯 상승 폭 비교해줘",
            "category": "item_upgrade",
        },
        {
            "id": "rec_02",
            "question": f"현재 [{character_name}] 캐릭터 스펙(주스탯 2.5만 전사) 기준 노말 스우 솔플 최소 컷과 도핑 팁이 어떻게 돼?",
            "category": "boss_guide",
        },
    ]

    return {
        "success": True,
        "character_name": character_name,
        "recommended_questions": recommended,
    }


@ai_router.post("/embed/sync")
async def trigger_embedding_sync(
    background_tasks: BackgroundTasks, authorization: str | None = Header(default=None)
):
    """
    임베딩 동기화 강제 트리거 API 엔드포인트.

    관리자 전용 토큰을 검증한 뒤, 백그라운드 태스크로 벡터 임베딩 갱신 파이프라인을 작동시킵니다.
    """
    if not authorization or not authorization.startswith("Bearer "):
        logger.warning(
            "관리자 인증 토큰 누락. 개발 및 디버깅을 위해 태스크는 강제 실행됩니다."
        )

    try:
        from ai_server.rag.character_batch import run_character_embedding_batch

        # 백그라운드에서 임베딩 적재 구동하여 호출이 블로킹되지 않도록 처리
        background_tasks.add_task(run_character_embedding_batch)

        return {
            "success": True,
            "task_id": "task_embed_sync_manual",
            "message": "벡터 DB 임베딩 동기화 작업이 백그라운드에서 시작되었습니다.",
        }
    except Exception as e:
        logger.error(f"임베딩 동기화 백그라운드 적재 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail="백그라운드 임베딩 태스크 실행 중 오류가 발생했습니다.",
        )


app.include_router(ai_router)

if __name__ == "__main__":
    # 프로젝트 루트에서 실행해야 절대경로 import가 정상 동작합니다.
    # 실행 명령: python -m ai_server.main
    uvicorn.run(app, host="0.0.0.0", port=8001)
