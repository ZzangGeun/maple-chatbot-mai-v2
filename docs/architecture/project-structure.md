# 프로젝트 디렉토리 구조 (Project Structure)

본 문서는 `maple-chatbot-mai-v2` 프로젝트의 디렉토리 구조와 주요 파일들의 역할을 정의합니다.

## 1. 디렉토리 트리 구조

```
maple-chatbot-mai-v2/
 ├── apps/                   # Django 애플리케이션 모듈 (인증, 사용자, 웹 API 등)
 │    ├── users/             # 사용자 관리 및 캐릭터 인증 앱
 │    ├── core/              # 공통 핵심 기능 및 서비스
 │    └── ...
 ├── ai_server/              # FastAPI 기반 AI & RAG 비동기 서버
 │    ├── main.py            # FastAPI 진입점
 │    ├── api/               # API 라우터 (v1)
 │    ├── services/          # 비동기 비즈니스 로직 (Nexon API 연동, LLM 질의 등)
 │    ├── core/              # FastAPI 설정 및 보안 로직
 │    └── models/            # Pydantic 데이터 모델
 ├── common/                 # Django와 FastAPI가 공유하는 공통 모듈 및 유틸리티
 ├── config/                 # Django 프로젝트 메인 설정 폴더 (settings.py 등)
 ├── data/                   # 분석용 원천 데이터 및 스태틱 백업 데이터
 ├── docs/                   # 프로젝트 설계 및 가이드 문서 폴더 (현재 위치)
 ├── env/                    # 로컬 실행 및 배포용 환경 설정 파일 관리 디렉토리
 ├── fine_tuned_model/       # 파인튜닝된 로컬 모델 가중치 및 설정 파일 저장소
 ├── frontend/               # 관리자 웹 혹은 사용자 대시보드 프론트엔드 (React/Vite 등)
 ├── rag_documents/          # RAG 임베딩에 사용되는 원본 텍스트/Markdown 가이드 문서
 ├── tests/                  # 단위 테스트 및 통합 테스트 코드
 ├── Dockerfile.django       # Django 서버 컨테이너 빌드 파일
 ├── Dockerfile.fastapi      # FastAPI 서버 컨테이너 빌드 파일
 ├── docker-compose.yml      # 멀티 컨테이너 로컬 실행 및 배포 오케스트레이션 설정
 ├── manage.py               # Django 관리 명령어 CLI 진입점
 └── requirements.txt        # 프로젝트 의존성 라이브러리 목록
```

---

## 2. 모듈별 역할 및 설계 의도

### 1) Django 애플리케이션 (`apps/`, `config/`)
* **역할:** 정적 데이터베이스 관리 및 일반 웹 기능.
* **설계 의도:** RDB 스키마 마이그레이션(`django-admin makemigrations/migrate`)을 안전하게 관리하며, 챗봇 사용자 인증 및 웹 관리자 기능(Django Admin)을 활용해 전체 시스템 관리 편의성을 가져갑니다.

### 2) FastAPI AI 서버 (`ai_server/`)
* **역할:** 비동기 I/O가 활발히 일어나는 챗봇 응답 및 RAG 검색 파이프라인.
* **설계 의도:** Django 백엔드와 별도 포트로 띄우거나 프로세스를 격리시켜, AI 연동 부하가 Django 백엔드의 사용자 로그인 및 기본 API 웹 서버에 미치는 영향을 최소화합니다.

### 3) 공통 모듈 (`common/`)
* **역할:** 데이터베이스 모델 공유(SQLAlchemy or Django ORM 연동 설정), 공통 에러 핸들러, 암호화 패키지 등 Django와 FastAPI에서 공통으로 수입(import)하여 사용해야 하는 코드를 분리합니다.
* **설계 의도:** 중복 코드를 방지하고 공유 도메인 로직의 정합성을 보장합니다.

### 4) RAG 문서 및 모델 저장소 (`rag_documents/`, `fine_tuned_model/`)
* **역할:** 임베딩 대상 원본 데이터 파일(.json, .md) 및 LLM 성능 개선을 위한 가벼운 로컬 언어모델/임베딩 모델 저장소.
* **설계 의도:** 배치(Batch) 엔진이 `rag_documents/`를 정기적으로 크롤링하여 업데이트한 뒤 임베딩 파이프라인을 실행하기 용이하게 구조화했습니다.
