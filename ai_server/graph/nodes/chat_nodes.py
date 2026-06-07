# ai_server/graph/nodes/chat_nodes.py
"""
일반 잡담/대화를 처리하는 서브 그래프(단일 노드)용 모듈.
"""

import logging

from langchain_core.messages import AIMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableConfig

from ai_server.graph.state.main_state import MainState
from ai_server.llm.gemini_loader import get_gemini_llm
from ai_server.prompts import PromptTemplate, get_prompt

logger = logging.getLogger("ChatNodes")


async def gemini_chat_node(state: MainState, config: RunnableConfig = None) -> dict:
    """Gemini를 사용한 일상 대화(잡담) 생성 노드"""
    llm = get_gemini_llm()
    logger.info("[GeminiChat] 일반 대화 답변 생성 시작")

    prompt = ChatPromptTemplate.from_messages([
        ("system", get_prompt(PromptTemplate.CHAT_SYSTEM, model="gemini")),
        MessagesPlaceholder(variable_name="messages"),
    ])

    chain = prompt | llm | StrOutputParser()
    response = await chain.ainvoke({"messages": state["messages"]}, config=config)
    return {"messages": [AIMessage(content=response)]}
