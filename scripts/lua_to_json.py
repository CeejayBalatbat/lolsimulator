import json
import re
from pathlib import Path
from slpp import slpp as lua

# =====================================================================
# CONFIG
# =====================================================================
data_folder = Path(__file__).resolve().parent.parent / "data" / "lolwiki"
raw_items_file = data_folder / "raw" / "items.lua"
processed_items_file = data_folder / "processed" / "items.json"

processed_items_file.parent.mkdir(parents=True, exist_ok=True)

# =====================================================================
# HELPERS
# =====================================================================
import re

def clean_description(text: str) -> str:
    """Convert wiki markup in descriptions into simulator-friendly text."""
    if not isinstance(text, str):
        return text

    # Replace tooltip templates like {{tt|700 units|center to edge}} -> "700 units"
    text = re.sub(r"\{\{tt\|([^|}]+)\|[^}]+\}\}", r"\1", text)

    # Replace alt-stat templates like {{as|reducing MR by 30%|magic penetration}} -> "reducing MR by 30%"
    text = re.sub(r"\{\{as\|([^|}]+)\|[^}]+\}\}", r"\1", text)

    # Replace gold template {{g|100}} -> "100"
    text = re.sub(r"\{\{g\|([^}]+)\}\}", r"\1", text)

    # Replace scaling template {{pp|100;200;300|-7+x;0+|...}} -> "100;200;300"
    text = re.sub(r"\{\{pp\|([^|}]+).*?\}\}", r"\1", text)

    # Remove bold/italic wiki markup
    text = text.replace("'''", "").replace("''", "")

    # Collapse multiple spaces or leftover punctuation
    text = re.sub(r"\s+,", ",", text)
    text = re.sub(r"\s{2,}", " ", text).strip()

    return text


def normalize_numbers(text: str) -> str:
    # Example: "30%" → "0.3"
    def perc_to_float(match):
        num = match.group(1)
        try:
            return str(float(num) / 100.0)
        except ValueError:
            return match.group(0)

    return re.sub(r"(\d+(?:\.\d+)?)%", perc_to_float, text)


# =====================================================================
# MAIN CONVERSION
# =====================================================================
print("=== League Wiki Lua → JSON Converter ===")

with open(raw_items_file, "r", encoding="utf-8") as f:
    raw_text = f.read()

# Remove leading 'return' to parse as Lua
raw_text = raw_text.replace("return", "", 1).strip()

# Parse Lua into Python dict
items_data = lua.decode(raw_text)

processed = {}

for item_name, item_data in items_data.items():
    item_id = str(item_data.get("id", ""))
    stats = item_data.get("stats", {})
    effects = item_data.get("effects", {})

    # Clean descriptions inside effects
    clean_effects = {}
    for eff_key, eff_value in effects.items():
        if isinstance(eff_value, dict):
            clean_effects[eff_key] = {
                "name": eff_value.get("name"),
                "unique": eff_value.get("unique", False),
                "description": normalize_numbers(clean_description(eff_value.get("description", "")))
            }
        else:
            clean_effects[eff_key] = normalize_numbers(clean_description(str(eff_value)))

    processed[item_name] = {
        "id": item_id,
        "tier": item_data.get("tier"),
        "type": item_data.get("type", []),
        "stats": stats,
        "effects": clean_effects,
        "recipe": item_data.get("recipe", []),
        "buy": item_data.get("buy"),
    }

# Save JSON
with open(processed_items_file, "w", encoding="utf-8") as f:
    json.dump(processed, f, indent=4, ensure_ascii=False)

print(f"✅ Processed {len(processed)} items → {processed_items_file}")
