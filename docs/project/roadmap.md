# 로드맵 (Roadmap)

MAI Help You 프로젝트의 단계별 기능 릴리즈 계획입니다.

## Phase 1: 기반 시스템 구축 (현재 완료)
- [x] Django와 FastAPI 듀얼 서버 아키텍처 도입
- [x] 프로젝트 디렉토리 리팩토링 (`apps/`, `common/`, `config/`)
- [x] Docker 기반 로컬 실행 환경 구성
- [x] PostgreSQL 데이터베이스 모델 연동 완료

## Phase 2: 핵심 기능 (Core Features) - *Next Step*
- [ ] 넥슨 Open API 연동 강화 (캐릭터 검색 시 캐싱 적용)
- [ ] 스트리밍 채팅 UI (React 프론트엔드 연동)
- [ ] 회원가입 시 넥슨 API 키 암호화 저장 및 유효성 검증

## Phase 3: AI 및 RAG 고도화
- [ ] `data/rag_documents/` 내 마크다운 문서를 임베딩하여 Vector DB 구축
- [ ] LangChain/LangGraph 기반 챗봇 에이전트 라우팅 적용 (질문 의도 파악)
- [ ] 유저 캐릭터 스탯을 컨텍스트로 LLM에 자동 주입하는 "개인화 프롬프트" 적용

## Phase 4: 성능 최적화 및 확장
- [ ] Redis를 활용한 세션 데이터 및 API 응답 캐싱
- [ ] 비동기 작업 처리를 위한 Celery 도입 (장기 실행 랭킹 수집 로직 등)
- [ ] AWS 또는 GCP 클라우드 프로덕션 배포 파이프라인(CI/CD) 구축
