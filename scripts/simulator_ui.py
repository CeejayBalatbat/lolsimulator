# scripts/simulator_ui.py

import streamlit as st
import pandas as pd
import json
from pathlib import Path
from simulator import compute_stats
from PIL import Image


# =====================================================================
# CACHE IMAGES
# =====================================================================
@st.cache_data
def load_item_image(path):
    """Load a PIL image from disk and cache it in memory."""
    return Image.open(path)

@st.cache_data
def filter_items(all_items, query):
    if not query:
        return all_items
    query = query.lower()
    return [item for item in all_items if query in item["name"].lower()]

# =====================================================================
# CONFIG & DATA PATHS
# =====================================================================
data_folder = Path(__file__).resolve().parent.parent / "data"
champ_icon_dir = data_folder / "champion_icons"
item_icon_dir = data_folder / "item_icons"

champ_icon_dir.mkdir(parents=True, exist_ok=True)
item_icon_dir.mkdir(parents=True, exist_ok=True)

# Load banned items
def load_banned_items(path=data_folder / "banned_items.json"):
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("banned_items", [])

BANNED_ITEMS = load_banned_items()

# =====================================================================
# LOAD CHAMPIONS & ITEMS
# =====================================================================
with open(data_folder / "champions_full.json", "r", encoding="utf-8") as f:
    champions = json.load(f)

champ_df = pd.DataFrame(champions)
champion_list = sorted([champ["name"] for champ in champions], key=lambda x: x.lower())

with open(data_folder / "items_full.json", "r", encoding="utf-8") as f:
    items = json.load(f)

all_items = []
for item in items:
    item_id = item.get("image", {}).get("full", "").replace(".png", "")
    # ✅ Ban check now uses ID instead of name
    if item_id not in BANNED_ITEMS:
        all_items.append({
            "id": item_id,
            "name": item.get("name"),
            "depth": item.get("depth", 0),
            "tags": item.get("tags", []),
            "image": item.get("image", {}),
        })


# =====================================================================
# STREAMLIT CONFIG
# =====================================================================
st.set_page_config(page_title="LoL Build Simulator", layout="wide")
st.title("⚔️ League of Legends Build Simulator")

# =====================================================================
# SIDEBAR: CHAMPION SELECTION
# =====================================================================
st.sidebar.header("Champion Selection")
selected_champion = st.sidebar.selectbox("Choose your champion", champion_list)

champ_level = st.sidebar.slider(
    "Select Champion Level",
    min_value=1,
    max_value=18,
    value=1,
    step=1
)

# =====================================================================
# SIDEBAR: ENEMY ARCHETYPE
# =====================================================================
st.sidebar.header("Enemy Archetype")
archetypes = {
    "Squishy": {"hp": 1200, "armor": 30, "mr": 30},
    "Bruiser": {"hp": 2000, "armor": 80, "mr": 60},
    "Tank": {"hp": 3000, "armor": 150, "mr": 120},
    "Custom": {}
}

enemy_type = st.sidebar.selectbox("Enemy Type", list(archetypes.keys()))

enemy_hp = archetypes.get(enemy_type, {}).get("hp", 2000)
enemy_armor = archetypes.get(enemy_type, {}).get("armor", 80)
enemy_mr = archetypes.get(enemy_type, {}).get("mr", 60)

if enemy_type == "Custom":
    enemy_hp = st.sidebar.number_input("Enemy HP", min_value=500, max_value=10000, step=500, value=2000)
    enemy_armor = st.sidebar.number_input("Enemy Armor", min_value=0, max_value=500, step=10, value=80)
    enemy_mr = st.sidebar.number_input("Enemy MR", min_value=0, max_value=500, step=10, value=60)
else:
    st.sidebar.text(f"HP: {enemy_hp}")
    st.sidebar.text(f"Armor: {enemy_armor}")
    st.sidebar.text(f"MR: {enemy_mr}")

# =====================================================================
# SIDEBAR: ITEM SELECTION WITH POPOVER (OPTIMIZED)
# =====================================================================
st.sidebar.header("Item Build (Popover Version)")
num_slots = 6
if "selected_items" not in st.session_state:
    st.session_state.selected_items = [None] * num_slots

# Create mapping of item_id -> item data
items_by_id = {item["id"]: item for item in all_items}

# Cached filtering function
@st.cache_data
def filter_items(items, query):
    query = query.lower()
    return [item for item in items if query in item["name"].lower()]

# Track how many rows to show per slot (lazy load)
if "rows_to_show" not in st.session_state:
    st.session_state.rows_to_show = [3] * num_slots  # start with 3 rows per slot

