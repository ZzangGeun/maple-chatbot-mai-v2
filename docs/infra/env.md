# 환경 변수 가이드 (Environment Variables)

본 문서는 `maple-chatbot-mai-v2` 서비스 구동에 필수적인 `.env` 환경 변수들의 상세 명세 및 보안 수칙을 기술합니다.

> [!IMPORTANT]
> `.env` 파일은 데이터베이스 패스워드 및 API 인증 키 등 민감한 정보를 담고 있습니다. 절대 Git 저장소(GitHub 등)에 push하지 않도록 `.gitignore`에 등록되어 있는지 반드시 확인하십시오.

---

## 1. 환경 변수 템플릿 (`.env.template`)

프로젝트 루트 디렉토리에 `.env` 파일을 생성하고 아래 형식을 맞추어 실제 값을 대입합니다.

```env
# 1. Django Settings
DEBUG=True
DJANGO_SECRET_KEY=django-insecure-your-custom-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1,maplechatbot.com

# 2. Database Connection
DB_ENGINE=django.db.backends.postgresql
DB_NAME=maple_chatbot
DB_USER=postgres
DB_PASSWORD=your_secure_db_password
DB_HOST=db
DB_PORT=5432

# 3. Redis Cache
REDIS_URL=redis://redis:6379/0

# 4. Nexon Open API Settings (Critical)
# 넥슨 개발자 센터(Nexon Open API Developer Center)에서 발급받은 API 키
NEXON_API_KEY=test_your_nexon_open_api_key_here

# 5. AI & LLM Settings
# RAG 임베딩 및 답변 생성에 필요한 API 키
OPENAI_API_KEY=sk-proj-your-openai-api-key-here
GEMINI_API_KEY=AIzaSyYourGeminiApiKeyHere

# 6. Vector Database Settings
CHROMA_DB_PATH=/app/data/chromadb
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_ENVIRONMENT=us-west1-gcp

# 7. JWT Settings
JWT_SECRET_KEY=your-jwt-signing-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

---

## 2. 세부 설명 및 설계 의도

1. **`NEXON_API_KEY` 호출 보안**
   - 넥슨 Open API는 캐릭터의 최신 스펙 데이터를 수집하기 위해 반드시 필요합니다.
   - 외부 챗봇(Discord, Kakao)의 클라이언트 코드에 키가 직접 하드코딩되지 않도록, 백엔드 서버(FastAPI) 내에서만 `os.getenv("NEXON_API_KEY")`로 가져와 API를 비동기 호출합니다.

2. **동기/비동기 프레임워크 간 설정 공유**
   - Django(`django-web`)와 FastAPI(`fastapi-ai`)가 동일한 `.env` 파일을 공유함으로써 DB 접속 정보 및 JWT 비밀키 동기화를 용이하게 만듭니다.
   - 이를 통해 Django에서 발급한 JWT 토큰을 FastAPI 서버에서 안전하게 해독(Decode)하고 사용자를 검증할 수 있습니다.
