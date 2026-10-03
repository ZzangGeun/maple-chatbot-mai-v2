# tests/test_character_context.py
"""
챗봇 캐릭터 정보 조회 테스트

- 넥슨 API 응답 → 답변 모델용 요약 (ai_server.graph.tools.character_context)
- 조회 대상·정보 종류 결정과 조회 실패 안내 (ai_server.graph.nodes.nexon_nodes)
넥슨 API와 LLM은 호출하지 않습니다.
"""

from unittest.mock import AsyncMock

import pytest
from langchain_core.messages import HumanMessage

from ai_server.graph.nodes import nexon_nodes
from ai_server.graph.tools import character_context as cc
from common.exceptions.nexon import ApiRateLimitExceeded, CharacterNotFound, NexonApiError
from common.nexon import CharacterFetchResult

BASIC = {
    "character_name": "테스트캐릭터",
    "world_name": "스카니아",
    "character_class": "아델",
    "character_class_level": "6",
    "character_level": 285,
    "character_exp_rate": "12.345",
    "character_guild_name": None,
}

WEAPON = {
    "item_equipment_slot": "무기",
    "item_name": "제네시스 브레스",
    "starforce": "22",
    "potential_option_grade": "레전드리",
    "potential_option_1": "보스 몬스터 데미지 +40%",
    "potential_option_2": "공격력 +12%",
    "potential_option_3": None,
    "additional_potential_option_grade": "유니크",
    "additional_potential_option_1": "공격력 +9%",
    "item_add_option": {"str": "100", "dex": "0", "attack_power": "246", "boss_damage": "0", "damage": "0"},
    "soul_name": "위대한 칼로스의 소울 적용",
    "soul_option": "공격력 +3%",
    "special_ring_level": 0,
}


# ---------------------------------------------------------------------------
# 요약 포맷
# ---------------------------------------------------------------------------


def test_format_basic_and_stat() -> None:
    basic = cc.format_basic(BASIC)
    stat = cc.format_stat(
        {
            "final_stat": [
                {"stat_name": "전투력", "stat_value": "51444830"},
                {"stat_name": "보스 몬스터 데미지", "stat_value": "310.00"},
                {"stat_name": "재사용 대기시간 감소 (초)", "stat_value": "2"},
                {"stat_name": "AP 배분 STR", "stat_value": "4"},
            ]
        }
    )

    assert "- 캐릭터명: 테스트캐릭터 (스카니아)" in basic
    assert "- 직업: 아델 (6차 전직)" in basic
    assert "- 레벨: 285 (경험치 12.345%)" in basic
    assert "- 길드: 없음" in basic
    assert "- 전투력: 51,444,830" in stat
    assert "- 보스 몬스터 데미지: 310%" in stat
    assert "- 재사용 대기시간 감소: 2초" in stat
    # 답변에 필요 없는 스탯(AP 배분 등)은 넣지 않습니다.
    assert "AP 배분" not in stat


def test_format_equipment_summarizes_one_line_per_item() -> None:
    text = cc.format_equipment(
        {
            "preset_no": 2,
            "item_equipment": [WEAPON, {"item_equipment_slot": "뱃지", "item_name": "크리스탈 웬투스 뱃지"}],
            "title": {"title_name": "판단이 느리다!"},
        }
    )

    assert text.startswith("### 장착 장비 (프리셋 2)")
    assert (
        "- 무기: 제네시스 브레스 | 22성 | 잠재 레전드리(보스 몬스터 데미지 +40% / 공격력 +12%)"
        " | 에디 유니크(공격력 +9%) | 추옵 STR +100, 공격력 +246"
        " | 소울 위대한 칼로스의 소울 적용(공격력 +3%)"
    ) in text
    assert "- 뱃지: 크리스탈 웬투스 뱃지" in text
    assert "- 칭호: 판단이 느리다!" in text