for i in range(num_slots):
    # Current slot label
    current_item_name = (
        items_by_id[st.session_state.selected_items[i]]["name"]
        if st.session_state.selected_items[i] else "None"
    )
    slot_label = f"Slot {i+1}: {current_item_name}"

    with st.sidebar.popover(slot_label):
        st.write(f"Select item for Slot {i+1}")

        # Search bar inside popover
        search_query = st.text_input(f"Search items (Slot {i+1})", key=f"search_{i}")
        filtered_items = filter_items(all_items, search_query)

        # Lazy rendering
        cols_per_row = 6
        max_rows_to_show = st.session_state.rows_to_show[i]
        total_rows = (len(filtered_items) + cols_per_row - 1) // cols_per_row
        rows_to_show = min(total_rows, max_rows_to_show)

        for row in range(rows_to_show):
            cols = st.columns(cols_per_row)
            for col in range(cols_per_row):
                idx = row * cols_per_row + col
                if idx < len(filtered_items):
                    item = filtered_items[idx]
                    img_file = item_icon_dir / f"{item['id']}.png"
                    with cols[col]:
                        if img_file.exists():
                            st.image(load_item_image(img_file), width=48)
                        display_name = (
                            item["name"][:14] + "..." if len(item["name"]) > 16 else item["name"]
                        )
                        if st.button(display_name, key=f"btn_{i}_{item['id']}"):
                            st.session_state.selected_items[i] = item["id"]

        # "Load more" button
        if total_rows > max_rows_to_show:
            if st.button(f"Load more items (Slot {i+1})", key=f"load_more_{i}"):
                st.session_state.rows_to_show[i] += 3  # show 3 more rows next rerun


# =====================================================================
# MAIN PANEL: SIMULATION OUTPUT
# =====================================================================
st.write("**Items:**")
selected_ids = [it for it in st.session_state.selected_items if it]

if selected_ids:
    item_cols = st.columns(len(selected_ids))
    for col, it in zip(item_cols, selected_ids):
        with col:
            img_file = item_icon_dir / f"{it}.png"
            if img_file.exists():
                st.image(str(img_file), width=48)
            else:
                st.write(items_by_id[it]["name"])  # fallback to name if icon missing
else:
    st.write("No items selected.")



# Enemy display
st.write(f"**Enemy:** {enemy_type} (HP: {enemy_hp}, Armor: {enemy_armor}, MR: {enemy_mr})")

# =====================================================================
# COMPUTE STATS
# =====================================================================
if selected_champion:
    stats = compute_stats(selected_champion, [it for it in st.session_state.selected_items if it], level=champ_level)

    st.subheader("Simulation Stats")

    stat_pairs = [
        ("AD", "AP"),
        ("Armor", "MR"),
        ("Attack Speed", "Ability Haste"),
        ("Crit Chance", "Move Speed"),
        ("HP Regen", "Resource Regen"),
        ("Armor Penetration", None),
        ("Magic Penetration", None),
        ("Lifesteal", "Omnivamp"),
        ("Range", "Tenacity"),
    ]

    # Add HP + resource dynamically
    resource_type = stats.get("resource_type", "None")
    if resource_type.lower() != "none":
        stat_pairs.append(("HP", resource_type))
    else:
        stat_pairs.append(("HP", None))

    rows = []
    for left, right in stat_pairs:
        left_key = left.lower().replace(" ", "_")
        right_key = right.lower().replace(" ", "_") if right else None

        # Magic Pen
        if left == "Magic Penetration" or right == "Magic Penetration":
            flat = stats.get("flat_magic_pen", 0)
            percent = stats.get("percent_magic_pen", 0)
            value = f"{flat}|{percent:.0%}"
            if left == "Magic Penetration":
                rows.append([f"{left}: {value}", ""])
            else:
                rows.append(["", f"{right}: {value}"])
            continue

        # Armor Pen
        if left == "Armor Penetration" or right == "Armor Penetration":
            flat = stats.get("flat_armor_pen", 0)
            percent = stats.get("percent_armor_pen", 0)
            value = f"{flat}|{percent:.0%}"
            if left == "Armor Penetration":
                rows.append([f"{left}: {value}", ""])
            else:
                rows.append(["", f"{right}: {value}"])
            continue

        left_val = stats.get(left_key, 0)
        right_val = stats.get(right_key, "") if right_key else ""
        if left_key == "attack_speed":
            left_val = round(left_val, 3)
        if right_key == "attack_speed" and right_val != "":
            right_val = round(right_val, 3)

        rows.append([f"{left}: {left_val}", f"{right}: {right_val}" if right else ""])

    st.table(rows)

# =====================================================================
# TABS (Overview, Skill Tooltips, Item Damage)
# =====================================================================
tab1, tab2, tab3 = st.tabs(["Overview", "Skill Tooltips", "Item Damage"])

with tab1:
    st.subheader("Fight Overview")

with tab2:
    st.subheader("Skill Tooltips")
    st.write("Damage values, ratios, cooldowns, etc.")

with tab3:
    st.subheader("Item Damage")
    st.write("Damage breakdown from items.")

# =====================================================================
# CLEAR BUTTON
# =====================================================================
if st.button("Clear All Items"):
    st.session_state.selected_items = [None] * num_slots