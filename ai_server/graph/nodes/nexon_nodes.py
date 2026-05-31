# ai_server/graph/nodes/nexon_nodes.py
"""
넥슨 API 서브 그래프 전용 노드 모음.
캐릭터명 추출(Gemini)과 넥슨 API 조회 기능을 수행합니다.
"""

import json
import logging

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig

from ai_server.graph.state.nexon_state import NexonState
from ai_server.graph.tools.nexon_api_tool import NexonAPIClient
from ai_server.llm.gemini_loader import get_gemini_llm

logger = logging.getLogger("NexonNodes")

# 싱글턴 클라이언트
_nexon_client = NexonAPIClient()


def gemini_intent_extract_node(state: NexonState, config: RunnableConfig = None) -> dict:
    """Gemini를 사용한 넥슨 API 파라미터(엔티티) JSON 추출 노드"""
    llm = get_gemini_llm()
    question = state["messages"][-1].content

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


async def nexon_api_tool_node(state: NexonState) -> dict:
    """
    로컬 LLM이 추출한 캐릭터명으로 넥슨 Open API를 호출합니다.
    조회 결과를 마크다운 형식의 context로 직렬화하여 다음 노드에 전달합니다.
    """
    entities = state.get("extracted_entities") or {}
    character_name: str = entities.get("character_name", "")

    if not character_name:
        logger.warning("[NexonAPI] extracted_entities에 character_name 없음")
        context = "## 캐릭터 조회 실패\n캐릭터명을 인식하지 못했습니다."
        return {"context": context}

    logger.info(f"[NexonAPI] 캐릭터 조회 시작: {character_name}")

    try:
        summary = await _nexon_client.get_character_summary(character_name)
        context = _format_character_context(character_name, summary)

    except Exception as e:
        logger.error(f"[NexonAPI] 캐릭터 조회 실패: {e}")
        context = (
            f"## 캐릭터 조회 오류\n"
            f"'{character_name}' 캐릭터 정보를 가져오는 데 실패했습니다.\n"
            f"오류: {e}"
        )

    return {"context": context}


def _format_character_context(character_name: str, summary: dict) -> str:
    """넥슨 API 응답을 Gemini가 읽기 좋은 마크다운 형식으로 변환합니다."""
    basic: dict = summary.get("basic", {})
    stat: dict = summary.get("stat", {})

    context = f"""## 캐릭터 기본 정보: {character_name}

| 항목 | 값 |
|------|-----|
| 캐릭터명 | {basic.get("character_name", "알 수 없음")} |
| 레벨 | {basic.get("character_level", "알 수 없음")} |
| 직업 | {basic.get("character_class", "알 수 없음")} |
| 월드 | {basic.get("world_name", "알 수 없음")} |

## 스탯 정보

```json
{json.dumps(stat, ensure_ascii=False, indent=2)}
```

---
*출처: 넥슨 Open API 실시간 조회*
"""
    return context
