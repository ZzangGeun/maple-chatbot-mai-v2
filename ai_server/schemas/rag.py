from pydantic import BaseModel

class SingleQueryRequest(BaseModel):
    """일회성 RAG 질의 스키마."""
    query: str
    top_k: int = 3
