# ai_server/graph/nodes/local_nodes.py
"""
로컬 LLM(Qwen) 전용 노드 모음 — 하이브리드 에이전트의 전처리 파이프라인

역할:
  - local_route_node         : 질문을 3가지로 분류합니다.
                               "local_rewrite"     → RAG 게임 정보 검색
                               "character_lookup"  → 넥슨 API 캐릭터 전적 조회
                               "gemini_chat"       → 일반 대화
  - local_rewrite_node       : 대화 맥락을 참고해 검색 쿼리를 메이플 도메인에 맞게 재작성합니다.
  - local_retrieve_node      : 재작성된 쿼리로 벡터스토어에서 관련 문서를 검색합니다.
  - local_intent_extract_node: 질문에서 캐릭터명/아이템명 등 도메인 엔티티를 구조화합니다.

설계 의도:
  로컬 LLM은 양자화로 인해 최종 답변 품질이 낮지만,
  메이플스토리 도메인 지식을 학습했기 때문에
  '분류/구조추출/검색' 같은 구조적 작업에는 충분한 성능을 발휘합니다.
  비용이 발생하는 Gemini API 호출 전에 최대한 많은 정보를 준비합니다.
"""

import logging

from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableConfig

from ai_server.graph.state import GraphState
from ai_server.llm.llm_loader import get_local_llm
from ai_server.prompts.templates import PromptTemplate
from ai_server.rag.retriever import Retriever

logger = logging.getLogger("LocalNodes")

# 모듈 레벨에서 한 번만 초기화 — 매 요청마다 모델을 재로드하면 VRAM 낭비입니다.
_retriever_instance = Retriever()


# ---------------------------------------------------------------------------
# Conditional Edge 노드 — 라우터
# ---------------------------------------------------------------------------

def local_route_node(state: GraphState, config: RunnableConfig = None) -> str:
    """
    로컬 LLM으로 질문을 3가지 경로 중 하나로 분류합니다.

    분류 결과:
      - "local_rewrite"    : 메이플 게임 정보 검색이 필요한 질문 (RAG 경로)
      - "character_lookup" : 특정 캐릭터 전적/정보 조회 질문 (넥슨 API 경로)
      - "gemini_chat"      : 인사, 잡담 등 일반 대화

    Args:
        state: 현재 그래프 상태.
        config: Langfuse 등 상위 콜백 추적 전파를 위한 랭체인 런타임 설정.

    Returns:
        세 경로 중 하나의 문자열.
    """
    from langchain_core.prompts import ChatPromptTemplate

    llm = get_local_llm()
    question = state["messages"][-1].content

    route_system = PromptTemplate.LOCAL_ROUTE_SYSTEM.value
    route_human = PromptTemplate.LOCAL_ROUTE_HUMAN.value

    prompt = ChatPromptTemplate.from_messages(
        [("system", route_system), ("human", route_human)]
    )

    chain = prompt | llm | StrOutputParser()
    # 로컬 모델은 간혹 불필요한 앞뒤 텍스트를 붙이므로 lower()로 정규화합니다.
    # config를 함께 전달하여 추적이 유실되지 않도록 연동합니다.
    decision = chain.invoke({"question": question}, config=config).strip().lower()

    logger.info(f"[LocalRoute] 분류 결과: '{decision}' | 질문: {question[:50]}...")

    # 우선순위: character > search > chat
    # 캐릭터 전적 조회는 넥슨 API가 실시간 데이터를 제공하므로 RAG보다 우선합니다.
    if "character" in decision:
        return "character_lookup"
    if "search" in decision:
        return "local_rewrite"
    return "gemini_chat"


# ---------------------------------------------------------------------------
# 일반 노드들 — 전처리 파이프라인
# ---------------------------------------------------------------------------

def local_rewrite_node(state: GraphState, config: RunnableConfig = None) -> dict:
    """
    로컬 LLM으로 검색 쿼리를 재작성합니다.

    대화 맥락(이전 메시지들)을 반영해 독립적으로 이해 가능한 검색 쿼리를 생성합니다.
    메이플스토리 용어(스타포스, 잠재능력 등)를 정확히 다루는 것이 핵심입니다.

    Args:
        state: 현재 그래프 상태.
        config: Langfuse 등 상위 콜백 추적 전파를 위한 랭체인 런타임 설정.

    Returns:
        {"query": 재작성된 쿼리 문자열}
    """
    from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

    llm = get_local_llm()
    messages = state["messages"]

    rewrite_system = PromptTemplate.LOCAL_REWRITE_SYSTEM.value
    rewrite_human = PromptTemplate.LOCAL_REWRITE_HUMAN.value

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", rewrite_system),
            MessagesPlaceholder(variable_name="messages"),
            ("human", rewrite_human),
        ]
    )

    chain = prompt | llm | StrOutputParser()
    new_query = chain.invoke({"messages": messages}, config=config).strip()

    logger.info(f"[LocalRewrite] 재작성된 쿼리: {new_query}")
    return {"query": new_query}


