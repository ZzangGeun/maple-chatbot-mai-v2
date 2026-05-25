# services/nexon/extractors.py
"""
넥슨 API 응답 데이터 추출·변환 함수 모음

각 함수는 API 응답 딕셔너리를 받아 정제된 딕셔너리를 반환합니다.
I/O가 없는 순수 변환 함수이므로 단위 테스트가 용이합니다.
"""

import logging

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 스탯
# ---------------------------------------------------------------------------

def extract_stat(stat_info: dict) -> dict:
    """
    스탯 정보를 추출하여 {stat_name: stat_value} 딕셔너리로 반환합니다.

    Args:
        stat_info: API에서 반환된 스탯 정보 딕셔너리.

    Returns:
        stat_name → stat_value 매핑 딕셔너리.
    """
    final_stat: dict = {}
    for stat in stat_info.get("final_stat", []):
        stat_name = stat["stat_name"].replace(" ", "_")
        final_stat[stat_name] = stat["stat_value"]
    return final_stat


# ---------------------------------------------------------------------------
# 장비
# ---------------------------------------------------------------------------

def _get_empty_equipment_data() -> dict:
    """빈 장비 데이터 기본값을 반환합니다."""
    return {
        "date": "정보 없음",
        "character_gender": "정보 없음",
        "character_class": "정보 없음",
        "preset_no": 0,
        "item_equipment": {},
        "item_equipment_preset_1": {},
        "item_equipment_preset_2": {},
        "item_equipment_preset_3": {},
        "title": {},
        "medal_shape": {},
        "dragon_equipment": [],
        "mechanic_equipment": [],
    }


def _process_equipment_list(equipment_list: list) -> dict:
    """장비 리스트를 slot → 상세정보 딕셔너리로 변환합니다."""
    processed: dict = {}
    for item in equipment_list:
        slot = item.get("item_equipment_slot", item.get("equipment_slot", "none"))
        processed[slot] = {
            "part": item.get("item_equipment_part", "none"),
            "slot": slot,
            "name": item.get("item_name", "none"),
            "icon": item.get("item_icon", "none"),
            "description": item.get("item_description", "none"),
            "shape_name": item.get("item_shape_name", "none"),
            "shape_icon": item.get("item_shape_icon", "none"),
            "gender": item.get("item_gender", "none"),
            "total_option": item.get("item_total_option", {}),
            "base_option": item.get("item_base_option", {}),
            "potential_option_flag": item.get("potential_option_flag", "none"),
            "additional_potential_option_flag": item.get("additional_potential_option_flag", "none"),
            "potential_option_grade": item.get("potential_option_grade", "none"),
            "additional_potential_option_grade": item.get("additional_potential_option_grade", "none"),
            "potential_options": [
                item.get("potential_option_1", "none"),
                item.get("potential_option_2", "none"),
                item.get("potential_option_3", "none"),
            ],
            "additional_potential_options": [
                item.get("additional_potential_option_1", "none"),
                item.get("additional_potential_option_2", "none"),
                item.get("additional_potential_option_3", "none"),
            ],
            "equipment_level_increase": item.get("equipment_level_increase", 0),
            "item_exceptional_option": item.get("item_exceptional_option", {}),
            "add_option": item.get("item_add_option", {}),
            "growth_exp": item.get("growth_exp", 0),
            "growth_level": item.get("growth_level", 0),
            "scroll_upgrade": item.get("scroll_upgrade", "none"),
            "cuttable_count": item.get("cuttable_count", "none"),
            "golden_hammer_flag": item.get("golden_hammer_flag", "none"),
            "scroll_resilience_count": item.get("scroll_resilience_count", "none"),
            "scroll_upgradable_count": item.get("scroll_upgradable_count", "none"),
            "soul_name": item.get("soul_name", "none"),
            "soul_option": item.get("soul_option", "none"),
            "item_etc_option": item.get("item_etc_option", {}),
            "starforce": item.get("starforce", "none"),
            "starforce_scroll_flag": item.get("starforce_scroll_flag", "none"),
            "item_starforce_option": item.get("item_starforce_option", {}),
            "special_ring_level": item.get("special_ring_level", 0),
            "date_expire": item.get("date_expire", "none"),
            "freestyle_flag": item.get("freestyle_flag", "none"),
        }
    return processed


