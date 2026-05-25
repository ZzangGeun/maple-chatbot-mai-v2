# 시스템 아키텍처

MAI Help You의 백엔드 시스템은 역할에 따라 2개의 서버로 완전히 분리된 **Dual-Server Architecture**를 채택했습니다.

## 1. 아키텍처 다이어그램 (개념도)

```mermaid
graph TD
    Client[Client (React / Browser)] -->|HTTP / SSE| Django[Django API Server\n:8000]
    
    subgraph "Main Backend"
    Django --> DB[(PostgreSQL\nUser, Session, Chat DB)]
    Django --> NexonAPI[Nexon Open API]
    end

    subgraph "AI Engine"
    Django -->|HTTP POST (Internal)| FastAPI[FastAPI AI Server\n:8001]
    FastAPI --> VectorDB[(Vector DB\nFAISS or PGVector)]
    FastAPI --> LLM((LLM\nGemini / Qwen))
    end
```

## 2. 모듈별 역할

### 2.1 Django Server (`/apps`, `/config`)
- **역할**: 인증(OAuth/JWT), 세션 관리, DB ORM(사용자 프로필, 채팅 기록 저장), 외부 API(Nexon Open API) 연동, 프론트엔드 라우팅 서빙.
- **특징**: "Thin Views, Fat Services" 패턴을 적용하여, 라우터(views)는 가볍게 유지하고 비즈니스 로직(AI 호출, 데이터 전처리)은 `services.py`에 격리.
- **주요 스택**: Django 5.x, psycopg2

### 2.2 FastAPI Server (`/ai_server`)
- **역할**: 대용량 텍스트 추론, 프롬프트 엔지니어링, 문서 벡터화(Embedding) 및 검색(Retrieval).
- **특징**: 메인 서버와는 완전히 독립적으로 동작. 상태(State)를 가지지 않으며(Stateless), Django 서버가 넘겨주는 Context(유저 질문, 캐릭터 정보 등)를 기반으로 답변만 생성하여 스트리밍 반환.
- **주요 스택**: FastAPI, LangChain, LangGraph, Pydantic

## 3. 왜 듀얼 서버인가?
- **의존성 충돌 방지**: AI 라이브러리(Torch, Langchain 등)는 매우 무겁고 버전 충돌이 잦습니다. 이를 일반적인 웹 비즈니스 로직(Django)과 한 환경(`.venv`)에 두면 배포와 유지보수가 극도로 힘들어집니다.
- **독립적 스케일링**: 트래픽이 몰릴 때, AI 추론 로직(FastAPI) 쪽에만 GPU 인스턴스를 할당하여 유연하게 스케일 아웃할 수 있습니다.
