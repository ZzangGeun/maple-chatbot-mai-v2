from pydantic import BaseModel


class SingleQueryRequest(BaseModel):
    """일회성 RAG 질의 요청 스키마."""

    query: str
    top_k: int = 3


class ReferencedDocument(BaseModel):
    """RAG 답변에 참조된 문서 메타데이터."""

    title: str = "제목 없음"
    source: str = "알 수 없음"
    score: float = 1.0


class RAGQueryResponse(BaseModel):
    """일회성 RAG 질의 응답 스키마."""

    success: bool = True
    answer: str
    referenced_documents: list[ReferencedDocument] = []


class EmbedSyncResponse(BaseModel):
    """임베딩 동기화 트리거 응답 스키마."""

    success: bool = True
    task_id: str
    message: str
