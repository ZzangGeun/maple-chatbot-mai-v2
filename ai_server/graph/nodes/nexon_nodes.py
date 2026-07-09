import json
import logging
from typing import Optional
from pydantic import BaseModel, Field

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig

from ai_server.graph.state.nexon_state import NexonState
from ai_server.graph.tools.nexon_api_tool import NexonAPIClient
from ai_server.llm.gemini_loader import get_gemini_llm
from ai_server.prompts import PromptTemplate, get_prompt

logger = logging.getLogger("NexonNodes")

# 싱글턴 클라이언트
_nexon_client = NexonAPIClient()


class MapleCharacterIntent(BaseModel):
    """Gemini로부터 구조화된 출력을 받기 위해 정의한 Pydantic 스키마.
    사용자의 질문 속에서 메이플 관련 핵심 정보를 식별하여 매핑합니다.
    """
    character_name: Optional[str] = Field(
        default=None, 
        description="검색 타겟이 되는 캐릭터의 이름 (예: '아델은최강')"
    )
    world: Optional[str] = Field(
        default=None, 
        description="캐릭터가 머무는 서버/월드 이름 (예: '스카니아', '루나')"
    )
    item_name: Optional[str] = Field(
        default=None, 
        description="성능 및 가격 정보를 얻고자 하는 아이템 이름 (예: '앱솔랩스 시프글러브')"
    )


async def gemini_intent_extract_node(state: NexonState, config: RunnableConfig = None) -> dict:
    """Gemini를 사용한 넥슨 API 파라미터(엔티티) 구조화 추출 노드.
    
    문자열 파싱 과정(백틱 제거, JSON 변환 등)에서의 에러 발생 가능성을 
    근본적으로 배제하기 위해 LangChain의 `with_structured_output` API를 활용합니다.
    """
    # 구조화 추출은 결정적 출력이 필요하므로 temperature=0.0을 사용합니다.
    llm = get_gemini_llm(temperature=0.0)
    # Pydantic 모델을 전달하여 Gemini가 정의된 형태의 JSON 객체를 바로 채워서 응답하도록 유도합니다.
    structured_llm = llm.with_structured_output(MapleCharacterIntent)
    
    question = state["messages"][-1].content

    extract_system = get_prompt(PromptTemplate.INTENT_EXTRACT_SYSTEM, model="gemini")

    prompt = ChatPromptTemplate.from_messages([
        ("system", extract_system),
        ("human", "{question}")
    ])

    chain = prompt | structured_llm

    try:
        # 모델 구조화 호출 실행
        result: MapleCharacterIntent = await chain.ainvoke({"question": question}, config=config)
        entities = result.model_dump()
    except Exception as e:
        # 추출 실패 시 캐릭터명을 비워 둔다.
        # (질문 전체를 캐릭터명으로 사용하면 넥슨 API에 잘못된 요청이 나가므로,
        # nexon_api_tool_node의 '캐릭터명 인식 실패' 경로를 타도록 합니다.)
        logger.error(f"[GeminiIntentExtract] 구조화 추출 중 예상치 못한 오류 발생: {e}")
        entities = {"character_name": None, "world": None, "item_name": None}

    logger.info(f"[GeminiIntentExtract] 최종 추출된 엔티티: {entities}")
    return {"extracted_entities": entities}


async def nexon_api_tool_node(state: NexonState) -> dict:
    """추출된 캐릭터명으로 넥슨 Open API를 호출하고 마크다운 형태로 변환하는 노드.
    
    I/O 바운드 작업인 외부 API 요청의 비동기 이점을 위해 async/await를 유지합니다.
    """
    entities = state.get("extracted_entities") or {}
    character_name: str = entities.get("character_name", "")

    if not character_name:
        logger.warning("[NexonAPI] extracted_entities에 character_name이 없어 기본 실패 반환 처리합니다.")
        context = "## 캐릭터 조회 실패\n캐릭터명을 인식하지 못했습니다."
        return {"context": context}

    logger.info(f"[NexonAPI] 캐릭터 '{character_name}' API 실시간 조회 및 데이터 파이프라인 구동")

    try:
        summary = await _nexon_client.get_character_summary(character_name)
        context = _format_character_context(character_name, summary)

    except Exception as e:
        # 넥슨 API 장애 상황이나 429 Rate Limit 상황 시 에러 세부 내용을 담아 뷰어에 전달합니다.
        logger.error(f"[NexonAPI] 캐릭터 '{character_name}' API 호출 실패: {e}")
        context = (
            f"## 캐릭터 조회 오류\n"
            f"'{character_name}' 캐릭터 정보를 가져오는 데 실패했습니다.\n"
            f"오류 내용: {e}"
        )

    return {"context": context}


def _format_character_context(character_name: str, summary: dict) -> str:
    """넥슨 API 응답 결과를 Gemini RAG 답변 생성 모델이 분석하기 좋은 최적의 마크다운 형식으로 포맷팅합니다.
    
    데이터 가독성을 위해 기본 프로필은 테이블 구조로, 가변적인 스탯 정보는 JSON 형태로 보존합니다.
    """
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
