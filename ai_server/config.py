# ai_server/config.py
"""
AI 서버 환경 설정 모듈

이 모듈은 프로젝트의 설정을 관리합니다.
env/.env.local 파일을 우선적으로 로드하며, 존재하지 않을 경우 프로젝트 루트의 .env 파일을 로드합니다.
설정값은 Pydantic BaseModel을 통해 구조화 및 타입 검증을 거쳐 settings 객체로 노출됩니다.
"""

import os
from pathlib import Path
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# 프로젝트 루트 경로 (MAI_Help_You/)
BASE_DIR = Path(__file__).resolve().parent.parent

# env/ 디렉토리 내의 설정 파일 경로 정의
ENV_LOCAL_PATH = BASE_DIR / "env" / ".env.local"
ENV_ROOT_PATH = BASE_DIR / ".env"

# 우선순위에 따른 환경 변수 로딩
if ENV_LOCAL_PATH.exists():
    load_dotenv(dotenv_path=ENV_LOCAL_PATH, override=True)
elif ENV_ROOT_PATH.exists():
    load_dotenv(dotenv_path=ENV_ROOT_PATH, override=True)
else:
    load_dotenv()


class DatabaseSettings(BaseModel):
    """데이터베이스 설정."""
    user: str = Field(default_factory=lambda: os.getenv("DATABASE_USER", "postgres"))
    password: str = Field(default_factory=lambda: os.getenv("DATABASE_PASSWORD", ""))
    name: str = Field(default_factory=lambda: os.getenv("DATABASE_NAME", "maple_chatbot_db"))
    host: str = Field(default_factory=lambda: os.getenv("DATABASE_HOST", "127.0.0.1"))
    port: int = Field(default_factory=lambda: int(os.getenv("DATABASE_PORT", "5432")))
    connection: str = Field(default_factory=lambda: os.getenv("DB_CONNECTION", ""))
    collection_name: str = Field(default_factory=lambda: os.getenv("COLLECTION_NAME", "maplestory_documents_docs"))


class ModelSettings(BaseModel):
    """AI 모델 설정."""
    provider: str = Field(default_factory=lambda: os.getenv("LLM_PROVIDER", "local").lower())
    model_path: str = Field(default_factory=lambda: os.getenv("MODEL_PATH", ""))
    base_model: str = Field(default_factory=lambda: os.getenv("BASE_MODEL", ""))


class ApiSettings(BaseModel):
    """외부 API 키 설정."""
    nexon_api_key: str = Field(default_factory=lambda: os.getenv("NEXON_API_KEY", ""))
    huggingface_token: str = Field(default_factory=lambda: os.getenv("HUGGINGFACE_TOKEN", ""))
    google_api_key: str = Field(default_factory=lambda: os.getenv("GOOGLE_API_KEY", ""))


class LangfuseSettings(BaseModel):
    """Langfuse 모니터링 설정."""
    enabled: bool = Field(default_factory=lambda: os.getenv("LANGFUSE_ENABLED", "False").lower() in ("true", "1", "yes"))
    secret_key: str | None = Field(default_factory=lambda: os.getenv("LANGFUSE_SECRET_KEY"))
    public_key: str | None = Field(default_factory=lambda: os.getenv("LANGFUSE_PUBLIC_KEY"))
    base_url: str = Field(default_factory=lambda: os.getenv("LANGFUSE_BASE_URL", "https://cloud.langfuse.com"))


class Settings(BaseModel):
    """전체 설정 통합 객체."""
    secret_key: str = Field(default_factory=lambda: os.environ["SECRET_KEY"])
    debug: bool = Field(default_factory=lambda: os.getenv("DEBUG", "False").lower() in ("true", "1", "yes"))
    allowed_hosts: list[str] = Field(default_factory=lambda: [h.strip() for h in os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")])
    
    redis_url: str = Field(default_factory=lambda: os.getenv("REDIS_URL", "redis://localhost:6379/0"))
    ai_server_url: str = Field(default_factory=lambda: os.getenv("AI_SERVER_URL", "http://localhost:8001"))
    
    db: DatabaseSettings = Field(default_factory=DatabaseSettings)
    model: ModelSettings = Field(default_factory=ModelSettings)
    api: ApiSettings = Field(default_factory=ApiSettings)
    langfuse: LangfuseSettings = Field(default_factory=LangfuseSettings)


# 전역 설정 객체 싱글톤 인스턴스 생성
settings = Settings()
