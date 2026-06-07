from pydantic import BaseModel

class QueryRequest(BaseModel):
    """API 요청 스키마."""
    session_id: str
    message: str