def extract_item_equipment(item_equipment_info: dict) -> dict:
    """
    장비 아이템 정보를 추출하여 정리합니다.

    Args:
        item_equipment_info: API에서 반환된 장비 정보 딕셔너리.

    Returns:
        정리된 장비 데이터 딕셔너리. 유효하지 않은 입력이면 빈 데이터 반환.
    """
    if not isinstance(item_equipment_info, dict):
        return _get_empty_equipment_data()

    return {
        "date": item_equipment_info.get("date", "정보 없음"),
        "character_gender": item_equipment_info.get("character_gender", "정보 없음"),
        "character_class": item_equipment_info.get("character_class", "정보 없음"),
        "preset_no": item_equipment_info.get("preset_no", 0),
        "item_equipment": _process_equipment_list(item_equipment_info.get("item_equipment", [])),
        "item_equipment_preset_1": _process_equipment_list(item_equipment_info.get("item_equipment_preset_1", [])),
        "item_equipment_preset_2": _process_equipment_list(item_equipment_info.get("item_equipment_preset_2", [])),
        "item_equipment_preset_3": _process_equipment_list(item_equipment_info.get("item_equipment_preset_3", [])),
        "title": item_equipment_info.get("title", {}),
        "medal_shape": item_equipment_info.get("medal_shape", {}),
        "dragon_equipment": _process_equipment_list(item_equipment_info.get("dragon_equipment", [])),
        "mechanic_equipment": _process_equipment_list(item_equipment_info.get("mechanic_equipment", [])),
    }


# ---------------------------------------------------------------------------
# 어빌리티
# ---------------------------------------------------------------------------

def extract_ability(ability_info: dict) -> dict:
    """
    어빌리티 정보를 프리셋별로 추출합니다.

    Args:
        ability_info: API에서 반환된 어빌리티 정보 딕셔너리.

    Returns:
        {"preset_1": {...}, "preset_2": {...}, ...} 형태의 딕셔너리.
    """
    if not isinstance(ability_info, dict):
        return {}

    extracted: dict = {}
    for preset_key, preset_value in ability_info.items():
        if not preset_key.startswith("ability_preset_"):
            continue
        preset_number = preset_key.split("_")[-1]
        preset_data = {
            "description": preset_value.get("description", "정보 없음"),
            "grade": preset_value.get("ability_preset_grade", "정보 없음"),
            "abilities": [
                {
                    "no": ab.get("ability_no", "정보 없음"),
                    "grade": ab.get("ability_grade", "정보 없음"),
                    "value": ab.get("ability_value", "정보 없음"),
                }
                for ab in preset_value.get("ability_info", [])
            ],
        }
        extracted[f"preset_{preset_number}"] = preset_data

    return extracted


# ---------------------------------------------------------------------------
# 링크 스킬
# ---------------------------------------------------------------------------

def extract_link_skills(link_skill_info: dict) -> dict:
    """
    링크 스킬 정보를 프리셋별로 추출합니다.

    Args:
        link_skill_info: API에서 반환된 링크 스킬 정보 딕셔너리.

    Returns:
        {"preset_1": [...], "preset_2": [...], ...} 형태의 딕셔너리.
    """
    if not isinstance(link_skill_info, dict):
        return {}

    extracted: dict = {}
    for preset_key, skills in link_skill_info.items():
        if not preset_key.startswith("character_link_skill_preset_"):
            continue
        preset_number = preset_key.split("_")[-1]
        extracted[f"preset_{preset_number}"] = [
            {
                "name": skill.get("skill_name", "정보 없음"),
                "description": skill.get("skill_description", "정보 없음"),
                "level": skill.get("skill_level", 0),
                "effect": skill.get("skill_effect", "정보 없음"),
                "icon": skill.get("skill_icon", "정보 없음"),
            }
            for skill in (skills if isinstance(skills, list) else [])
        ]

    return extracted


# ---------------------------------------------------------------------------
# V매트릭스
# ---------------------------------------------------------------------------

