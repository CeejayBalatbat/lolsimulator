# scripts/simulator.py

import json
from pathlib import Path

# =====================================================================
# LOAD DATA
# =====================================================================
data_folder = Path(__file__).resolve().parent.parent / "data"

with open(data_folder / "champions_full.json", "r", encoding="utf-8") as f:
    champions = json.load(f)

with open(data_folder / "items_full.json", "r", encoding="utf-8") as f:
    items = json.load(f)

# Missing stats for items (custom)
with open(data_folder / "special_item_stats.json", "r", encoding="utf-8") as f:
    special_item_stats = json.load(f)

# Convert items list into dict for quick lookup by name
items_by_name = {item["name"]: item for item in items}


# =====================================================================
# BACKEND HELPERS
# =====================================================================

def compute_stats(champion_name, item_names, level=1):
    """
    Compute final stats for a champion given selected items and level.
    Attack Speed uses Riot's non-linear growth formula.
    """
    champion = next((c for c in champions if c["name"] == champion_name), None)
    if not champion:
        return {}

    base_stats = champion.get("stats", {})

    # --- Base stats ---
    stats = {
        "ad": base_stats.get("attackdamage", 0) + base_stats.get("attackdamageperlevel", 0) * (level - 1),
        "ap": 0,
        "armor": base_stats.get("armor", 0) + base_stats.get("armorperlevel", 0) * (level - 1),
        "mr": base_stats.get("spellblock", 0) + base_stats.get("spellblockperlevel", 0) * (level - 1),
        "attack_speed": base_stats.get("attackspeed", 0),
        "ability_haste": 0,
        "crit_chance": base_stats.get("crit", 0) + base_stats.get("critperlevel", 0) * (level - 1),
        "move_speed": base_stats.get("movespeed", 0),
        "hp_regen": base_stats.get("hpregen", 0) + base_stats.get("hpregenperlevel", 0) * (level - 1),
        "resource": base_stats.get("mp", 0) + base_stats.get("mpperlevel", 0) * (level - 1),
        "resource_regen": base_stats.get("mpregen", 0) + base_stats.get("mpregenperlevel", 0) * (level - 1),
        "resource_type": champion.get("partype", "None"),
        "lethality": 0,       
        "flat_armor_pen": 0,
        "percent_armor_pen": 0,
        "flat_magic_pen": 0,      
        "percent_magic_pen": 0.0,
        "lifesteal": 0,
        "omnivamp": 0,
        "range": base_stats.get("attackrange", 0),
        "tenacity": 0,
        "hp": base_stats.get("hp", 0) + base_stats.get("hpperlevel", 0) * (level - 1),
    }

    # --- Attack Speed Calculation (Riot formula) ---
    base_as = base_stats.get("attackspeed", 0)
    ratio_as = base_stats.get("attackspeed", 0)  # usually same as base
    growth_percent = base_stats.get("attackspeedperlevel", 0) / 100  # convert 2.5 -> 0.025

    # Non-linear growth: bonus AS from level
    bonus_as = growth_percent * (0.7025 + 0.0175 * (level - 1)) * (level - 1)

    # Item bonus
    item_bonus_as = sum(
        items_by_name[item].get("stats", {}).get("PercentAttackSpeedMod", 0) / 100
        for item in item_names if item in items_by_name
    )

    total_bonus_as = bonus_as + item_bonus_as
    stats["attack_speed"] = base_as + (ratio_as * total_bonus_as)

    # --- Add item stats ---
    for item_name in item_names:
        item = items_by_name.get(item_name)
        if not item:
            continue
        item_stats = item.get("stats", {})

        stats["ad"] += item_stats.get("FlatPhysicalDamageMod", 0)
        stats["ap"] += item_stats.get("FlatMagicDamageMod", 0)
        stats["armor"] += item_stats.get("FlatArmorMod", 0)
        stats["mr"] += item_stats.get("FlatSpellBlockMod", 0)
        stats["attack_speed"] += item_stats.get("PercentAttackSpeedMod", 0) / 100 * ratio_as
        stats["ability_haste"] += item_stats.get("AbilityHaste", 0)
        stats["crit_chance"] += item_stats.get("FlatCritChanceMod", 0)
        stats["move_speed"] += item_stats.get("FlatMovementSpeedMod", 0)
        stats["hp_regen"] += item_stats.get("FlatHPRegenMod", 0)
        stats["resource_regen"] += item_stats.get("FlatMPRegenMod", 0)
        stats["lethality"] += item_stats.get("Lethality", 0)
        stats["flat_armor_pen"] += item_stats.get("FlatArmorPen", 0)
        stats["percent_armor_pen"] += item_stats.get("PercentArmorPen", 0)
        stats["flat_magic_pen"] += item_stats.get("FlatMagicPen", 0)
        stats["percent_magic_pen"] += item_stats.get("PercentMagicPen", 0)
        stats["lifesteal"] += item_stats.get("LifeSteal", 0)
        stats["omnivamp"] += item_stats.get("Omnivamp", 0)
        stats["tenacity"] += item_stats.get("Tenacity", 0)
        stats["hp"] += item_stats.get("FlatHPPoolMod", 0)

        # --- Apply special overrides from special_item_stats.json ---
        if item_name in special_item_stats:
            overrides = special_item_stats[item_name]
            for stat_key, value in overrides.items():
                stats[stat_key] += value

    return stats


def calculate_damage(champion_name, item_names, enemy_stats):
    """
    Placeholder backend function.
    champion_name: str
    item_names: list of str
    enemy_stats: dict with keys 'hp', 'armor', 'mr'
    Returns simulated damage (placeholder value for now)
    """
    # TODO: Replace with actual calculations
    total_damage = 1000  # dummy
    return {
        "total_damage": total_damage,
        "details": {
            "basic_attacks": 300,
            "abilities": 700
        }
    }
