# ai_server/config.py
"""
AI 서버 환경 설정 모듈

이 모듈은 프로젝트의 설정을 관리합니다.
env/.env.local 파일을 우선적으로 로드하며, 존재하지 않을 경우 프로젝트 루트의 .env 파일을 로드합니다.
설정값은 Pydantic BaseModel을 통해 구조화 및 타입 검증을 거쳐 settings 객체로 노출됩니다.
"""

import os
from pathlib import Path
from typing import Literal
from urllib.parse import quote_plus

from dotenv import load_dotenv
from pydantic import BaseModel, Field

# 프로젝트 루트 경로 (MAI_Help_You/)
BASE_DIR = Path(__file__).resolve().parent.parent

# env/ 디렉토리 내의 설정 파일 경로 정의
ENV_LOCAL_PATH = BASE_DIR / "env" / ".env.local"
ENV_ROOT_PATH = BASE_DIR / ".env"

# 우선순위에 따른 환경 변수 로딩
# override=False: 이미 설정된 OS 환경변수(예: docker-compose의 environment)가 우선됩니다.
if ENV_LOCAL_PATH.exists():
    load_dotenv(dotenv_path=ENV_LOCAL_PATH, override=False)
elif ENV_ROOT_PATH.exists():
    load_dotenv(dotenv_path=ENV_ROOT_PATH, override=False)
else:
    load_dotenv()


class DatabaseSettings(BaseModel):
    """데이터베이스 설정."""

    user: str = Field(default_factory=lambda: os.getenv("DATABASE_USER", "postgres"))
    password: str = Field(default_factory=lambda: os.getenv("DATABASE_PASSWORD", ""))
    name: str = Field(
        default_factory=lambda: os.getenv("DATABASE_NAME", "maple_chatbot_db")
    )
    host: str = Field(default_factory=lambda: os.getenv("DATABASE_HOST", "127.0.0.1"))
    port: int = Field(default_factory=lambda: int(os.getenv("DATABASE_PORT", "5432")))
    connection: str = Field(default_factory=lambda: os.getenv("DB_CONNECTION", ""))
    collection_name: str = Field(
        default_factory=lambda: os.getenv(
            "COLLECTION_NAME", "maplestory_documents_docs"
        )
    )

    def model_post_init(self, __context) -> None:
        # DB_CONNECTION이 비어 있으면 개별 설정값으로 접속 문자열을 조립합니다.
        # (docker-compose에서 DATABASE_HOST=db만 주입해도 동작하도록)
        if not self.connection:
            password = quote_plus(self.password)
            self.connection = (
                f"postgresql+psycopg://{self.user}:{password}"
                f"@{self.host}:{self.port}/{self.name}"
            )


class ModelSettings(BaseModel):
    """AI 모델 설정.

    용도별로 모델을 고릅니다.
      - provider       (LLM_PROVIDER)       : 질문 분류·검색어 재작성·캐릭터명 추출 + 기본 답변 생성
      - answer_provider (ANSWER_LLM_PROVIDER): 답변 생성만 다른 모델로 바꿀 때 (비우면 LLM_PROVIDER와 같음)

    provider 값:
      - "gemini"  : Gemini API (GOOGLE_API_KEY 필요)
      - "deepseek": DeepSeek API (기본값, DEEPSEEK_API_KEY 필요)
      - "local"   : OpenAI 호환 API로 서빙되는 로컬 모델 (vLLM 등, LOCAL_LLM_BASE_URL 필요).
                    구조화 출력이 필요한 보조 호출에는 쓰지 않고 답변 생성에만 사용할 수 있습니다.
    허용되지 않은 값이면 서버 시작 시 설정 검증 오류가 발생합니다.
    """

    provider: Literal["gemini", "deepseek"] = Field(
        default_factory=lambda: os.getenv("LLM_PROVIDER", "deepseek").lower(),
        validate_default=True,
    )
    answer_provider: Literal["gemini", "deepseek", "local"] = Field(
        default_factory=lambda: (
            os.getenv("ANSWER_LLM_PROVIDER") or os.getenv("LLM_PROVIDER", "deepseek")
        ).lower(),
        validate_default=True,
    )
    gemini_model: str = Field(
        default_factory=lambda: os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    )
    deepseek_model: str = Field(
        default_factory=lambda: os.getenv("DEEPSEEK_MODEL", "deepseek-flash")
    )
    deepseek_api_base: str = Field(
        default_factory=lambda: (
            os.getenv("DEEPSEEK_API_BASE", "").strip() or "https://api.deepseek.com"
        )
    )
    # 답변 생성의 사고 모드만 선택합니다. 분류·추출은 항상 비활성화합니다.
    deepseek_thinking_enabled: bool = Field(
        default_factory=lambda: _env_flag("DEEPSEEK_THINKING_ENABLED")
    )
    local_llm_base_url: str = Field(
        default_factory=lambda: os.getenv("LOCAL_LLM_BASE_URL", "")
    )
    local_llm_model: str = Field(
        default_factory=lambda: os.getenv("LOCAL_LLM_MODEL", "merged_qwen")
    )