def test_format_symbol_hexa_and_ability() -> None:
    symbol = cc.format_symbol(
        {
            "symbol": [
                {"symbol_name": "아케인심볼 : 소멸의 여로", "symbol_level": 20},
                {"symbol_name": "어센틱심볼 : 세르니움", "symbol_level": 11},
                {"symbol_name": "어센틱심볼 : 아르크스", "symbol_level": 9},
            ]
        }
    )
    hexa = cc.format_hexa(
        {"character_hexa_core_equipment": [{"hexa_core_name": "솔 야누스", "hexa_core_level": 14, "hexa_core_type": "공용 코어"}]},
        {
            "character_hexa_stat_core": [
                {
                    "main_stat_name": "주력 스탯 증가",
                    "main_stat_level": 6,
                    "sub_stat_name_1": "공격력 증가",
                    "sub_stat_level_1": 10,
                    "sub_stat_name_2": "보스 데미지 증가",
                    "sub_stat_level_2": 4,
                }
            ]
        },
    )
    ability = cc.format_ability(
        {
            "preset_no": 2,
            "ability_preset_1": {"ability_preset_grade": "레전드리", "ability_info": [{"ability_value": "보스 데미지 20%"}]},
            "ability_preset_2": {"ability_preset_grade": "유니크", "ability_info": [{"ability_value": "메소 획득량 15%"}]},
        }
    )

    assert "- 아케인심볼: 소멸의 여로 Lv.20" in symbol
    assert "- 어센틱심볼: 세르니움 Lv.11, 아르크스 Lv.9" in symbol
    assert "- 공용 코어: 솔 야누스 Lv.14" in hexa
    assert "- HEXA 스탯 I: 주력 스탯 증가 Lv.6 / 공격력 증가 Lv.10 / 보스 데미지 증가 Lv.4" in hexa
    assert "- 프리셋 1 (레전드리): 보스 데미지 20%" in ability
    assert "- 프리셋 2 (유니크 - 사용 중): 메소 획득량 15%" in ability


def test_format_union_and_dojang() -> None:
    assert "그랜드 마스터 유니온 4 (유니온 레벨 9,780)" in cc.format_union(
        {"union_grade": "그랜드 마스터 유니온 4", "union_level": 9780, "union_artifact_level": 53}
    )
    assert "- 기록 없음" in cc.format_dojang({"dojang_best_floor": 0})
    assert "- 최고 기록: 65층 (12분 34초)" in cc.format_dojang(
        {"dojang_best_floor": 65, "dojang_best_time": 754}
    )


def test_build_context_marks_failed_sections() -> None:
    result = CharacterFetchResult(
        ocid="ocid-1",
        responses={"/character/basic": BASIC, "/character/stat": {"final_stat": []}},
        failed={"/character/item-equipment": NexonApiError()},
    )

    text = cc.build_character_context("테스트캐릭터", result, ["stat", "equipment"], is_main_character=True)

    assert text.startswith("사용자의 대표 캐릭터: 테스트캐릭터")
    assert "### 기본 정보" in text
    assert "### 장착 장비\n- 정보를 가져오지 못했습니다." in text


def test_paths_for_always_includes_basic_without_duplicates() -> None:
    assert cc.paths_for(["hexa", "stat", "hexa"]) == [
        "/character/basic",
        "/character/hexamatrix",
        "/character/hexamatrix-stat",
        "/character/stat",
    ]


# ---------------------------------------------------------------------------
# 조회 대상 / 정보 종류 결정
# ---------------------------------------------------------------------------

MAIN = {"main_character": {"character_name": "대표캐릭", "ocid": "main-ocid"}}