def extract_vmatrix(vmatrix_info: dict) -> dict:
    """
    V매트릭스 정보를 추출합니다.

    Args:
        vmatrix_info: API에서 반환된 V매트릭스 정보 딕셔너리.

    Returns:
        코어 리스트와 잔여 포인트를 포함한 딕셔너리.
    """
    try:
        if not isinstance(vmatrix_info, dict):
            return {"error": "Invalid Data", "cores": []}

        return {
            "date": vmatrix_info.get("date", "정보 없음"),
            "character_class": vmatrix_info.get("character_class", "정보 없음"),
            "cores": [
                {
                    "slot_id": core.get("slot_id", "정보 없음"),
                    "slot_level": int(core.get("slot_level", 0)),
                    "core_name": core.get("v_core_name", "정보 없음"),
                    "core_type": core.get("v_core_type", "정보 없음"),
                    "core_level": int(core.get("v_core_level", 0)),
                    "skill_1": core.get("v_core_skill_1", "정보 없음"),
                    "skill_2": core.get("v_core_skill_2", "정보 없음"),
                    "skill_3": core.get("v_core_skill_3", "정보 없음"),
                }
                for core in (vmatrix_info.get("character_v_core_equipment") or [])
            ],
            "remain_points": int(
                vmatrix_info.get("character_v_matrix_remain_slot_upgrade_point", 0)
            ),
        }

    except Exception as e:
        logger.error(f"V매트릭스 정보 처리 중 오류: {e}")
        return {"error": str(e), "cores": []}


# ---------------------------------------------------------------------------
# 심볼
# ---------------------------------------------------------------------------

def extract_symbols(symbol_equipment_info: dict) -> dict:
    """
    심볼 장비 정보를 추출합니다.

    Args:
        symbol_equipment_info: API에서 반환된 심볼 정보 딕셔너리.

    Returns:
        심볼 리스트가 포함된 딕셔너리.
    """
    if not isinstance(symbol_equipment_info, dict):
        return {}

    return {
        "date": symbol_equipment_info.get("date", "정보 없음"),
        "character_class": symbol_equipment_info.get("character_class", "정보 없음"),
        "symbol": [
            {
                "symbol_name": sym.get("symbol_name", "정보 없음"),
                "symbol_icon": sym.get("symbol_icon", "정보 없음"),
                "symbol_description": sym.get("symbol_description", "정보 없음"),
                "symbol_force": sym.get("symbol_force", "정보 없음"),
                "symbol_level": sym.get("symbol_level", 0),
                "symbol_str": sym.get("symbol_str", "정보 없음"),
                "symbol_dex": sym.get("symbol_dex", "정보 없음"),
                "symbol_int": sym.get("symbol_int", "정보 없음"),
                "symbol_luk": sym.get("symbol_luk", "정보 없음"),
                "symbol_hp": sym.get("symbol_hp", "정보 없음"),
                "symbol_drop_rate": sym.get("symbol_drop_rate", "정보 없음"),
                "symbol_meso_rate": sym.get("symbol_meso_rate", "정보 없음"),
                "symbol_exp_rate": sym.get("symbol_exp_rate", "정보 없음"),
                "symbol_growth_count": sym.get("symbol_growth_count", 0),
                "symbol_require_growth_count": sym.get("symbol_require_growth_count", 0),
            }
            for sym in (symbol_equipment_info.get("symbol") or [])
        ],
    }


# ---------------------------------------------------------------------------
# 하이퍼 스탯
# ---------------------------------------------------------------------------

def extract_hyper_stat(hyper_stat_info: dict) -> dict:
    """
    하이퍼 스탯 정보를 프리셋별로 추출합니다.

    Args:
        hyper_stat_info: API에서 반환된 하이퍼 스탯 정보 딕셔너리.

    Returns:
        프리셋별 스탯 리스트가 포함된 딕셔너리.
    """
    if not isinstance(hyper_stat_info, dict):
        return {}

    presets: dict = {}
    for preset_num in range(1, 4):
        preset_key = f"hyper_stat_preset_{preset_num}"
        remain_point_key = f"hyper_stat_preset_{preset_num}_remain_point"

        if preset_key not in hyper_stat_info:
            continue

        preset_data = {
            "preset_number": preset_num,
            "remain_point": hyper_stat_info.get(remain_point_key, 0),
            "stats": [
                {
                    "stat_type": stat.get("stat_type", "정보 없음"),
                    "stat_point": stat.get("stat_point", 0),
                    "stat_level": stat.get("stat_level", 0),
                    "stat_increase": stat.get("stat_increase", "정보 없음"),
                }
                for stat in (hyper_stat_info.get(preset_key) or [])
            ],
        }
        presets[f"preset_{preset_num}"] = preset_data

    return {
        "date": hyper_stat_info.get("date", "정보 없음"),
        "character_class": hyper_stat_info.get("character_class", "정보 없음"),
        "use_preset_no": hyper_stat_info.get("use_preset_no", "정보 없음"),
        "use_available_hyper_stat": hyper_stat_info.get("use_available_hyper_stat", 0),
        "presets": presets,
    }


