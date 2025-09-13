# scripts/champion_stats_puller.py
import json
from pathlib import Path

# =========================
# CONFIG
# =========================
data_folder = Path(__file__).parent.parent / "data"  # points to /LoLSimulator/data/
champions_full_file = data_folder / "champions_full.json"
champion_stats_file = data_folder / "champion_stats.json"

# =========================
# LOAD FULL CHAMPION DATA
# =========================
with open(champions_full_file, "r", encoding="utf-8") as f:
    champions_full = json.load(f)

champion_stats = {}

for champ in champions_full:
    name = champ.get("id")  # e.g., "Aatrox"
    stats = champ.get("stats", {})

    # Only pick the stats we care about for calculations
    champion_stats[name] = {
        "hp": stats.get("hp"),
        "hpperlevel": stats.get("hpperlevel"),
        "mp": stats.get("mp"),
        "mpperlevel": stats.get("mpperlevel"),
        "movespeed": stats.get("movespeed"),
        "armor": stats.get("armor"),
        "armorperlevel": stats.get("armorperlevel"),
        "spellblock": stats.get("spellblock"),
        "spellblockperlevel": stats.get("spellblockperlevel"),
        "attackrange": stats.get("attackrange"),
        "hpregen": stats.get("hpregen"),
        "hpregenperlevel": stats.get("hpregenperlevel"),
        "mpregen": stats.get("mpregen"),
        "mpregenperlevel": stats.get("mpregenperlevel"),
        "crit": stats.get("crit"),
        "critperlevel": stats.get("critperlevel"),
        "attackdamage": stats.get("attackdamage"),
        "attackdamageperlevel": stats.get("attackdamageperlevel"),
        "attackspeed": stats.get("attackspeed"),
        "attackspeedperlevel": stats.get("attackspeedperlevel")
    }

# =========================
# SAVE TO champion_stats.json
# =========================
with open(champion_stats_file, "w", encoding="utf-8") as f:
    json.dump(champion_stats, f, ensure_ascii=False, indent=2)

print(f"Saved stats for {len(champion_stats)} champions to {champion_stats_file}")
