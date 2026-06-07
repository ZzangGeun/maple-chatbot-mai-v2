# ai_server/graph/nodes/common_nodes.py
"""
여러 서브 그래프에서 공통으로 사용되는 노드 모음.
주로 로컬 LLM(Qwen)을 사용한 최종 답변 생성 노드 등을 포함합니다.
"""

import logging

from langchain_core.messages import AIMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableConfig

from ai_server.llm.llm_loader import get_local_llm
from ai_server.prompts import PromptTemplate, get_prompt

logger = logging.getLogger("CommonNodes")


async def local_generate_rag_node(state: dict, config: RunnableConfig = None) -> dict:
    """
    로컬 LLM (Qwen)을 사용하여 최종 RAG 또는 API 기반 답변을 생성합니다.
    검색된 문서(또는 API 결괏값)를 기반으로 <think> 추론 과정을 거칩니다.
    
    이 노드는 RagState와 NexonState 모두에서 호출할 수 있도록 
    파라미터 타입을 dict로 받아 필요한 키만 읽습니다.
    """
    llm = get_local_llm()
    context = state.get("context", "")
    rewritten_query = state.get("query", "")
    
    query_log = f" | 쿼리: '{rewritten_query}'" if rewritten_query else ""
    logger.info(f"[LocalGenerateRAG] 답변 생성 시작{query_log} | 컨텍스트 길이: {len(context)}자")

    rag_system = get_prompt(PromptTemplate.RAG_SYSTEM, model="local")
    rag_human = get_prompt(PromptTemplate.RAG_HUMAN, model="local")

    # ChatML 템플릿 구조
    prompt = ChatPromptTemplate.from_messages([
        ("system", rag_system),
        MessagesPlaceholder(variable_name="messages"),
        ("human", rag_human)
    ])

    chain = prompt | llm | StrOutputParser()
    
    response = await chain.ainvoke(
        {"context": context, "messages": state["messages"]},
        config=config
    )
    
    return {"messages": [AIMessage(content=response)]}