# ---------------------------------------------------------------------------
# 헥사 매트릭스
# ---------------------------------------------------------------------------

def extract_hexamatrix(hexamatrix_info: dict) -> dict:
    """
    헥사매트릭스 정보를 추출합니다.

    Args:
        hexamatrix_info: API에서 반환된 헥사매트릭스 정보 딕셔너리.

    Returns:
        헥사 코어 리스트가 포함된 딕셔너리.
    """
    if not isinstance(hexamatrix_info, dict):
        return {"hexamatrix": []}

    hexamatrix_list = [
        {
            "slot_id": hexa.get("slot_id", "정보 없음"),
            "slot_level": hexa.get("slot_level", 0),
            "main_stat_name": hexa.get("main_stat_name", "정보 없음"),
            "main_stat_level": hexa.get("main_stat_level", 0),
        }
        for hexa in hexamatrix_info.get("hexamatrix", [])
        if isinstance(hexa, dict)
    ]

    return {
        "date": hexamatrix_info.get("date", "정보 없음"),
        "hexamatrix": hexamatrix_list,
    }


def extract_hexamatrix_stat(hexamatrix_stat_info: dict) -> dict:
    """
    헥사 스탯 정보를 추출합니다.

    Args:
        hexamatrix_stat_info: API에서 반환된 헥사 스탯 정보 딕셔너리.

    Returns:
        헥사 스탯 코어 리스트가 포함된 딕셔너리.
    """
    if not isinstance(hexamatrix_stat_info, dict):
        return {}

    def _extract_stats(source_list: list | None) -> list:
        return [
            {
                "slot_id": stat.get("slot_id", "정보 없음"),
                "main_stat_name": stat.get("main_stat_name", "정보 없음"),
                "sub_stat_name_1": stat.get("sub_stat_name_1", "정보 없음"),
                "sub_stat_name_2": stat.get("sub_stat_name_2", "정보 없음"),
                "main_stat_level": int(stat.get("main_stat_level", 0)),
                "sub_stat_level_1": int(stat.get("sub_stat_level_1", 0)),
                "sub_stat_level_2": int(stat.get("sub_stat_level_2", 0)),
                "stat_grade": int(stat.get("stat_grade", 0)),
            }
            for stat in (source_list or [])
        ]

    return {
        "date": hexamatrix_stat_info.get("date", "정보 없음"),
        "hexamatrix_stat_1": _extract_stats(hexamatrix_stat_info.get("character_hexa_stat_core")),
        "hexamatrix_stat_2": _extract_stats(hexamatrix_stat_info.get("character_hexa_stat_core_2")),
        "hexamatrix_stat_3": _extract_stats(hexamatrix_stat_info.get("character_hexa_stat_core_3")),
    }


# ---------------------------------------------------------------------------
# 기타 스탯
# ---------------------------------------------------------------------------

def extract_other_stat(other_stat_info: dict) -> dict:
    """
    기타 스탯 정보를 추출합니다.

    Args:
        other_stat_info: API에서 반환된 기타 스탯 정보 딕셔너리.

    Returns:
        기타 스탯 리스트가 포함된 딕셔너리.
    """
    if not isinstance(other_stat_info, dict):
        return {}

    return {
        "date": other_stat_info.get("date", "정보 없음"),
        "other_stat": [
            {
                "other_stat_type": stat.get("other_stat_type", "정보 없음"),
                "stat_info": [
                    {
                        "stat_name": si.get("stat_name", "정보 없음"),
                        "stat_value": si.get("stat_value", "정보 없음"),
                    }
                    for si in (stat.get("stat_info") or [])
                ],
            }
            for stat in (other_stat_info.get("other_stat") or [])
        ],
    }


# ---------------------------------------------------------------------------
# 펫 장비
# ---------------------------------------------------------------------------

