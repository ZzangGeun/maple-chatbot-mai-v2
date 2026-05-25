# MAI Help You 문서 (Documentation)

MAI Help You 프로젝트의 모든 기술 문서, 기획 문서, 아키텍처 의사결정 기록(ADR)을 모아둔 인덱스 페이지입니다.

## 📌 기획 및 설계 (Project)

프로젝트의 목표부터 향후 로드맵, 그리고 기술적 스펙을 정의한 문서들입니다.

- **[00_goal.md](./project/00_goal.md)**: 프로젝트의 궁극적인 목표와 핵심 가치
- **[01_as_is.md](./project/01_as_is.md)**: 기존 서비스들이 가지고 있던 문제점과 한계
- **[02_to_be.md](./project/02_to_be.md)**: MAI Help You를 통해 개선될 시스템의 미래
- **[03_architecture.md](./project/03_architecture.md)**: 전체 시스템 아키텍처 (Django + FastAPI Dual Server)
- **[04_api_spec.md](./project/04_api_spec.md)**: 프론트엔드와 백엔드 간 통신을 위한 REST API 명세
- **[05_db_schema.md](./project/05_db_schema.md)**: 데이터베이스(PostgreSQL) 모델 구조 설계
- **[06_rag_design.md](./project/06_rag_design.md)**: 지식 검색(RAG) 시스템 및 텍스트 임베딩 파이프라인 설계
- **[roadmap.md](./project/roadmap.md)**: 단계별 기능 릴리즈 및 고도화 계획

## 🏛️ 아키텍처 의사결정 (ADR)

프로젝트를 진행하며 내린 굵직한 기술적 의사결정들의 배경과 이유를 기록합니다. (Architecture Decision Records)

- **[ADR 001: FastAPI 사용 결정](./adr/001_use_fastapi.md)**: 왜 AI 서버를 Django에서 분리했는가?
- **[ADR 002: PostgreSQL 사용 결정](./adr/002_use_postgresql.md)**: 왜 RDBMS(PostgreSQL)를 메인 DB로 채택했는가?
- **[ADR 003: Docker 사용 결정](./adr/003_use_docker.md)**: 왜 컨테이너 기반 아키텍처를 도입했는가?

---

> 이 문서들은 프로젝트가 성장함에 따라 지속적으로 최신화됩니다. 
> 코드를 변경하거나 아키텍처를 뒤집기 전에, 관련된 문서 내용(ADR)을 먼저 확인하시길 권장합니다.