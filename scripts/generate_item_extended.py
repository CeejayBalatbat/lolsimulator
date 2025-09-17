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
    items = json.load(f)  # <-- list of items

if banned_file.exists():
    with open(banned_file, "r", encoding="utf-8") as f:
        banned_data = json.load(f)
    banned_items = set(str(x) for x in banned_data.get("banned_items", []))
else:
    banned_items = set()

# Load existing extended file if available
if output_file.exists():
    with open(output_file, "r", encoding="utf-8") as f:
        old_extended = {item["id"]: item for item in json.load(f)}
else:
    old_extended = {}

# =====================================================================
# PROCESS ITEMS
# =====================================================================
extended_items = []

for item in items:  # items is a list
    # Grab ID from the image filename ("6676.png" → "6676")
    item_id = str(item.get("image", {}).get("full", "").replace(".png", ""))
    if not item_id or item_id in banned_items:
        continue

    name = item.get("name")
    if not name:
        continue

    tags = item.get("tags", [])

    # Keep user-defined data from old_extended if available
    old_data = old_extended.get(item_id, {})

    extended_items.append({
        "id": item_id,
        "name": name,
        "tags": tags,                          # update tags from Riot
        "classes": old_data.get("classes", []),
        "passives": old_data.get("passives", []),
        "actives": old_data.get("actives", [])
    })

# =====================================================================
# SAVE OUTPUT
# =====================================================================
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(extended_items, f, indent=4, ensure_ascii=False)

print(f"Generated {len(extended_items)} items → {output_file}")
