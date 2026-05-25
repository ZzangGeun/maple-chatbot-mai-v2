# 001. FastAPI 사용 결정 (AI Server)

## 날짜
2026-05-25

## 상태
**Accepted**

## 컨텍스트
AI 챗봇 서비스는 메인 로직인 유저/세션 관리 외에, 대용량 언어 모델(LLM)을 다루고 RAG 시스템을 구동해야 합니다. 
기존의 메인 서버 프레임워크인 Django로 모든 것을 처리할 수도 있지만, AI 로직(LangChain, LangGraph 등)은 대부분 비동기(Async)에 최적화되어 있으며 응답을 스트리밍(SSE)하는 데에 탁월한 성능이 필요합니다.

## 결정
AI 서버를 Django에서 분리하여 **FastAPI 기반의 독립적인 마이크로서비스**로 구축하기로 결정했습니다.

## 이유
1. **비동기 I/O 최적화**: FastAPI는 Starlette과 asyncio를 기반으로 구축되어, LLM API 대기 시간이나 벡터 DB 검색과 같은 긴 I/O 작업(네트워크 병목)을 블로킹 없이 처리하는 데 탁월합니다.
2. **AI 생태계 친화성**: LangChain, LlamaIndex 등 Python 기반의 최신 AI 라이브러리들은 FastAPI와 결합하여 사용되는 레퍼런스가 가장 많습니다.
3. **Pydantic 기본 내장**: 입출력 데이터의 스키마 검증과 직렬화에 Pydantic을 기본으로 사용하여, LLM 프롬프트에 주입할 데이터 구조를 강제하기 매우 쉽습니다.
4. **스트리밍(SSE)**: StreamingResponse를 통해 AI가 생성하는 텍스트를 클라이언트나 브릿지 서버(Django)에게 실시간으로 전달하기가 매우 용이합니다.

## 결과
- 아키텍처가 Dual Server 구조(Django + FastAPI)로 분리되었습니다.
- 관리가 복잡해지는 단점(포트 2개 관리, Docker Compose 필수)이 생겼지만, 챗봇 응답 속도와 AI 로직 구현의 편의성이라는 더 큰 이점을 얻었습니다.