@pytest.mark.parametrize(
    ("query", "user_context", "expected"),
    [
        # 질문에 다른 캐릭터명이 있으면 그 캐릭터를 조회합니다.
        ({"character_name": "다른캐릭"}, MAIN, ("다른캐릭", "", False)),
        # 이름이 없거나 대표 캐릭터와 같으면 대표 캐릭터를 OCID로 바로 조회합니다.
        ({"refers_to_self": True}, MAIN, ("대표캐릭", "main-ocid", True)),
        ({}, MAIN, ("대표캐릭", "main-ocid", True)),
        ({"character_name": "대표캐릭"}, MAIN, ("대표캐릭", "main-ocid", True)),
        # 비로그인(대표 캐릭터 없음)이면 질문 속 캐릭터만 조회할 수 있습니다.
        ({"character_name": "다른캐릭"}, {}, ("다른캐릭", "", False)),
        ({"refers_to_self": True}, {}, None),
        ({}, None, None),
    ],
)
def test_resolve_target(query, user_context, expected) -> None:
    assert nexon_nodes.resolve_target(query, user_context) == expected


def test_select_aspects() -> None:
    assert nexon_nodes.select_aspects({"aspects": ["hexa", "unknown", "hexa", "stat"]}, "character") == [
        "hexa",
        "stat",
    ]
    assert nexon_nodes.select_aspects({}, "character") == ["stat"]
    assert nexon_nodes.select_aspects({}, "character_knowledge") == ["stat", "equipment", "symbol", "hexa"]
    assert len(nexon_nodes.select_aspects({"aspects": list(cc.ASPECT_PATHS)}, "character")) == nexon_nodes.MAX_ASPECTS


# ---------------------------------------------------------------------------
# 노드 동작
# ---------------------------------------------------------------------------


def _state(query: dict, user_context: dict | None = None, route: str = "character") -> dict:
    return {
        "messages": [HumanMessage("질문")],
        "character_query": query,
        "user_context": user_context or {},
        "route": route,
    }


@pytest.mark.asyncio
async def test_fetch_node_uses_main_character_ocid(monkeypatch: pytest.MonkeyPatch) -> None:
    fetch = AsyncMock(
        return_value=CharacterFetchResult(ocid="main-ocid", responses={"/character/basic": BASIC})
    )
    monkeypatch.setattr(nexon_nodes._nexon_client, "fetch_character", fetch)

    output = await nexon_nodes.fetch_character_node(_state({"refers_to_self": True, "aspects": ["union"]}, MAIN))

    fetch.assert_awaited_once_with(
        ["/character/basic", "/user/union"], character_name="대표캐릭", ocid="main-ocid"
    )
    assert output["character_context"].startswith("사용자의 대표 캐릭터: 대표캐릭")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (CharacterNotFound("없는캐릭"), "'없는캐릭' 캐릭터를 찾을 수 없습니다"),
        (ApiRateLimitExceeded(), "요청이 몰려"),
        (NexonApiError("점검 중"), "점검 또는 일시적인 오류"),
    ],
)
async def test_fetch_node_turns_errors_into_guidance(
    monkeypatch: pytest.MonkeyPatch, error: Exception, expected: str
) -> None:
    monkeypatch.setattr(nexon_nodes._nexon_client, "fetch_character", AsyncMock(side_effect=error))

    output = await nexon_nodes.fetch_character_node(_state({"character_name": "없는캐릭"}))

    assert "캐릭터 조회 실패" in output["character_context"]
    assert expected in output["character_context"]


@pytest.mark.asyncio
async def test_fetch_node_without_target_asks_for_name(monkeypatch: pytest.MonkeyPatch) -> None:
    fetch = AsyncMock()
    monkeypatch.setattr(nexon_nodes._nexon_client, "fetch_character", fetch)

    self_output = await nexon_nodes.fetch_character_node(_state({"refers_to_self": True}))
    other_output = await nexon_nodes.fetch_character_node(_state({}))

    fetch.assert_not_awaited()
    assert "연동된 대표 캐릭터가 없습니다" in self_output["character_context"]
    assert "캐릭터명을 알려 달라고" in other_output["character_context"]


@pytest.mark.asyncio
async def test_extract_node_falls_back_when_llm_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        nexon_nodes, "extract_character_query", AsyncMock(side_effect=RuntimeError("LLM 장애"))
    )

    output = await nexon_nodes.extract_character_node(_state({}))

    assert output["character_query"] == {"character_name": None, "refers_to_self": False, "aspects": []}