def local_retrieve_node(state: GraphState) -> dict:
    """
    재작성된 쿼리로 RAG 벡터스토어에서 관련 문서를 검색합니다.

    검색 결과를 마크다운 구조로 정리하여 Gemini가 출처를 명확히
    파악하고 더 정확한 답변을 생성할 수 있도록 돕습니다.

    Args:
        state: 현재 그래프 상태 (state["query"] 사용).

    Returns:
        {"context": 메타데이터 포함 마크다운 컨텍스트 문자열}
    """
    query = state["query"]
    docs = _retriever_instance.retriever.invoke(query)

    # Gemini가 출처를 참고해 링크까지 답변에 포함할 수 있도록 구조화합니다.
    context_parts = []
    for i, doc in enumerate(docs, 1):
        metadata = doc.metadata
        title = metadata.get("title", "제목 없음")
        source = metadata.get("source", "출처 정보 없음")
        category = metadata.get("category", "기타")
        url = (
            metadata.get("notice_url")
            or metadata.get("thumbnail_url")
            or metadata.get("url", "")
        )

        # f-string 대신 문자열 결합을 사용합니다.
        # doc.page_content에 중괄호({})가 포함될 수 있어 f-string은 format spec 에러를 유발합니다.
        url_line = f"- **참고 링크**: {url}" if url else ""

        context_part = "\n".join([
            f"## [문서 {i}] {title}",
            f"- **카테고리**: {category}",
            f"- **출처**: {source}",
            url_line,
            "",
            "**내용**:",
            doc.page_content,
            "",
            "---",
        ])
        context_parts.append(context_part)

    context_text = "\n".join(context_parts)
    logger.info(f"[LocalRetrieve] {len(docs)}개 문서 검색 완료 | 쿼리: '{query}'")
    if docs:
        logger.info(f"[LocalRetrieve] 첫 번째 문서 미리보기: {docs[0].page_content[:80]}...")

    return {"context": context_text}


# ---------------------------------------------------------------------------
# 엔티티 추출 노드 — 넥슨 API 경로 전처리
# ---------------------------------------------------------------------------

import json as _json  # 함수 내 사용을 위해 별칭 사용 (모듈 상단 import와 충돌 방지)


def local_intent_extract_node(state: GraphState, config: RunnableConfig = None) -> dict:
    """
    로컬 LLM으로 질문에서 메이플스토리 도메인 엔티티를 구조화하여 추출합니다.

    추출 대상:
      - character_name: 캐릭터명 (넥슨 API 호출의 필수 키)
      - world         : 월드명 (선택)
      - item_name     : 아이템명 (선택)

    로컬 LLM이 메이플 도메인 지식으로 학습했으므로
    '홍길동' '스카니아 홍길동' 같은 자연어에서 엔티티를 잘 추출합니다.
    출력은 JSON 파싱을 시도하고, 실패하면 question 전체를 character_name으로 사용합니다.

    Args:
        state: 현재 그래프 상태.
        config: Langfuse 등 상위 콜백 추적 전파를 위한 랭체인 런타임 설정.

    Returns:
        {"extracted_entities": {"character_name": ..., "world": ..., "item_name": ...}}
    """
    from langchain_core.prompts import ChatPromptTemplate

    llm = get_local_llm()
    question = state["messages"][-1].content

    intent_extract_system = PromptTemplate.LOCAL_INTENT_EXTRACT_SYSTEM.value
    intent_extract_human = PromptTemplate.LOCAL_INTENT_EXTRACT_HUMAN.value

    # Qwen 로컬 모델은 assistant 턴의 JSON prefix를 그대로 완성해야 하므로 
    # 프롬프트 유도 구문을 적용하되, 누락된 여는 브레이스 부분을 채워줍니다.
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", intent_extract_system), 
            ("human", intent_extract_human)
        ]
    )

    chain = prompt | llm | StrOutputParser()
    raw_output = chain.invoke({"question": question}, config=config).strip()

    # assistant 턴이 '{"character_name": "'로 유도되었기 때문에,
    # 출력된 텍스트 앞에 이 접두사를 결합해야 완전한 JSON이 됩니다.
    full_json_str = '{"character_name": "' + raw_output
    logger.info(f"[LocalIntentExtract] 결합된 원본 JSON 출력: {full_json_str}")

    # 로컬 LLM 출력이 JSON이 아닐 수 있으므로 안전하게 파싱합니다.
    try:
        entities = _json.loads(full_json_str)
    except (_json.JSONDecodeError, ValueError):
        logger.warning("[LocalIntentExtract] JSON 파싱 실패. 질문 전체를 character_name으로 사용합니다.")
        # 파싱 실패 시 질문 자체를 캐릭터명으로 추정합니다.
        entities = {"character_name": question}

    logger.info(f"[LocalIntentExtract] 추출된 엔티티: {entities}")
    return {"extracted_entities": entities}
