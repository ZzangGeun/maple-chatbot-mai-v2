# ai_server/graph/tools/character_context.py
"""
넥슨 Open API 캐릭터 정보 → 답변 모델 참고 자료 변환 모듈

질문에 필요한 정보 종류(aspect)만 조회하도록 엔드포인트를 고르고,
원본 JSON 대신 짧은 한국어 요약으로 바꿔 토큰 사용량을 줄이고 해석 오류를 막습니다.
조회할 수 없을 때는 답변 모델이 사용자에게 전할 안내를 참고 자료로 돌려줍니다.
"""

from collections.abc import Callable, Iterable
from typing import Any, Literal

from common.nexon import CharacterFetchResult

# 질문에서 고를 수 있는 캐릭터 정보 종류
CharacterAspect = Literal[
    "stat",
    "equipment",
    "set_effect",
    "symbol",
    "hexa",
    "vmatrix",
    "ability",
    "hyper_stat",
    "link_skill",
    "union",
    "dojang",
]

# 기본 정보(레벨·직업·월드·길드)는 항상 함께 조회합니다.
BASIC_PATH = "/character/basic"

ASPECT_PATHS: dict[str, tuple[str, ...]] = {
    "stat": ("/character/stat",),
    "equipment": ("/character/item-equipment",),
    "set_effect": ("/character/set-effect",),
    "symbol": ("/character/symbol-equipment",),
    "hexa": ("/character/hexamatrix", "/character/hexamatrix-stat"),
    "vmatrix": ("/character/vmatrix",),
    "ability": ("/character/ability",),
    "hyper_stat": ("/character/hyper-stat",),
    "link_skill": ("/character/link-skill",),
    "union": ("/user/union",),
    "dojang": ("/character/dojang",),
}

ASPECT_LABELS: dict[str, str] = {
    "stat": "종합 능력치",
    "equipment": "장착 장비",
    "set_effect": "세트 효과",
    "symbol": "심볼",
    "hexa": "HEXA 매트릭스 (6차)",
    "vmatrix": "V 매트릭스 (5차)",
    "ability": "어빌리티",
    "hyper_stat": "하이퍼 스탯",
    "link_skill": "링크 스킬",
    "union": "유니온",
    "dojang": "무릉도장",
}

# 질문에서 필요한 정보를 고르지 못했을 때 경로별로 사용할 기본 정보
DEFAULT_ASPECTS: dict[str, list[str]] = {
    "character": ["stat"],
    "character_knowledge": ["stat", "equipment", "symbol", "hexa"],
}


def paths_for(aspects: Iterable[str]) -> list[str]:
    """정보 종류 목록을 조회할 엔드포인트 목록으로 바꿉니다. (기본 정보 포함, 중복 제거)"""
    paths = [BASIC_PATH]
    for aspect in aspects:
        paths.extend(ASPECT_PATHS.get(aspect, ()))
    return list(dict.fromkeys(paths))


# ---------------------------------------------------------------------------
# 포맷 도우미
# ---------------------------------------------------------------------------


def _num(value: Any) -> str:
    """숫자 문자열에 천 단위 구분 기호를 붙입니다. (숫자가 아니면 그대로)"""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    if number.is_integer():
        return f"{int(number):,}"
    return f"{number:,.2f}".rstrip("0").rstrip(".")


def _section(title: str, lines: list[str]) -> str:
    return "\n".join([f"### {title}", *lines])


# ---------------------------------------------------------------------------
# 엔드포인트별 요약
# ---------------------------------------------------------------------------


def format_basic(data: dict) -> str:
    name = data.get("character_name") or "알 수 없음"
    world = data.get("world_name")
    lines = [f"- 캐릭터명: {name}" + (f" ({world})" if world else "")]

    job = data.get("character_class")
    if job:
        job_level = data.get("character_class_level")
        lines.append(f"- 직업: {job}" + (f" ({job_level}차 전직)" if job_level else ""))

    level = data.get("character_level")
    if level is not None:
        exp_rate = data.get("character_exp_rate")
        lines.append(f"- 레벨: {level}" + (f" (경험치 {exp_rate}%)" if exp_rate else ""))

    lines.append(f"- 길드: {data.get('character_guild_name') or '없음'}")
    return _section("기본 정보", lines)


