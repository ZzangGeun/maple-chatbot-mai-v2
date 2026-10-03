# MAI Help You

메이플스토리 유저를 위한 AI 챗봇 서비스입니다. 게임 지식은 RAG(문서 검색 기반 생성)로, 캐릭터 정보는 넥슨 Open API로 가져와 LLM이 근거를 바탕으로 답변합니다. 챗봇은 메이플스토리 마스코트 '돌의 정령' 말투(~담)로 대답합니다.

## 주요 기능

- **메이플스토리 지식 Q&A**: 공지·이벤트 등 게임 문서를 검색해 근거 문서 번호([1], [2])와 함께 답변합니다.
- **캐릭터 정보 조회**: 질문 속 캐릭터를 넥슨 Open API로 조회해 답변에 활용합니다.
  - 로그인 사용자는 "내 캐릭터"로 물으면 대표 캐릭터를 조회합니다.
  - 질문에 필요한 정보(스탯, 장비, 심볼, HEXA, 유니온 등)만 골라서 조회합니다.
  - 캐릭터 정보와 게임 지식이 모두 필요한 질문(예: "이 캐릭터로 하드 루시드 잡을 수 있어?")은 두 정보를 함께 사용합니다.
- **실시간 답변 스트리밍**: 답변을 SSE(Server-Sent Events)로 생성되는 대로 보냅니다.
- **회원가입·캐릭터 연동**: 가입 시 넥슨 API 키로 대표 캐릭터를 확인하고, 인게임 소개글 인증 코드로 캐릭터를 연동합니다.
- **기타 화면**: 캐릭터 검색, 공지·랭킹 홈, 커뮤니티 게시판

## 아키텍처

```
브라우저 (React)
   │  /api/v1/*
   ▼
Django :8000 ── 인증·세션, 대화 기록 저장, 넥슨 Open API (PostgreSQL, Redis)
   │  POST /stream  {message, 최근 대화, 대표 캐릭터}
   ▼
AI 서버 (FastAPI + LangGraph) :8001 ── 대화 기록을 저장하지 않음(stateless)
   ├─ LLM: Gemini / DeepSeek / 로컬 모델(OpenAI 호환 서버)
   ├─ 지식 검색: pgvector + BM25
   └─ 캐릭터 조회: 넥슨 Open API
```

Django와 AI 서버를 분리한 이유는 [ADR 001](docs/adr/001_use_fastapi.md)과 [시스템 아키텍처](docs/project/03_architecture.md)를 참고하세요.

## 빠른 시작

### 준비물

- Python 3.11, Node.js 18 이상
- Docker (PostgreSQL + pgvector, Redis 실행용)
- API 키: 넥슨 Open API 키, Gemini API 키(`GOOGLE_API_KEY`) 또는 DeepSeek API 키

### 1. 환경 변수 파일 만들기

```bash
mkdir env
cp .env.example env/.env.local    # Windows PowerShell: Copy-Item .env.example env/.env.local
```

