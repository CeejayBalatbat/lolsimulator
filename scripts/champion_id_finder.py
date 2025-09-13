# scripts/champion_id_finder.py
import json
from pathlib import Path

# =========================
# CONFIG
# =========================
data_folder = Path(__file__).parent.parent / "data"  # points to /LoLSimulator/data/
champions_full_file = data_folder / "champions_full.json"
champion_ids_file = data_folder / "champion_ids.json"

# =========================
# LOAD FULL CHAMPION DATA
# =========================
with open(champions_full_file, "r", encoding="utf-8") as f:
    champions = json.load(f)

# Extract lowercase champion IDs
champion_ids = [champ.get("id").lower() for champ in champions if "id" in champ]

# =========================
# SAVE TO champion_ids.json
# =========================
with open(champion_ids_file, "w", encoding="utf-8") as f:
    json.dump(champion_ids, f, ensure_ascii=False, indent=2)

print(f"Saved {len(champion_ids)} champion IDs to {champion_ids_file}")
