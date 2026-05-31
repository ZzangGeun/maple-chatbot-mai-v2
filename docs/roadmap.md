# 서비스 개발 로드맵 (Roadmap)

본 문서는 메이플스토리 챗봇 서비스(`maple-chatbot-mai-v2`)의 마일스톤별 개발 단계와 릴리즈 로드맵을 정의합니다.

## 1. 개발 마일스톤 개요

```mermaid
gantt
    title 메이플스토리 챗봇 개발 일정
    dateFormat  YYYY-MM-DD
    section Phase 1: 아키텍처 구축
    기초 프레임워크 셋업      :active, p1, 2026-06-01, 7d
    DB 및 기본 ERD 구현      :active, p2, after p1, 5d
    section Phase 2: Open API & 챗봇
    넥슨 Open API 비동기 연동  :content, p3, after p2, 10d
    디스코드/카카오 챗봇 프로토타입 :content, p4, after p3, 7d
    section Phase 3: RAG & AI
    크롤러 및 배치 적재 파이프라인 :content, p5, after p4, 10d
    벡터 스토어 구축 및 LLM 연동 :content, p6, after p5, 7d
    section Phase 4: 배포 & 고도화
    Docker 기반 운영 서버 배포 :content, p7, after p6, 5d
    모니터링 및 성능 최적화      :content, p8, after p7, 7d
```

---

## 2. 단계별 세부 계획

### **Phase 1: 핵심 아키텍처 및 DB 인프라 구축 (완료 목표: W2)**
* **목표:** Django 백엔드와 FastAPI AI 서버의 기본 뼈대를 완성하고 상호 JWT 토큰 인증 연동을 구축합니다.
* **주요 작업:**
  - Django: User, CharacterLink 스키마 마이그레이션 및 로그인 API.
  - FastAPI: Uvicorn 구동 및 미들웨어 설정.
  - Docker Compose 로컬 격리 개발 환경 셋업.

### **Phase 2: 넥슨 Open API 연동 및 챗봇 연동 (완료 목표: W4)**
* **목표:** 사용자의 캐릭터를 실제로 인증 연동하고 캐릭터의 상세 스탯을 챗봇 채널에서 실시간 조회하도록 구현합니다.
* **주요 작업:**
  - 넥슨 Open API 클라이언트 구현 (`aiohttp` 비동기 통신 및 예외 처리).
  - 인게임 소개글 매칭 기반 캐릭터 소유 인증 API.
  - Discord 봇 SDK를 이용한 기본 `!전적 [캐릭터명]` 명령어 구현.

### **Phase 3: RAG 기반 지식 검사 및 크롤링 배치 (완료 목표: W6)**
* **목표:** 챗봇에 메이플 게임에 특화된 질문을 던졌을 때 벡터 지식 기반을 참고해 똑똑하게 답변하는 AI 기능을 배포합니다.
* **주요 작업:**
  - 메이플스토리 공식 업데이트 내역 및 가이드 문서 크롤러 스크립트 작성.
  - ChromaDB 연동 및 문서 청킹/임베딩 자동화 파이프라인 구축.
  - 프롬프트 엔지니어링 및 Guardrail 기능(메이플 외 질문 분류기) 구현.

### **Phase 4: 배포 및 운영 고도화 (완료 목표: W8)**
* **목표:** 클라우드 서버에 실배포를 완료하고, CI/CD 자동화를 통해 지속적인 서비스 개선 기반을 확보합니다.
* **주요 작업:**
  - GitHub Actions를 통한 테스트 및 배포 자동화 구현.
  - Redis 캐싱 성능 분석 및 Nexon API 호출 Rate Limit 모니터링 적용.
  - 서비스 정식 오픈 및 유저 피드백 채널 개설.
