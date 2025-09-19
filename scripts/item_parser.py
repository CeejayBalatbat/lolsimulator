# scripts/parse_items.py
import json
import re
import html as html_lib
from pathlib import Path

# -------------------------
# Config / paths
# -------------------------
ROOT = Path(__file__).resolve().parent.parent
DATA_FOLDER = ROOT / "data"
INPUT_FILE = DATA_FOLDER / "items_full.json"
OUTPUT_FILE = DATA_FOLDER / "items_parsed.json"

# -------------------------
# Stat mapping (keep only mapped keys)
# -------------------------
STAT_MAP = {
    "FlatHPPoolMod": "health",
    "FlatMPPoolMod": "mana",
    "FlatArmorMod": "armor",
    "FlatSpellBlockMod": "magic_resist",
    "FlatPhysicalDamageMod": "attack_damage",
    "FlatMagicDamageMod": "ability_power",
    "FlatMovementSpeedMod": "move_speed",
    "PercentMovementSpeedMod": "move_speed_pct",
    "PercentAttackSpeedMod": "attack_speed_pct",
    "FlatCritChanceMod": "crit_chance",
    "FlatHPRegenMod": "hp_regen",
    "FlatMPRegenMod": "mp_regen",
}

# keywords to map numbers parsed from <stats> block
STAT_KEYWORDS = {
    "health": "health",
    "hp": "health",
    "mana": "mana",
    "attack damage": "attack_damage",
    "ad": "attack_damage",
    "ability power": "ability_power",
    "ap": "ability_power",
    "ability haste": "ability_haste",
    "crit": "crit_chance",
    "critical": "crit_chance",
    "attack speed": "attack_speed",
    "attack-speed": "attack_speed",
    "life steal": "lifesteal",
    "lifesteal": "lifesteal",
    "omnivamp": "omnivamp",
    "movement speed": "move_speed",
    "armor": "armor",
    "magic resist": "magic_resist",
    "magic pen": "magic_pen",  # optional
}

# -------------------------
# Patterns
# -------------------------
# Capture <passive>Name</passive>   then optional <br/> etc then description until next passive/active/mainText or end
PASSIVE_PATTERN = re.compile(
    r"<passive>(.*?)</passive>\s*(?:<br\s*/?>\s*)*(.*?)(?=(?:<passive>|<active>|</mainText>|$))",
    re.IGNORECASE | re.DOTALL,
)
ACTIVE_PATTERN = re.compile(
    r"<active>(.*?)</active>\s*(?:<br\s*/?>\s*)*(.*?)(?=(?:<passive>|<active>|</mainText>|$))",
    re.IGNORECASE | re.DOTALL,
)

# Grab the <stats> ... </stats> block to extract numbers inside it (e.g. "15 Ability Haste")
STATS_BLOCK = re.compile(r"<stats>(.*?)</stats>", re.IGNORECASE | re.DOTALL)

# a generic matcher for "number + stat name" inside a stats block
NUM_STAT_RE = re.compile(r"(\d+(?:\.\d+)?%?)\s*([A-Za-z \-]+?)(?:<br>|$|\n|,)", re.IGNORECASE)

# -------------------------
# Helpers
# -------------------------
def clean_html_keep_text(s: str) -> str:
    """Turn <br> into newline, remove tags but keep inner text, unescape entities, trim."""
    if not s:
        return ""
    # convert <br> to newline
    s = re.sub(r"<br\s*/?>", "\n", s, flags=re.IGNORECASE)
    # remove tags but keep inner text
    s = re.sub(r"</?[^>]+>", "", s)
    # collapse whitespace
    s = html_lib.unescape(s)
    return " ".join(s.split()).strip()

def parse_stats_block(desc: str) -> dict:
    """Extract numbers from the <stats> block (if any) and map them to keys."""
    stats = {}
    m = STATS_BLOCK.search(desc)
    if not m:
        return stats
    block = m.group(1)
    # remove tags inside block but keep text to simplify
    block_text = re.sub(r"</?[^>]+>", " ", block)
    # find tokens like "15 Ability Haste" or "25% Critical Strike Chance"
    for num_str, label in NUM_STAT_RE.findall(block_text + "<br>"):
        label = label.strip().lower()
        # convert to numeric; percentages -> fraction
        if num_str.endswith("%"):
            try:
                val = float(num_str.strip("%")) / 100.0
            except ValueError:
                val = num_str
        else:
            try:
                # prefer int when possible
                if "." in num_str:
                    val = float(num_str)
                else:
                    val = int(num_str)
            except ValueError:
                val = num_str
        # map label to our stat key using STAT_KEYWORDS
        matched = None
        for k, v in STAT_KEYWORDS.items():
            if k in label:
                matched = v
                break
        if matched:
            stats[matched] = val
    return stats

def get_item_id(item: dict) -> str:
    # prefer explicit id field, else use image.full, else empty string
    if "id" in item and item["id"]:
        return str(item["id"])
    img = item.get("image", {})
    full = img.get("full", "")
    if full:
        return full.replace(".png", "")
    return ""

# -------------------------
# Main parse function
# -------------------------
def parse_item(item: dict) -> dict:
    item_id = get_item_id(item)
    name = item.get("name", "")
    tags = item.get("tags", []) or []

    # map Riot's numeric stats (FlatHPPoolMod etc.) -> readable keys, drop original keys
    stats = {}
    for k, v in (item.get("stats") or {}).items():
        mapped = STAT_MAP.get(k)
        if mapped:
            stats[mapped] = v
        # else: drop raw keys to avoid duplicates; keep only mapped

    # also parse the <stats> block inside description (Ability Haste, AP listed there)
    desc = item.get("description", "") or ""
    parsed_from_desc = parse_stats_block(desc)
    # desc-derived stats should override if present
    stats.update(parsed_from_desc)

    # parse passives and actives: capture both name and following description
    passives = []
    for m in PASSIVE_PATTERN.finditer(desc):
        name_raw = m.group(1) or ""
        desc_raw = m.group(2) or ""
        passives.append({
            "name": clean_html_keep_text(name_raw),
            "description": clean_html_keep_text(desc_raw),
        })

    actives = []
    for m in ACTIVE_PATTERN.finditer(desc):
        name_raw = m.group(1) or ""
        desc_raw = m.group(2) or ""
        actives.append({
            "name": clean_html_keep_text(name_raw),
            "description": clean_html_keep_text(desc_raw),
        })

    return {
        "id": item_id,
        "name": name,
        "tags": tags,
        "stats": stats,
        "passives": passives,
        "actives": actives,
    }

# -------------------------
# Load input (supports list or dict/data)
# -------------------------
def load_items(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    # handle common variants:
    # - raw is a list of items (your earlier file)
    # - raw is dict with "data" where values are item dicts
    # - raw is dict mapping id->item
    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict):
        if "data" in raw and isinstance(raw["data"], dict):
            return list(raw["data"].values())
        # otherwise maybe it's id->item map
        # check if values are dict and contain 'name'
        values = list(raw.values())
        if values and isinstance(values[0], dict) and "name" in values[0]:
            return values
    # fallback: return empty
    return []

def main():
    items = load_items(INPUT_FILE)
    parsed = []
    for item in items:
        parsed_item = parse_item(item)
        parsed.append(parsed_item)

    # save
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(parsed, f, indent=2, ensure_ascii=False)

    print(f"✅ Parsed {len(parsed)} items → {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
