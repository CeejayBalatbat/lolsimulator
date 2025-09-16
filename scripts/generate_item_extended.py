import json
from pathlib import Path

# =====================================================================
# CONFIG & PATHS
# =====================================================================
data_folder = Path(__file__).resolve().parent.parent / "data"
items_file = data_folder / "items_full.json"
banned_file = data_folder / "banned_items.json"
output_file = data_folder / "items_extended.json"

# =====================================================================
# LOAD FILES
# =====================================================================
with open(items_file, "r", encoding="utf-8") as f:
    items = json.load(f)  # <-- this is a list

if banned_file.exists():
    with open(banned_file, "r", encoding="utf-8") as f:
        banned_data = json.load(f)
    banned_items = set(banned_data.get("banned_items", []))
else:
    banned_items = set()

# =====================================================================
# PROCESS ITEMS
# =====================================================================
extended_items = []

for item in items:
    name = item.get("name")
    if not name or name in banned_items:
        continue

    item_id = item.get("image", {}).get("full", "").replace(".png", "")
    tags = item.get("tags", [])

    extended_items.append({
        "id": item_id,
        "name": name,
        "tags": tags,       # preserve Riot’s tags
        "classes": [],      # champion classes this item is recommended for
        "passives": [],     # list of passive effect descriptions
        "actives": []       # list of active effect descriptions
    })

# =====================================================================
# SAVE OUTPUT
# =====================================================================
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(extended_items, f, indent=4, ensure_ascii=False)

print(f"Generated {len(extended_items)} items → {output_file}")
