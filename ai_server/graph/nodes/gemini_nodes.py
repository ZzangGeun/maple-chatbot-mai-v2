# ai_server/graph/nodes/gemini_nodes.py
"""
Gemini LLM 전용 노드 모음 — 하이브리드 에이전트의 전처리 및 채팅 파이프라인

역할:
  - gemini_route_node : 질문을 3가지 경로로 매우 빠르게 분류합니다.
  - gemini_rewrite_node : 대화 맥락을 참고해 검색 쿼리를 요약 및 재작성합니다.
  - gemini_intent_extract_node : 넥슨 API에 필요한 캐릭터 엔티티를 구조화하여 추출합니다.
  - gemini_chat_node : 게임 정보가 아닌 일반 대화를 빠르게 처리합니다.

설계 의도:
  Gemini 모델의 빠른 응답 속도와 완벽한 포맷(JSON 등) 준수 능력을 활용하여,
  라우팅과 전처리 단계를 ER(에러) 없이 즉각적으로 수행하도록 역할을 반전했습니다.
"""

import json
import logging

from langchain_core.messages import AIMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableConfig

from ai_server.graph.state import GraphState
from ai_server.llm.gemini_loader import get_gemini_llm
from ai_server.prompts.templates import PromptTemplate

logger = logging.getLogger("GeminiNodes")


def gemini_route_node(state: GraphState, config: RunnableConfig = None) -> str:
    """Gemini를 사용한 초고속 라우팅 노드"""
    llm = get_gemini_llm()
    question = state["messages"][-1].content

    prompt = ChatPromptTemplate.from_messages([
        ("system", PromptTemplate.GEMINI_ROUTE_SYSTEM.value),
        ("human", "{question}")
    ])

    chain = prompt | llm | StrOutputParser()
    decision = chain.invoke({"question": question}, config=config).strip().lower()

    logger.info(f"[GeminiRoute] 분류 결과: '{decision}' | 질문: {question[:50]}...")

    if "character" in decision:
        return "gemini_intent_extract"
    if "search" in decision:
        return "gemini_rewrite"
    return "gemini_chat"


def gemini_rewrite_node(state: GraphState, config: RunnableConfig = None) -> dict:
    """Gemini를 사용한 초고속 쿼리 재작성 노드"""
    llm = get_gemini_llm()
    messages = state["messages"]

    prompt = ChatPromptTemplate.from_messages([
        ("system", PromptTemplate.GEMINI_REWRITE_SYSTEM.value),
        MessagesPlaceholder(variable_name="messages"),
    ])

    chain = prompt | llm | StrOutputParser()
    new_query = chain.invoke({"messages": messages}, config=config).strip()

    logger.info(f"[GeminiRewrite] 재작성된 쿼리: {new_query}")
    return {"query": new_query}


def gemini_intent_extract_node(state: GraphState, config: RunnableConfig = None) -> dict:
    """Gemini를 사용한 넥슨 API 파라미터(엔티티) JSON 추출 노드"""
    llm = get_gemini_llm()
    # Gemini는 프롬프트를 json 형태로 요청하면 보통 잘 반환하지만 
    # 포맷 지정 기능을 명시적으로 주입할 수도 있습니다 (with_structured_output 등).
    # 여기서는 기존 텍스트 프롬프트를 재활용합니다.
    question = state["messages"][-1].content

    # Gemini용은 LOCAL용과 달리 ChatML 태그 없이 평문으로 사용합니다.
    # 기존 코드에서 LOCAL 프롬프트를 쓰면 <|im_start|>가 섞이므로 전용 프롬프트 생성
    extract_system = (
        "당신은 메이플스토리 캐릭터 정보 추출기입니다.\n"
        "사용자 질문에서 아래 항목을 JSON 형식으로만 추출하세요.\n"
        "- character_name: 캐릭터명 (없으면 null)\n"
        "- world: 월드명 (스카니아, 베라, 등, 없으면 null)\n"
        "- item_name: 아이템명 (없으면 null)\n"
        "설명 없이 오직 유효한 JSON 객체 하나만 출력하세요."
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", extract_system),
        ("human", "{question}")
    ])

    chain = prompt | llm | StrOutputParser()
    raw_output = chain.invoke({"question": question}, config=config).strip()

    # JSON 마크다운 블록 제거
    if raw_output.startswith("```json"):
        raw_output = raw_output[7:]
    if raw_output.startswith("```"):
        raw_output = raw_output[3:]
    raw_output = raw_output.rstrip("`").strip()

    logger.info(f"[GeminiIntentExtract] 원본 JSON 출력: {raw_output}")

    try:
        entities = json.loads(raw_output)
    except (json.JSONDecodeError, ValueError):
        logger.warning("[GeminiIntentExtract] JSON 파싱 실패. 질문 전체를 character_name으로 사용합니다.")
        entities = {"character_name": question}

    logger.info(f"[GeminiIntentExtract] 추출된 엔티티: {entities}")
    return {"extracted_entities": entities}


def gemini_chat_node(state: GraphState, config: RunnableConfig = None) -> dict:
    """Gemini를 사용한 일상 대화(잡담) 생성 노드"""
    llm = get_gemini_llm()
    logger.info("[GeminiChat] 일반 대화 답변 생성 시작")

    prompt = ChatPromptTemplate.from_messages([
        ("system", PromptTemplate.GEMINI_CHAT_SYSTEM.value),
        MessagesPlaceholder(variable_name="messages"),
    ])

    chain = prompt | llm | StrOutputParser()
    response = chain.invoke({"messages": state["messages"]}, config=config)
    return {"messages": [AIMessage(content=response)]}
