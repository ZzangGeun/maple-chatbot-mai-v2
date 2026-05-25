# 002. PostgreSQL 사용 결정

## 날짜
2026-05-25

## 상태
**Accepted**

## 컨텍스트
채팅 세션, 채팅 로그, 유저 프로필(넥슨 연동 정보) 등 영구적으로 보존해야 할 상태 데이터가 필요합니다. 
SQLite는 개발 환경에서 편하지만 배포 시 동시성(Concurrency) 제어가 부족하며, 
NoSQL(MongoDB)은 채팅 내역 저장엔 좋지만 유저(User)와 세션(Session) 간의 관계(Relation) 제약이 불리합니다.

## 결정
관계형 데이터베이스 관리 시스템(RDBMS)인 **PostgreSQL**을 프로젝트의 메인 DB로 도입하기로 결정했습니다.

## 이유
1. **강력한 정합성과 동시성**: 수많은 유저가 동시에 접속하여 채팅 로그를 DB에 INSERT 할 때 SQLite와 달리 락(Lock) 문제가 발생하지 않습니다.
2. **JSONB 및 UUID 지원**: 메이플스토리 캐릭터의 장비 데이터 등 스키마가 복잡한 데이터를 통째로 넣어야 할 때 `JSONB` 필드를 활용할 수 있으며, 고유 세션 ID 생성을 위한 UUID 처리도 네이티브로 강력히 지원합니다.
3. **pgvector 확장 가능성**: 향후 RAG 시스템의 Vector DB를 외부 솔루션(Pinecone)이나 로컬(FAISS) 대신 PostgreSQL 하나로 통합(`pgvector` 익스텐션)할 수 있는 확장성이 존재합니다.

## 결과
- `docker-compose.yml`에 PostgreSQL 서비스가 정의됨.
- `psycopg2-binary` 라이브러리가 의존성에 추가됨.
- 개발 및 상용 환경 모두에서 동일하게 PostgreSQL을 사용해 "개발/운영 환경 불일치" 문제를 제거함.
