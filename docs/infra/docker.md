# Docker 배포 및 실행 가이드 (Docker Setup)

본 문서는 Docker 및 Docker Compose를 사용하여 메이플스토리 챗봇 백엔드 서비스의 개발 및 상용 환경을 격리하고 구동하는 방법을 정의합니다.

## 1. 멀티 컨테이너 아키텍처 구조

로컬 및 개발 서버 구동을 위해 다음 4가지 서비스가 컨테이너로 연동됩니다.
* **django (Django Backend):** RDB 마이그레이션 관리, 어드민, 사용자 인증 담당
* **fastapi (FastAPI):** 비동기 챗봇 API, RAG 질의, Nexon Open API 호출 담당
* **db (PostgreSQL):** 정적 및 사용자 데이터 저장
* **redis (Cache & Lock):** 넥슨 Open API 데이터 캐시 및 호출 Rate Limit 기록

---

## 2. Docker Compose 설정 가이드 (`docker-compose.yml`)

프로젝트 루트의 `docker-compose.yml` 템플릿 예시입니다.

```yaml
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    container_name: maple_db
    environment:
      POSTGRES_DB: maple_chatbot
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    container_name: maple_redis
    ports:
      - "6379:6379"

  django-web:
    build:
      context: .
      dockerfile: Dockerfile.django
    container_name: maple_django
    command: python manage.py runserver 0.0.0.0:8000
    volumes:
      - .:/app
    ports:
      - "8000:8000"
    depends_on:
      - db
      - redis
    env_file:
      - .env

  fastapi-ai:
    build:
      context: .
      dockerfile: Dockerfile.fastapi
    container_name: maple_fastapi
    command: uvicorn ai_server.main:app --host 0.0.0.0 --port 8001 --reload
    volumes:
      - .:/app
    ports:
      - "8001:8001"
    depends_on:
      - db
      - redis
    env_file:
      - .env

volumes:
  postgres_data:
```

---

## 3. 실행 및 관리 명령어

1. **컨테이너 빌드 및 백그라운드 실행**
   ```bash
   docker compose --env-file env/.env.local up --build -d
   ```
2. **Django DB 마이그레이션 적용**
   ```bash
   docker compose --env-file env/.env.local exec django python manage.py migrate
   ```
3. **특정 서비스 로그 실시간 확인**
   ```bash
   docker compose --env-file env/.env.local logs -f fastapi
   ```
4. **컨테이너 완전 종료 (볼륨 유지)**
   ```bash
   docker compose --env-file env/.env.local down
   ```