`env/.env.local`을 열어 최소한 `SECRET_KEY`, `DATABASE_PASSWORD`, `NEXON_API_KEY`, `GOOGLE_API_KEY`를 채웁니다. 각 변수는 [환경 설정](#환경-설정)에서 설명합니다.

### 2-A. 로컬 개발 환경으로 실행 (권장)

답변이 실시간으로 스트리밍되는 구성입니다.

```bash
# 1) DB와 Redis만 Docker로 실행
docker compose --env-file env/.env.local up -d db redis

# 2) Python 가상환경과 의존성 설치
python -m venv .venv
.venv\Scripts\activate             # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
pip install pytest pytest-django pytest-asyncio   # 테스트용

# 3) DB 마이그레이션
python manage.py migrate
```

이어서 터미널 3개에서 각각 실행합니다. 모든 Python 명령은 프로젝트 루트에서, 가상환경을 활성화한 상태로 실행해야 합니다.

```bash
python -m ai_server.main                              # AI 서버 → http://localhost:8001
uvicorn config.asgi:application --reload --port 8000  # Django(ASGI) → http://localhost:8000
cd frontend && npm install && npm run dev             # 프론트엔드 → http://localhost:5173
```

브라우저에서 **http://localhost:5173** 에 접속합니다. Vite 개발 서버가 `/api` 요청을 Django로 넘겨줍니다.

> `python manage.py runserver`로도 실행되지만, runserver(WSGI)는 스트리밍 응답을 끝까지 모았다가 한 번에 보냅니다. 답변이 실시간으로 보여야 하면 위처럼 uvicorn(ASGI)을 사용하세요.

### 2-B. Docker Compose로 전체 실행

```bash
docker compose --env-file env/.env.local up --build
```

http://localhost:8000 에서 Django가 빌드된 프론트엔드(`static/dist/`)를 서빙합니다. 마이그레이션은 컨테이너 시작 시 자동으로 실행됩니다.

> 현재 Compose 구성은 개발용입니다. Django가 runserver로 실행되므로 답변이 한 번에 표시됩니다. AI 서버 이미지는 PyTorch 등을 포함해 용량이 큽니다.

### 3. 지식 검색 데이터 준비 (선택)

지식 질문에 답하려면 벡터 DB에 문서가 있어야 합니다. 원본 데이터 폴더(`data/`, `rag_documents/`)는 git에 포함되어 있지 않습니다.

```bash
# 넥슨 Open API에서 최신 공지·이벤트를 가져와 Redis(rag_docs:notices)에 저장
python manage.py shell -c "from apps.core.services import sync_notices_to_rag; sync_notices_to_rag()"

# rag_documents/**/*.json과 Redis의 rag_docs:* 문서를 임베딩해 pgvector에 적재
python -m ai_server.rag.vectorstore
```

처음 실행하면 임베딩 모델(`Qwen/Qwen3-Embedding-0.6B`, 1GB 이상)을 내려받습니다. 적재 스크립트는 기존 문서를 지우지 않으므로, 여러 번 실행하면 문서가 중복으로 쌓입니다.

## 환경 설정

환경 변수는 `env/.env.local` → 루트 `.env` 순서로 읽고, 이미 설정된 OS 환경 변수가 가장 우선합니다. 전체 목록과 기본값은 [`.env.example`](.env.example)에 있습니다.

| 변수 | 필수 | 설명 |
| :--- | :---: | :--- |
| `SECRET_KEY` | ✅ | Django·AI 서버 공용 비밀 키. 테스트 실행에도 필요합니다. |
| `DATABASE_*` | ✅ | PostgreSQL 접속 정보 (`DATABASE_HOST=127.0.0.1`은 로컬 개발 기준) |
| `REDIS_URL` | ✅ | 공지·랭킹 캐시와 RAG용 공지 문서 저장소 |
| `NEXON_API_KEY` | ✅ | 캐릭터 검색·연동, 공지·랭킹 조회 |
| `NEXON_REQUESTS_PER_SECOND` |  | 넥슨 API 초당 요청 수 상한(서버 프로세스마다 적용). 기본 5는 개발 단계 키 기준이며, 서비스 단계 키로 바꾸면 올립니다. |
| `NEXON_CACHE_ENABLED` |  | 넥슨 API 응답을 Redis에 캐싱해 Django와 AI 서버가 공유 (기본 `True`) |
| `LLM_PROVIDER` |  | 질문 분류·검색어 재작성·캐릭터명 추출과 기본 답변 생성 모델: `gemini`(기본) \| `deepseek` |
| `ANSWER_LLM_PROVIDER` |  | 답변 생성만 다른 모델로 바꿀 때: `gemini` \| `deepseek` \| `local` (비우면 `LLM_PROVIDER`) |
| `GOOGLE_API_KEY` / `GEMINI_MODEL` | Gemini 사용 시 | Gemini API 키와 모델명 (기본 `gemini-2.5-flash`) |
| `DEEPSEEK_API_KEY` / `DEEPSEEK_MODEL` | DeepSeek 사용 시 | DeepSeek API 키와 모델명 (기본 `deepseek-chat`) |
| `LOCAL_LLM_BASE_URL` / `LOCAL_LLM_MODEL` | local 사용 시 | OpenAI 호환 서버 주소와 모델명 |
| `CHAT_HISTORY_MAX_MESSAGES` |  | 프롬프트에 넣을 이전 대화 수 (기본 10) |
| `AI_SERVER_URL` |  | Django가 호출할 AI 서버 주소 (기본 `http://127.0.0.1:8001`) |
| `LANGFUSE_*` |  | LLM 호출 추적(Langfuse). `LANGFUSE_ENABLED=True`일 때만 동작 |
| `ADS_*` |  | 애드센스 광고 설정 |

`LLM_PROVIDER`, `ANSWER_LLM_PROVIDER`에 허용되지 않은 값을 넣으면 AI 서버가 시작할 때 설정 오류를 냅니다.

### LLM 바꾸기

- **DeepSeek**: `LLM_PROVIDER=deepseek`와 `DEEPSEEK_API_KEY`를 설정합니다. 질문 분류 등 보조 호출과 답변 생성이 모두 DeepSeek로 바뀝니다. 실제 DeepSeek API로는 아직 검증하지 않았으므로, 전환할 때 한 번 대화해 보고 확인하세요.
- **파인튜닝한 로컬 모델**: 모델을 OpenAI 호환 서버로 띄우고 답변 생성에만 사용합니다. 보조 호출은 `LLM_PROVIDER` 모델을 그대로 씁니다. vLLM은 Linux/WSL에서 실행됩니다.

  ```bash
  vllm serve fine_tuned_model/merged_qwen --served-model-name merged_qwen --port 8002
  ```

  ```env
  ANSWER_LLM_PROVIDER=local
  LOCAL_LLM_BASE_URL=http://localhost:8002/v1
  LOCAL_LLM_MODEL=merged_qwen
  ```

## 동작 방식

채팅 메시지 하나가 처리되는 흐름입니다.

1. 프론트엔드가 `POST /api/v1/chat/rooms/{room_id}/stream`으로 질문을 보냅니다.
2. Django가 질문을 저장하고, 최근 대화 10개와 대표 캐릭터 정보를 붙여 AI 서버 `/stream`을 호출합니다.
3. AI 서버의 LangGraph가 질문을 분류하고, 필요한 정보를 모은 뒤 답변을 생성합니다.

   ```
   route ─┬─ chat ────────────────────────────────────┐
          ├─ knowledge: 검색어 재작성 → 문서 검색 ────┤
          ├─ character: 질문 분석 → 넥슨 API 조회·요약 ─┼─▶ generate (답변 스트리밍)
          └─ character_knowledge: 위 두 경로를 병렬 실행┘
   ```

   캐릭터 경로는 이렇게 동작합니다.
   - **조회 대상**: 질문 속 캐릭터명을 우선합니다. 없거나 "내 캐릭터"를 물으면 대표 캐릭터를 조회합니다.
   - **조회 범위**: 질문에 필요한 정보 종류만 고르고, 넥슨 API 응답은 짧은 한국어 요약으로 바꿔 답변 모델에 넘깁니다.
   - **조회 실패**: 캐릭터가 없거나 API에 장애가 있으면, 무엇이 문제인지 안내하는 문구를 답변으로 돌려줍니다.

4. Django가 AI 서버의 SSE 이벤트를 그대로 브라우저로 중계합니다. 끝나면 답변, 질문 분류 결과, 근거 문서를 DB에 저장합니다.

스트리밍 이벤트는 `status`(진행 상태), `route`(질문 분류), `token`(답변 조각), `sources`(근거 문서), `error`가 있고, 항상 `data: [DONE]`으로 끝납니다. 자세한 형식은 [채팅 API 명세](docs/api/chat-api.md)와 [AI API 명세](docs/api/ai-api.md)를 참고하세요.

## 코드 구조

```
MAI_Help_You/
├── config/                  # Django 프로젝트 설정
│   ├── settings/            #   base / development / production / test
│   ├── env_loader.py        #   env/.env.local → .env 순서로 환경 변수 로드
│   └── urls.py              #   /api/v1/<앱>/ 라우팅 + React SPA catch-all(마지막)
├── apps/                    # Django 앱 (뷰는 얇게, 비즈니스 로직은 services.py)
│   ├── core/                #   홈(공지·랭킹), React index.html 서빙, 광고 설정
│   ├── auth/                #   회원가입·로그인, UserProfile (앱 label: accounts)
│   ├── character/           #   캐릭터 검색·연동(CharacterLink), nexon/ API 클라이언트·추출기
│   ├── chat/                #   대화방·메시지 저장, AI 서버 호출·SSE 중계
│   └── community/           #   커뮤니티 게시글
├── common/                  # 공용 예외·미들웨어·응답 스키마·유틸
│   └── nexon/               #   넥슨 Open API 클라이언트·Redis 캐시·응답 정제 (Django·AI 서버 공용)
├── ai_server/               # FastAPI AI 서버
│   ├── main.py, lifespan.py #   앱 진입점, 시작/종료 처리(그래프 빌드, 스케줄러, 모니터링)
│   ├── api/                 #   라우터: /generate, /stream, /api/v1/ai/*
│   ├── services/            #   요청 → 그래프 입력, 그래프 이벤트 → SSE 변환
│   ├── graph/               #   LangGraph
│   │   ├── builder/         #     메인 그래프 + RAG·넥슨 서브 그래프 조립
│   │   ├── nodes/           #     route / rag / nexon / generate 노드
│   │   ├── state/           #     그래프 상태 타입
│   │   └── tools/           #     캐릭터 정보 → 답변용 요약 (character_context.py)
│   ├── llm/                 #   모델 팩토리 (Gemini / DeepSeek / 로컬)
│   ├── prompts/             #   프롬프트 템플릿 (PromptTemplate Enum)
│   ├── rag/                 #   문서 로더·임베딩·pgvector·검색기·배치·평가
│   ├── schemas/             #   요청/응답 스키마 (Pydantic)
│   └── common/observability/ #  Langfuse 연동
├── frontend/                # React 18 + Vite (빌드 결과는 static/dist/)
├── static/dist/             # 프론트엔드 빌드 결과 (Django가 서빙, git에 포함)
├── tests/                   # pytest 테스트
├── docs/                    # 기획·설계 문서, API 명세, ADR
├── data/, rag_documents/    # RAG 원본 데이터 (git 미포함)
├── fine_tuned_model/        # 파인튜닝한 Qwen 모델 (git 미포함)
├── docker-compose.yml       # db(pgvector) · redis · django · fastapi
└── requirements.txt
```

코드 작성 관례는 다음과 같습니다.

- 코드 주석·문서는 한국어로 작성하고, 메이플스토리 용어(스탯, 잠재능력, 스타포스 등)를 정확히 사용합니다.
- 외부 API 호출은 `aiohttp` 등으로 비동기 처리합니다. 비동기 뷰에서는 `await request.auser()`로 사용자를 가져옵니다.
- 넥슨 Open API는 직접 호출하지 않고 `common/nexon`의 `NexonClient`를 사용합니다(재시도·오류 분류·캐시·호출 속도 제한 포함).
- 프롬프트 문구는 `ai_server/prompts/templates.py`에만 둡니다.
- 그래프 노드는 특정 LLM을 직접 import하지 않고 `ai_server/llm/factory.py`를 통해 모델을 받습니다.
- 새 API 라우트는 `config/urls.py`의 React catch-all보다 앞에 등록해야 합니다.

## 테스트

```bash
pytest                                       # 전체 (SQLite 메모리 DB 사용, 외부 API 호출 없음)
pytest tests/test_ai_chat_graph.py           # 파일 하나
pytest tests/test_ai_chat_graph.py::test_stream_answers_for_every_route   # 테스트 하나

cd frontend && npm test                      # 프론트엔드 (vitest)
```

AI 서버 설정을 불러오므로 테스트에도 `SECRET_KEY`가 있는 환경 변수 파일이 필요합니다.

## 현재 상태와 개선 예정

- **LLM 호출 한도**: Gemini 무료 등급은 모델별로 분당 5회, 하루 20회까지만 호출할 수 있습니다. 질문 1건에 2~4회를 호출하므로, 실서비스에는 유료 등급 또는 DeepSeek 전환이 필요합니다.
- **넥슨 API 호출 한도**: 개발 단계 키는 초당 호출 한도가 낮아 클라이언트가 초당 5건으로 속도를 맞춥니다. 서비스 전에 서비스 단계 키로 전환하고 `NEXON_REQUESTS_PER_SECOND`를 올려야 합니다.
- **캐릭터 연동(인증 코드)**: 넥슨 Open API의 캐릭터 기본 정보에는 인게임 소개글 필드가 없습니다. 그래서 소개글에 인증 코드를 넣는 연동 방식은 실제 API로는 통과하지 않습니다. 대표 캐릭터는 현재 회원가입 때 넥슨 API 키로 확인한 캐릭터를 사용합니다.
- **지식 베이스**: 공지·랭킹·보스/직업 목록 위주라 공략 문서가 부족하고, 검색이 BM25 위주입니다. 캐릭터 데이터도 같은 컬렉션에 섞여 있습니다. 수집 파이프라인 정비와 하이브리드 검색으로 개선할 예정입니다.
- **프론트엔드**: `status`, `sources` 이벤트는 아직 화면에 표시하지 않습니다.
- **운영 배포**: 채팅 세션 소유권 확인, 요청 횟수 제한, AI 서버 내부 인증, ASGI 운영 서버 구성은 배포 전에 추가할 예정입니다.

## 문서

- [문서 목차](docs/README.md): 기획, 아키텍처, ADR
- [채팅 API 명세](docs/api/chat-api.md), [AI API 명세](docs/api/ai-api.md), [인증 API 명세](docs/api/auth-api.md)
- [환경 변수 가이드](docs/infra/env.md), [배포 설계](docs/infra/deployment.md)
