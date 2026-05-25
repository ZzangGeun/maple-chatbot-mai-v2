# MAI (MapleStory AI) 🍁

메이플스토리 전문 AI 챗봇 시스템 - RAG(검색 증강 생성) 기반의 지능형 챗봇

## 📋 프로젝트 개요

MAI는 메이플스토리 관련 질문에 답변하는 AI 챗봇입니다. Django 웹 애플리케이션과 FastAPI AI 서버가 결합된 구조로, RAG 시스템을 통해 정확하고 최신의 메이플스토리 정보를 제공합니다.

### 🎯 주요 기능

- 🤖 **AI 챗봇**: 메이플스토리 관련 질문에 대한 지능적 답변
- 🔍 **RAG 검색**: 벡터 데이터베이스 기반의 문서 검색 증강 생성
- 👤 **사용자 관리**: 회원가입, 로그인, 캐릭터 연동
- 🎮 **캐릭터 정보**: Nexon API 연동으로 실시간 캐릭터 데이터 조회
- 📊 **데이터 갱신**: 공지사항, 랭킹 등 최신 정보 자동 업데이트
- 💬 **세션 관리**: 대화 기록 저장 및 맥락 유지
- 🌊 **스트리밍 응답**: 실시간으로 답변 전송

## 🏗️ 시스템 아키텍처

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Django Web    │    │   FastAPI AI    │    │   PostgreSQL    │
│   (Port 8000)   │◄──►│   (Port 8001)   │◄──►│   + pgvector    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
    ┌────▼────┐            ┌─────▼─────┐            ┌─────▼─────┐
    │  Core   │            │  LangGraph │            │  Vector   │
    │ Accounts │            │  RAG System│            │  Database │
    │Character│            │  LLM Module│            │  Storage  │
    │Chat     │            │  Streaming │            │           │
    └─────────┘            └───────────┘            └───────────┘
```

## 🚀 기술 스택

### Backend
- **Django 5.1.7**: 웹 프레임워크
- **FastAPI 0.104.1**: AI 서버 API
- **PostgreSQL**: 메인 데이터베이스
- **pgvector**: 벡터 데이터베이스 확장

### AI/ML
- **LangChain**: RAG 프레임워크
- **LangGraph**: 대화 흐름 제어
- **Transformers**: LLM 모델 로딩
- **PyTorch**: 딥러닝 프레임워크
- **Sentence Transformers**: 임베딩 생성

### LLM 지원
- **로컬 Qwen 모델**: 오프라인 추론
- **Google Gemini API**: 클라우드 기반 추론

## 📁 프로젝트 구조

```
MAI_Help_You/
├── maple_chatbot/          # Django 설정
├── core/                   # 메인 페이지, 공통 API
├── accounts/               # 사용자 인증, 프로필
├── character/              # 캐릭터 정보 조회
├── chat/                  # 채팅 세션 관리
├── ai_server/             # FastAPI AI 서버
│   ├── rag/              # RAG 시스템
│   ├── llm/              # LLM 모듈
│   └── main.py           # FastAPI 앱
├── rag_documents/         # 메이플스토리 문서
│   ├── boss/             # 보스 정보
│   ├── class/            # 직업 정보
│   ├── notices/          # 공지사항
│   └── rankings/         # 랭킹 데이터
├── services/              # 외부 API 연동
├── static/               # 정적 파일
└── requirements.txt      # 의존성 패키지
```

## 🛠️ 설치 및 설정

### 1. 환경 준비

```bash
# Python 3.11+ 설치 확인
python --version

# 가상환경 생성 (권장)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 2. 의존성 설치

```bash
pip install -r requirements.txt
```

### 3. 데이터베이스 설정

```bash
# PostgreSQL 설치 (Ubuntu/Debian)
sudo apt-get install postgresql postgresql-contrib

# pgvector 확장 설치
sudo -u postgres psql -c "CREATE EXTENSION vector;"

# 데이터베이스 및 사용자 생성
sudo -u postgres psql
CREATE DATABASE maple_chatbot_db;
CREATE USER mai_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE maple_chatbot_db TO mai_user;
\q
```

### 4. 환경 변수 설정

`.env` 파일 생성:

```bash
# Database
DB_CONNECTION=postgresql+psycopg2://mai_user:your_password@localhost/maple_chatbot_db
COLLECTION_NAME=maple_documents

# API Keys
NEXON_API_KEY=your_nexon_api_key
OPENAI_API_KEY=your_openai_api_key  # Gemini용
SECRET_KEY=your_django_secret_key

# LLM Provider (local 또는 gemini)
LLM_PROVIDER=local
```

