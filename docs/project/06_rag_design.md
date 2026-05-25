# 지식 검색(RAG) 시스템 설계

환각(Hallucination) 없이 정확한 메이플스토리 정보를 제공하기 위해 RAG(Retrieval-Augmented Generation) 파이프라인을 구축합니다.

## 1. RAG 파이프라인 개요

1. **문서 수집 (Ingestion)**
   - `data/rag_documents/`에 마크다운(`*.md`) 또는 텍스트 형태로 게임 패치노트, 보스 패턴 가이드, 직업별 스킬 정보를 저장합니다.
2. **청킹 및 임베딩 (Embedding)**
   - 문서를 의미 단위로 쪼개고(Chunking), HuggingFace의 임베딩 모델(예: `bge-m3` 등)을 이용해 벡터화합니다.
3. **저장 (Vector Store)**
   - 임베딩된 벡터 데이터는 FAISS (또는 PostgreSQL의 `pgvector`)에 저장됩니다.
4. **검색 (Retrieval)**
   - 사용자가 질문하면, 질문을 임베딩한 후 가장 유사한 문서 N개를 벡터 DB에서 뽑아냅니다.
5. **생성 (Generation)**
   - 뽑아낸 문서(Context)를 프롬프트에 주입하여, LLM(FastAPI AI 서버)이 정확한 사실을 기반으로 답변을 스트리밍합니다.

## 2. 문서 카테고리 구성 (`data/rag_documents/`)

- `boss/`: 윌, 진힐라, 칼로스 등 보스 몬스터의 주요 기믹 및 파훼법
- `class/`: 직업별 주력기, 극딜 순서, 5/6차 스킬 정보
- `notices/`: 최신 패치로 인해 변경된 주요 이벤트 및 시스템 패치 내역
- `rankings/`: 주간 랭킹, 무릉도장 랭킹 요약 데이터

## 3. LangChain/LangGraph 통합
- 단순한 RAG를 넘어, 질문의 의도(보스 질문인지, 아이템 추천 질문인지)에 따라 Router가 판단하여 
  **[넥슨 API 호출 에이전트]** 또는 **[벡터 DB 검색 에이전트]** 로 분기 처리하는 구조(LangGraph)를 구현할 예정입니다.