def extract_pet_equipment(pet_equipment_info: dict) -> dict:
    """
    펫 장비 정보를 추출합니다.

    Args:
        pet_equipment_info: API에서 반환된 펫 장비 정보 딕셔너리.

    Returns:
        펫 리스트가 포함된 딕셔너리 (최대 3마리).
    """
    if not isinstance(pet_equipment_info, dict):
        return {}

    pets = []
    for pet_num in range(1, 4):
        prefix = f"pet_{pet_num}"
        if f"{prefix}_name" not in pet_equipment_info:
            continue

        pet_data: dict = {
            "pet_number": pet_num,
            "name": pet_equipment_info.get(f"{prefix}_name", "정보 없음"),
            "nickname": pet_equipment_info.get(f"{prefix}_nickname", "정보 없음"),
            "icon": pet_equipment_info.get(f"{prefix}_icon", "정보 없음"),
            "description": pet_equipment_info.get(f"{prefix}_description", "정보 없음"),
            "pet_type": pet_equipment_info.get(f"{prefix}_pet_type", "정보 없음"),
            "date_expire": pet_equipment_info.get(f"{prefix}_date_expire", "정보 없음"),
            "appearance": pet_equipment_info.get(f"{prefix}_appearance", "정보 없음"),
            "appearance_icon": pet_equipment_info.get(f"{prefix}_appearance_icon", "정보 없음"),
            "skills": pet_equipment_info.get(f"{prefix}_skill", []),
            "equipment": {},
            "auto_skill": {},
        }

        # 장비
        eq = pet_equipment_info.get(f"{prefix}_equipment")
        if eq:
            pet_data["equipment"] = {
                "item_name": eq.get("item_name", "정보 없음"),
                "item_icon": eq.get("item_icon", "정보 없음"),
                "item_description": eq.get("item_description", "정보 없음"),
                "scroll_upgrade": eq.get("scroll_upgrade", 0),
                "scroll_upgradable": eq.get("scroll_upgradable", 0),
                "item_shape": eq.get("item_shape", "정보 없음"),
                "item_shape_icon": eq.get("item_shape_icon", "정보 없음"),
                "item_option": [
                    {
                        "option_type": opt.get("option_type", "정보 없음"),
                        "option_value": opt.get("option_value", "정보 없음"),
                    }
                    for opt in eq.get("item_option", [])
                ],
            }

        # 자동 스킬
        auto = pet_equipment_info.get(f"{prefix}_auto_skill")
        if auto:
            pet_data["auto_skill"] = {
                "skill_1": auto.get("skill_1", "정보 없음"),
                "skill_1_icon": auto.get("skill_1_icon", "정보 없음"),
                "skill_2": auto.get("skill_2", "정보 없음"),
                "skill_2_icon": auto.get("skill_2_icon", "정보 없음"),
            }

        pets.append(pet_data)

    return {
        "date": pet_equipment_info.get("date", "정보 없음"),
        "pets": pets,
    }


# ---------------------------------------------------------------------------
# 종합 추출 오케스트레이터
# ---------------------------------------------------------------------------

def all_info_extract(character_info: dict) -> dict:
    """
    캐릭터 API 응답 전체에서 필요한 모든 정보를 추출하여 종합합니다.

    Args:
        character_info: 각 API 엔드포인트 키를 키로 하는 응답 딕셔너리.

    Returns:
        섹션별로 정리된 캐릭터 종합 정보 딕셔너리.

    Raises:
        Exception: 추출 과정에서 예외 발생 시 상위로 전파합니다.
    """
    try:
        basic_info = character_info.get("get_character_basic_info", {})
        popularity_info = character_info.get("get_character_popularity_info", {})

        # 기본 정보에 인기도를 병합합니다.
        if popularity_info and "popularity" in popularity_info:
            basic_info["character_popularity"] = popularity_info["popularity"]

        return {
            "basic_info": basic_info,
            "stat_info": extract_stat(character_info.get("get_character_stat_info", {})),
            "item_info": extract_item_equipment(character_info.get("get_character_item_equipment_info", {})),
            "ability_info": extract_ability(character_info.get("get_character_ability_info", {})),
            "link_skill_info": extract_link_skills(character_info.get("get_character_link_skill_info", {})),
            "vmatrix_info": extract_vmatrix(character_info.get("get_character_vmatrix_info", {})),
            "symbol_info": extract_symbols(character_info.get("get_character_symbol_info", {})),
            "hyper_stat_info": extract_hyper_stat(character_info.get("get_character_hyper_stat_info", {})),
            "pet_equipment_info": extract_pet_equipment(character_info.get("get_character_pet_equipment_info", {})),
            "hexamatrix_info": extract_hexamatrix(character_info.get("get_character_hexamatrix_info", {})),
            "hexamatrix_stat_info": extract_hexamatrix_stat(
                character_info.get("get_character_hexamatrix_stat_info", {})
            ),
            "other_stat_info": extract_other_stat(character_info.get("get_character_other_stat_info", {})),
        }

    except Exception as e:
        logger.error(f"정보 추출 중 오류 발생: {e!s}")
        raise