# (API 스탯 이름, 표시 이름, 단위)
_STAT_FIELDS: tuple[tuple[str, str, str], ...] = (
    ("전투력", "전투력", ""),
    ("최소 스탯공격력", "최소 스탯공격력", ""),
    ("최대 스탯공격력", "최대 스탯공격력", ""),
    ("데미지", "데미지", "%"),
    ("보스 몬스터 데미지", "보스 몬스터 데미지", "%"),
    ("최종 데미지", "최종 데미지", "%"),
    ("방어율 무시", "방어율 무시", "%"),
    ("크리티컬 확률", "크리티컬 확률", "%"),
    ("크리티컬 데미지", "크리티컬 데미지", "%"),
    ("공격력", "공격력", ""),
    ("마력", "마력", ""),
    ("STR", "STR", ""),
    ("DEX", "DEX", ""),
    ("INT", "INT", ""),
    ("LUK", "LUK", ""),
    ("HP", "HP", ""),
    ("스타포스", "스타포스", ""),
    ("아케인포스", "아케인포스", ""),
    ("어센틱포스", "어센틱포스", ""),
    ("재사용 대기시간 감소 (%)", "재사용 대기시간 감소", "%"),
    ("재사용 대기시간 감소 (초)", "재사용 대기시간 감소", "초"),
    ("재사용 대기시간 미적용", "재사용 대기시간 미적용", "%"),
    ("버프 지속시간", "버프 지속시간", "%"),
    ("일반 몬스터 데미지", "일반 몬스터 데미지", "%"),
    ("속성 내성 무시", "속성 내성 무시", "%"),
    ("상태이상 추가 데미지", "상태이상 추가 데미지", "%"),
    ("아이템 드롭률", "아이템 드롭률", "%"),
    ("메소 획득량", "메소 획득량", "%"),
    ("추가 경험치 획득", "추가 경험치 획득", "%"),
)


def format_stat(data: dict) -> str:
    stats = {
        stat.get("stat_name"): stat.get("stat_value")
        for stat in data.get("final_stat") or []
    }
    lines = [
        f"- {label}: {_num(stats[name])}{unit}"
        for name, label, unit in _STAT_FIELDS
        if stats.get(name) not in (None, "")
    ]
    return _section(ASPECT_LABELS["stat"], lines or ["- 정보 없음"])


# 추가옵션 키 → (표시 이름, 단위)
_ADD_OPTION_LABELS: tuple[tuple[str, str, str], ...] = (
    ("str", "STR", ""),
    ("dex", "DEX", ""),
    ("int", "INT", ""),
    ("luk", "LUK", ""),
    ("max_hp", "최대 HP", ""),
    ("attack_power", "공격력", ""),
    ("magic_power", "마력", ""),
    ("boss_damage", "보스 몬스터 데미지", "%"),
    ("damage", "데미지", "%"),
    ("all_stat", "올스탯", "%"),
)


def _add_options(option: dict | None) -> str:
    parts = []
    for key, label, unit in _ADD_OPTION_LABELS:
        value = (option or {}).get(key)
        if value not in (None, "", "0", 0):
            parts.append(f"{label} +{value}{unit}")
    return ", ".join(parts)


def _potential(grade: str | None, options: list[str | None]) -> str:
    values = [option for option in options if option]
    if not grade:
        return ""
    return f"{grade}({' / '.join(values)})" if values else grade


def _format_item(item: dict) -> str:
    slot = item.get("item_equipment_slot") or item.get("item_equipment_part") or "기타"
    parts = [f"{slot}: {item.get('item_name') or '알 수 없음'}"]

    starforce = str(item.get("starforce") or "0")
    if starforce != "0":
        parts.append(f"{starforce}성")

    potential = _potential(
        item.get("potential_option_grade"),
        [item.get(f"potential_option_{i}") for i in (1, 2, 3)],
    )
    if potential:
        parts.append(f"잠재 {potential}")

    additional = _potential(
        item.get("additional_potential_option_grade"),
        [item.get(f"additional_potential_option_{i}") for i in (1, 2, 3)],
    )
    if additional:
        parts.append(f"에디 {additional}")

    add_options = _add_options(item.get("item_add_option"))
    if add_options:
        parts.append(f"추옵 {add_options}")

    if item.get("soul_name"):
        soul_option = item.get("soul_option")
        parts.append(f"소울 {item['soul_name']}" + (f"({soul_option})" if soul_option else ""))

    if item.get("special_ring_level"):
        parts.append(f"특수 반지 {item['special_ring_level']}레벨")

    return "- " + " | ".join(parts)


def format_equipment(data: dict) -> str:
    title = ASPECT_LABELS["equipment"]
    if data.get("preset_no"):
        title += f" (프리셋 {data['preset_no']})"

    lines = [_format_item(item) for item in data.get("item_equipment") or []]
    title_name = (data.get("title") or {}).get("title_name")
    if title_name:
        lines.append(f"- 칭호: {title_name}")
    return _section(title, lines or ["- 장착한 장비 없음"])


