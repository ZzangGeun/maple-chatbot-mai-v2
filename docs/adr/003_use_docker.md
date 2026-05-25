# 003. Docker 및 Docker Compose 사용 결정

## 날짜
2026-05-25

## 상태
**Accepted**

## 컨텍스트
시스템 아키텍처가 Django(Web API), FastAPI(AI), PostgreSQL(DB) 등 3개 이상의 거대한 컴포넌트로 나뉘어졌습니다. 
새로운 개발자가 이 프로젝트를 로컬에 세팅하려면 Python 버전 맞추기, DB 설치 등 수많은 매뉴얼 작업이 필요합니다. 

## 결정
프로젝트의 모든 실행 환경을 **Docker 컨테이너화(Containerization)**하고, 이를 묶어서 실행하는 오케스트레이션 도구로 **Docker Compose**를 사용하기로 결정했습니다.

## 이유
1. **Infrastructure as Code (IaC)**: 인프라 구성이 파일(`docker-compose.yml`, `Dockerfile`)로 문서화되어 환경설정의 파편화를 막습니다.
2. **독립된 환경 보장**: 앞서 001 ADR(FastAPI 분리)에서 언급한 "무거운 AI 라이브러리 의존성"이 메인 웹 환경을 오염시키는 것을 물리적으로 차단합니다. (Django 컨테이너와 FastAPI 컨테이너의 완전 분리)
3. **One-Command 실행**: `docker compose up -d` 한 줄로 DB, 메인 서버, AI 서버가 설정된 네트워크 안에서 즉각적으로 연동되어 실행됩니다.

## 결과
- `Dockerfile.django`: 가벼운 웹 서버 이미지 구축
- `Dockerfile.fastapi`: AI 라이브러리를 포함한 이미지 구축
- 네트워크(`maple-net`)를 구성하여 `http://fastapi:8001/` 과 같은 도메인으로 내부 컨테이너 간 통신 가능하게 구성됨.
