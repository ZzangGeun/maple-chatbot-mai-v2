# ai_server/graph/nodes/nexon_nodes.py
"""
넥슨 API 조회 노드 모음

역할:
  - nexon_api_tool_node: extracted_entities의 캐릭터명으로 넥슨 Open API를 호출하고
                         조회 결과를 state["context"]에 저장합니다.
                         이후 gemini_generate_rag_node에서 이 context를 사용합니다.

설계 의도:
  RAG 검색과 넥슨 API 조회 모두 최종적으로 gemini_generate_rag_node로 흘러가도록 설계했습니다.
  context 필드를 공유함으로써, Gemini 생성 노드를 하나만 유지할 수 있습니다.
"""

import json
import logging

from ai_server.graph.state import GraphState
from ai_server.graph.tools.nexon_api_tool import NexonAPIClient

logger = logging.getLogger("NexonNodes")

# 싱글턴 클라이언트 — 매 요청마다 aiohttp 세션 헤더를 재구성하지 않도록 합니다.
_nexon_client = NexonAPIClient()


async def nexon_api_tool_node(state: GraphState) -> dict:
    """
    로컬 LLM이 추출한 캐릭터명으로 넥슨 Open API를 호출합니다.

    조회 결과를 마크다운 형식의 context로 직렬화하여
    gemini_generate_rag_node에 전달합니다.

    Args:
        state: 현재 그래프 상태.
               state["extracted_entities"]["character_name"] 이 필수입니다.

    Returns:
        {"context": 넥슨 API 조회 결과 마크다운 문자열}
    """
    entities = state.get("extracted_entities") or {}
    character_name: str = entities.get("character_name", "")

    # 캐릭터명이 없으면 Gemini에게 "찾을 수 없음" 컨텍스트를 전달합니다.
    if not character_name:
        logger.warning("[NexonAPI] extracted_entities에 character_name 없음")
        context = "## 캐릭터 조회 실패\n캐릭터명을 인식하지 못했습니다."
        return {"context": context}

    logger.info(f"[NexonAPI] 캐릭터 조회 시작: {character_name}")

    try:
        # TODO: get_character_summary 내부의 실제 API 호출 구현 후 동작합니다.
        summary = await _nexon_client.get_character_summary(character_name)
        context = _format_character_context(character_name, summary)

    except Exception as e:
        logger.error(f"[NexonAPI] 캐릭터 조회 실패: {e}")
        # 오류 시에도 Gemini가 안내 메시지를 생성할 수 있도록 컨텍스트를 제공합니다.
        context = (
            f"## 캐릭터 조회 오류\n"
            f"'{character_name}' 캐릭터 정보를 가져오는 데 실패했습니다.\n"
            f"오류: {e}"
        )

    return {"context": context}


def _format_character_context(character_name: str, summary: dict) -> str:
    """
    넥슨 API 응답을 Gemini가 읽기 좋은 마크다운 형식으로 변환합니다.

    Args:
        character_name: 조회한 캐릭터명.
        summary: get_character_summary 반환값 {"basic": {...}, "stat": {...}}.

    Returns:
        마크다운 형식의 컨텍스트 문자열.
    """
    basic: dict = summary.get("basic", {})
    stat: dict = summary.get("stat", {})

    # TODO: 실제 API 응답 구조에 맞게 필드명을 수정하세요.
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