def format_set_effect(data: dict) -> str:
    lines = [
        f"- {effect.get('set_name')}: {effect.get('total_set_count')}세트"
        for effect in data.get("set_effect") or []
    ]
    return _section(ASPECT_LABELS["set_effect"], lines or ["- 적용 중인 세트 효과 없음"])


def format_symbol(data: dict) -> str:
    # "아케인심볼 : 소멸의 여로" → 종류별로 묶어서 표시합니다.
    groups: dict[str, list[str]] = {}
    for symbol in data.get("symbol") or []:
        kind, _, region = (symbol.get("symbol_name") or "").partition(" : ")
        groups.setdefault(kind or "심볼", []).append(
            f"{region or kind} Lv.{symbol.get('symbol_level')}"
        )
    lines = [f"- {kind}: {', '.join(entries)}" for kind, entries in groups.items()]
    return _section(ASPECT_LABELS["symbol"], lines or ["- 장착한 심볼 없음"])


_HEXA_STAT_KEYS = (
    ("character_hexa_stat_core", "I"),
    ("character_hexa_stat_core_2", "II"),
    ("character_hexa_stat_core_3", "III"),
)


def format_hexa(cores: dict | None, stats: dict | None) -> str:
    groups: dict[str, list[str]] = {}
    for core in (cores or {}).get("character_hexa_core_equipment") or []:
        groups.setdefault(core.get("hexa_core_type") or "코어", []).append(
            f"{core.get('hexa_core_name')} Lv.{core.get('hexa_core_level')}"
        )
    lines = [f"- {kind}: {', '.join(entries)}" for kind, entries in groups.items()]
    if not groups:
        lines.append("- 장착한 HEXA 코어 없음")

    for key, numeral in _HEXA_STAT_KEYS:
        for core in (stats or {}).get(key) or []:
            lines.append(
                f"- HEXA 스탯 {numeral}: {core.get('main_stat_name')} Lv.{core.get('main_stat_level')}"
                f" / {core.get('sub_stat_name_1')} Lv.{core.get('sub_stat_level_1')}"
                f" / {core.get('sub_stat_name_2')} Lv.{core.get('sub_stat_level_2')}"
            )
    return _section(ASPECT_LABELS["hexa"], lines)


def format_vmatrix(data: dict) -> str:
    groups: dict[str, list[str]] = {}
    for core in data.get("character_v_core_equipment") or []:
        if not core.get("v_core_name"):
            continue
        groups.setdefault(core.get("v_core_type") or "코어", []).append(
            f"{core['v_core_name']} Lv.{core.get('v_core_level')}"
        )
    lines = [f"- {kind}: {', '.join(entries)}" for kind, entries in groups.items()]
    return _section(ASPECT_LABELS["vmatrix"], lines or ["- 장착한 V 코어 없음"])


def format_ability(data: dict) -> str:
    lines = []
    for number in (1, 2, 3):
        preset = data.get(f"ability_preset_{number}") or {}
        values = [a.get("ability_value") for a in preset.get("ability_info") or [] if a.get("ability_value")]
        if values:
            in_use = " - 사용 중" if str(data.get("preset_no")) == str(number) else ""
            lines.append(
                f"- 프리셋 {number} ({preset.get('ability_preset_grade')}{in_use}): {' / '.join(values)}"
            )

    if not lines:
        values = [a.get("ability_value") for a in data.get("ability_info") or [] if a.get("ability_value")]
        if values:
            lines.append(f"- {data.get('ability_grade')}: {' / '.join(values)}")
    return _section(ASPECT_LABELS["ability"], lines or ["- 정보 없음"])


def format_hyper_stat(data: dict) -> str:
    preset = data.get("use_preset_no") or "1"
    lines = [
        f"- {stat.get('stat_type')} Lv.{stat.get('stat_level')}"
        + (f" ({stat['stat_increase']})" if stat.get("stat_increase") else "")
        for stat in data.get(f"hyper_stat_preset_{preset}") or []
        if stat.get("stat_level")
    ]
    return _section(
        f"{ASPECT_LABELS['hyper_stat']} (프리셋 {preset})",
        lines or ["- 투자한 하이퍼 스탯 없음"],
    )


def format_link_skill(data: dict) -> str:
    skills = [
        f"{skill.get('skill_name')} Lv.{skill.get('skill_level')}"
        for skill in data.get("character_link_skill") or []
    ]
    lines = [f"- 장착: {', '.join(skills) or '없음'}"]
    owned = (data.get("character_owned_link_skill") or {}).get("skill_name")
    if owned:
        lines.append(f"- 이 캐릭터가 제공하는 링크 스킬: {owned}")
    return _section(ASPECT_LABELS["link_skill"], lines)


