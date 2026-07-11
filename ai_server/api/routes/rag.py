import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from ai_server.api.deps import require_admin_token
from ai_server.schemas.rag import (
    EmbedSyncResponse,
    RAGQueryResponse,
    SingleQueryRequest,
)
from ai_server.services.rag import process_single_rag_query

logger = logging.getLogger("AI_Server.RAGRouter")
router = APIRouter()


@router.post("/query", response_model=RAGQueryResponse)
async def single_rag_query(request: SingleQueryRequest) -> RAGQueryResponse:
    """
    일회성 RAG 검색 및 답변 API 엔드포인트.
    """
    try:
        logger.info(f"일회성 RAG 쿼리 수신: {request.query} (top_k: {request.top_k})")
        return await process_single_rag_query(request.query, request.top_k)

    except Exception as e:
        logger.error(f"일회성 RAG 쿼리 처리 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail="RAG 질의응답 중 내부 오류가 발생했습니다.",
        )


@router.post(
    "/embed/sync",
    response_model=EmbedSyncResponse,
    dependencies=[Depends(require_admin_token)],
)
async def trigger_embedding_sync(
    background_tasks: BackgroundTasks,
) -> EmbedSyncResponse:
    """
    임베딩 동기화 강제 트리거 API 엔드포인트. (관리자 인증 필요)
    """
    try:
        from ai_server.rag.character_batch import run_character_embedding_batch

        # 백그라운드에서 임베딩 적재 구동하여 호출이 블로킹되지 않도록 처리
        background_tasks.add_task(run_character_embedding_batch)

        return EmbedSyncResponse(
            task_id="task_embed_sync_manual",
            message="벡터 DB 임베딩 동기화 작업이 백그라운드에서 시작되었습니다.",
        )
    except Exception as e:
        logger.error(f"임베딩 동기화 백그라운드 적재 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail="백그라운드 임베딩 태스크 실행 중 오류가 발생했습니다.",
        )