class ChatSettings(BaseModel):
    """대화 처리 설정."""

    # 프롬프트에 포함할 이전 대화 메시지 수 (현재 질문 제외)
    history_max_messages: int = Field(
        default_factory=lambda: int(os.getenv("CHAT_HISTORY_MAX_MESSAGES", "10"))
    )
    # 이전 대화 메시지 하나당 최대 글자 수 (긴 답변이 토큰을 과도하게 쓰지 않도록 자릅니다)
    history_message_max_chars: int = Field(
        default_factory=lambda: int(os.getenv("CHAT_HISTORY_MESSAGE_MAX_CHARS", "2000"))
    )


def _env_flag(name: str, default: str = "False") -> bool:
    return os.getenv(name, default).lower() in ("true", "1", "yes")


class RagSettings(BaseModel):
    """RAG 지식 베이스 설정."""

    # 공략 문서 폴더 (knowledge/guides/*.md)
    guides_dir: str = Field(
        default_factory=lambda: os.getenv("RAG_GUIDES_DIR", str(BASE_DIR / "knowledge" / "guides"))
    )
    # 검토 전(status: draft) 공략 문서도 적재할지 (개발용, 운영에서는 False)
    include_draft_guides: bool = Field(
        default_factory=lambda: _env_flag("RAG_INCLUDE_DRAFT_GUIDES")
    )
    # 공지 종류별로 가져올 최신 공지 수
    notice_limit: int = Field(default_factory=lambda: int(os.getenv("RAG_NOTICE_LIMIT", "20")))
    # 공략 문서·공지 정기 적재 주기(시간). 0이면 정기 적재를 하지 않습니다.
    sync_interval_hours: float = Field(
        default_factory=lambda: float(os.getenv("RAG_SYNC_INTERVAL_HOURS", "6"))
    )


class ApiSettings(BaseModel):
    """외부 API 키 설정."""

    nexon_api_key: str = Field(default_factory=lambda: os.getenv("NEXON_API_KEY", ""))
    huggingface_token: str = Field(
        default_factory=lambda: os.getenv("HUGGINGFACE_TOKEN", "")
    )
    google_api_key: str = Field(default_factory=lambda: os.getenv("GOOGLE_API_KEY", ""))
    deepseek_api_key: str = Field(
        default_factory=lambda: os.getenv("DEEPSEEK_API_KEY", "")
    )


class LangfuseSettings(BaseModel):
    """Langfuse 모니터링 설정."""

    enabled: bool = Field(
        default_factory=lambda: (
            os.getenv("LANGFUSE_ENABLED", "False").lower() in ("true", "1", "yes")
        )
    )
    secret_key: str | None = Field(
        default_factory=lambda: os.getenv("LANGFUSE_SECRET_KEY")
    )
    public_key: str | None = Field(
        default_factory=lambda: os.getenv("LANGFUSE_PUBLIC_KEY")
    )
    base_url: str = Field(
        default_factory=lambda: os.getenv(
            "LANGFUSE_BASE_URL", "https://cloud.langfuse.com"
        )
    )


class Settings(BaseModel):
    """전체 설정 통합 객체."""

    secret_key: str = Field(default_factory=lambda: os.environ["SECRET_KEY"])
    debug: bool = Field(
        default_factory=lambda: (
            os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")
        )
    )
    allowed_hosts: list[str] = Field(
        default_factory=lambda: [
            h.strip()
            for h in os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
        ]
    )

    redis_url: str = Field(
        default_factory=lambda: os.getenv("REDIS_URL", "redis://localhost:6379/0")
    )
    ai_server_url: str = Field(
        default_factory=lambda: os.getenv("AI_SERVER_URL", "http://localhost:8001")
    )
    # Django → AI 서버 내부 호출 토큰. 비우면 검사하지 않습니다(로컬 개발용, 운영에서는 반드시 설정).
    ai_server_token: str = Field(default_factory=lambda: os.getenv("AI_SERVER_TOKEN", ""))
    # 관리자 API(/api/v1/ai/embed/sync) 토큰. 비우면 관리자 API를 쓸 수 없습니다.
    admin_token: str = Field(default_factory=lambda: os.getenv("AI_ADMIN_TOKEN", ""))

    db: DatabaseSettings = Field(default_factory=DatabaseSettings)
    model: ModelSettings = Field(default_factory=ModelSettings)
    chat: ChatSettings = Field(default_factory=ChatSettings)
    rag: RagSettings = Field(default_factory=RagSettings)
    api: ApiSettings = Field(default_factory=ApiSettings)
    langfuse: LangfuseSettings = Field(default_factory=LangfuseSettings)


# 전역 설정 객체 싱글톤 인스턴스 생성
settings = Settings()