def format_union(data: dict) -> str:
    lines = [
        f"- {data.get('union_grade') or '등급 정보 없음'} (유니온 레벨 {_num(data.get('union_level'))})"
    ]
    if data.get("union_artifact_level") is not None:
        lines.append(f"- 아티팩트 레벨: {data['union_artifact_level']}")
    return _section(ASPECT_LABELS["union"], lines)


def format_dojang(data: dict) -> str:
    floor = data.get("dojang_best_floor") or 0
    if not floor:
        return _section(ASPECT_LABELS["dojang"], ["- 기록 없음"])
    seconds = int(data.get("dojang_best_time") or 0)
    return _section(
        ASPECT_LABELS["dojang"],
        [f"- 최고 기록: {floor}층 ({seconds // 60}분 {seconds % 60}초)"],
    )


_FORMATTERS: dict[str, Callable[[dict[str, dict]], str]] = {
    "stat": lambda r: format_stat(r["/character/stat"]),
    "equipment": lambda r: format_equipment(r["/character/item-equipment"]),
    "set_effect": lambda r: format_set_effect(r["/character/set-effect"]),
    "symbol": lambda r: format_symbol(r["/character/symbol-equipment"]),
    "hexa": lambda r: format_hexa(r.get("/character/hexamatrix"), r.get("/character/hexamatrix-stat")),
    "vmatrix": lambda r: format_vmatrix(r["/character/vmatrix"]),
    "ability": lambda r: format_ability(r["/character/ability"]),
    "hyper_stat": lambda r: format_hyper_stat(r["/character/hyper-stat"]),
    "link_skill": lambda r: format_link_skill(r["/character/link-skill"]),
    "union": lambda r: format_union(r["/user/union"]),
    "dojang": lambda r: format_dojang(r["/character/dojang"]),
}


def build_character_context(
    character_name: str,
    result: CharacterFetchResult,
    aspects: Iterable[str],
    *,
    is_main_character: bool = False,
) -> str:
    """조회 결과를 답변 모델용 참고 자료로 요약합니다. 일부 정보 조회에 실패하면 그 사실을 함께 적습니다."""
    responses = result.responses
    target = "사용자의 대표 캐릭터" if is_main_character else "조회한 캐릭터"
    sections = [f"{target}: {character_name} (넥슨 Open API 조회 결과)"]

    basic = responses.get(BASIC_PATH)
    if basic:
        sections.append(format_basic(basic))

    for aspect in aspects:
        if not any(path in responses for path in ASPECT_PATHS[aspect]):
            sections.append(_section(ASPECT_LABELS[aspect], ["- 정보를 가져오지 못했습니다."]))
            continue
        sections.append(_FORMATTERS[aspect](responses))

    return "\n\n".join(sections)


# ---------------------------------------------------------------------------
# 조회할 수 없을 때 답변 모델에 전할 안내
# ---------------------------------------------------------------------------


def describe_missing_target(refers_to_self: bool) -> str:
    if refers_to_self:
        return (
            "## 캐릭터 조회 불가\n"
            "사용자가 본인 캐릭터에 대해 물었지만 연동된 대표 캐릭터가 없습니다. "
            "캐릭터명을 함께 알려 주거나, 로그인하면 대표 캐릭터 기준으로 '내 캐릭터'라고 물어볼 수 있다고 안내하세요."
        )
    return (
        "## 캐릭터 조회 불가\n"
        "질문에서 조회할 캐릭터명을 찾지 못했습니다. 어떤 캐릭터인지 캐릭터명을 알려 달라고 안내하세요."
    )


def describe_not_found(character_name: str) -> str:
    return (
        "## 캐릭터 조회 실패\n"
        f"'{character_name}' 캐릭터를 찾을 수 없습니다. "
        "캐릭터명을 정확히(띄어쓰기 없이) 입력했는지 확인해 달라고 안내하세요."
    )


def describe_api_error(character_name: str, *, rate_limited: bool = False) -> str:
    reason = (
        "넥슨 Open API 요청이 몰려"
        if rate_limited
        else "넥슨 Open API 점검 또는 일시적인 오류로"
    )
    return (
        "## 캐릭터 조회 실패\n"
        f"{reason} '{character_name}' 캐릭터 정보를 가져오지 못했습니다. "
        "잠시 후 다시 시도해 달라고 안내하세요."
    )