### 5. 데이터베이스 마이그레이션

```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. RAG 데이터베이스 구축

```bash
cd ai_server/rag
python vectorstore.py
```

### 7. 서버 실행

```bash
# Django 웹 서버 (터미널 1)
python manage.py runserver 0.0.0.0:8000

# FastAPI AI 서버 (터미널 2)
cd ai_server
python main.py
```

## 📖 사용법

### 1. 웹 접속
- 메인 페이지: `http://localhost:8000`
- 챗봇 페이지: `http://localhost:8000/chat/`

### 2. 회원가입 및 캐릭터 연동
```bash
# API를 통한 회원가입 예시
curl -X POST http://localhost:8000/accounts/api/signup/ \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "testuser",
    "password": "SecurePass123!",
    "nexon_api_key": "your_nexon_api_key"
  }'
```

### 3. AI 챗봇 사용
```bash
# 챗봇 API 호출 예시
curl -X POST http://localhost:8001/generate \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-session-123",
    "message": "메이플스토리에서 가장 강한 보스는 누구야?"
  }'
```

## 🔄 AI 챗봇 동작 방식

```
사용자 질문
    ↓
LangGraph 흐름 시작
    ↓
route_question: 검색 필요 여부 판단
    ↓
┌─ 필요: rewrite_query → retrieve → generate
│
└─ 불필요: generate_chat (일반 대화)
    ↓
최종 답변 생성 및 응답
```

## 📊 API 명세

### Django API (Port 8000)

| 엔드포인트 | 메소드 | 설명 |
|-----------|--------|------|
| `/accounts/api/signup/` | POST | 회원가입 |
| `/accounts/api/login/` | POST | 로그인 |
| `/character/api/search/` | GET | 캐릭터 검색 |
| `/api/notices/` | GET | 공지사항 |
| `/api/rankings/overall/` | GET | 종합 랭킹 |

### FastAPI AI 서버 (Port 8001)

| 엔드포인트 | 메소드 | 설명 |
|-----------|--------|------|
| `/generate` | POST | 일반 답변 생성 |
| `/stream` | POST | 스트리밍 답변 |

## 🎯 RAG 시스템

### 문서 카테고리
- **boss**: 보스 몬스터 정보 및 공략
- **class**: 직업 정보 및 스킬
- **notices**: 게임 공지사항 및 업데이트
- **rankings**: 랭킹 데이터 및 통계

### 검색 과정
1. 사용자 질문 임베딩
2. pgvector에서 유사 문서 검색
3. 검색된 문서를 컨텍스트로 LLM에 전달
4. 컨텍스트 기반 답변 생성

## 🔧 개발 및 테스트

### 테스트 실행
```bash
# Django 테스트
python manage.py test

# RAG 시스템 테스트
cd ai_server/rag
python retriever.py
```

### LLM 모델 변경
```bash
# 로컬 Qwen 모델 사용
export LLM_PROVIDER=local

# Gemini API 사용
export LLM_PROVIDER=gemini
```

## 📝 로깅 및 디버깅

### 로그 레벨 설정
```python
# ai_server/main.py
logging.basicConfig(level=logging.INFO)

# Django settings.py
LOGGING = {
    'version': 1,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}
```

## 🚀 배포

### Docker 배포 (권장)
```dockerfile
# Dockerfile 예시
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000 8001

CMD ["sh", "-c", "python manage.py runserver 0.0.0.0:8000 & cd ai_server && python main.py"]
```

### 환경별 설정
- **개발**: `DEBUG=True`, 로컬 데이터베이스
- **프로덕션**: `DEBUG=False`, 외부 데이터베이스, HTTPS

## 🤝 기여

1. 이슈 생성: 버그 리포트 또는 기능 요청
2. 포크 및 브랜치 생성: `git checkout -b feature/AmazingFeature`
3. 커밋: `git commit -m 'Add some AmazingFeature'`
4. 푸시: `git push origin feature/AmazingFeature`
5. 풀 리퀘스트 생성

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 `LICENSE` 파일을 참조하세요.

## 🙏 감사

- **Nexon**: 메이플스토리 오픈 API 제공
- **LangChain**: RAG 프레임워크 지원
- **FastAPI**: 고성능 API 프레임워크
- **pgvector**: 벡터 데이터베이스 확장

## 📞 문의

- 프로젝트 관련 문의: GitHub Issues
- 개발자: [개발자 이메일 또는 연락처]

---

**MAI** - 메이플스토리와 함께하는 스마트한 AI 챗봇 🍁