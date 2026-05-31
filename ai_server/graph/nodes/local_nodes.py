# ai_server/graph/nodes/local_nodes.py
"""
로컬 LLM(Qwen) 전용 노드 모음 — 하이브리드 에이전트의 생성 파이프라인

역할:
  - local_retrieve_node  : 재작성된 쿼리로 벡터스토어에서 관련 문서를 검색합니다.
  - local_generate_rag_node : 메이플 도메인 지식에 특화된 Qwen 모델이 RAG 문서 혹은 넥슨 API 결과를 
                              바탕으로 깊이 있는 추론(<think>)을 거쳐 최종 답변을 생성합니다.

설계 의도:
  전처리(라우팅/추출)는 Gemini에 맡겨 속도와 형식 안정성을 확보하고, 
  진짜 도메인 지식과 분석이 필요한 '최종 답변' 단계만 로컬 모델을 활용하도록 역할을 반전했습니다.
"""

import logging

from langchain_core.messages import AIMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableConfig

from ai_server.graph.state import GraphState
from ai_server.llm.llm_loader import get_local_llm
from ai_server.prompts.templates import PromptTemplate
from ai_server.rag.retriever import Retriever

logger = logging.getLogger("LocalNodes")

# 모듈 레벨 초기화
_retriever_instance = Retriever()


def local_retrieve_node(state: GraphState) -> dict:
    """재작성된 쿼리로 RAG 벡터스토어에서 관련 문서를 검색합니다."""
    query = state["query"]
    docs = _retriever_instance.retriever.invoke(query)

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


def local_generate_rag_node(state: GraphState, config: RunnableConfig = None) -> dict:
    """
    로컬 LLM (Qwen)을 사용하여 최종 RAG 답변을 생성합니다.
    검색된 문서(또는 API 결괏값)를 기반으로 <think> 추론 과정을 거칩니다.
    """
    llm = get_local_llm()
    context = state.get("context", "")
    rewritten_query = state.get("query", "")

    logger.info(f"[LocalGenerateRAG] 답변 생성 시작 | 쿼리: '{rewritten_query}' | 컨텍스트 길이: {len(context)}자")

    rag_system = PromptTemplate.LOCAL_RAG_SYSTEM.value
    rag_human = PromptTemplate.LOCAL_RAG_HUMAN.value

    # ChatML 템플릿 구조
    prompt = ChatPromptTemplate.from_messages([
        ("system", rag_system),
        MessagesPlaceholder(variable_name="messages"),
        ("human", rag_human)
    ])

    chain = prompt | llm | StrOutputParser()
    
    response = chain.invoke(
        {"context": context, "messages": state["messages"]},
        config=config
    )
    
    return {"messages": [AIMessage(content=response)]}
