import streamlit as st
import pandas as pd
import json
from pathlib import Path
from simulator import compute_stats  # backend handles stats calculation
from PIL import Image


# =====================================================================
# CONFIG SECTION
# =====================================================================
data_folder = Path(__file__).resolve().parent.parent / "data"

# =====================================================================
# PATH CONFIGURATION
# =====================================================================
champ_icon_dir = data_folder / "champion_icons"
item_icon_dir = data_folder / "item_icons"

# Ensure folders exist
champ_icon_dir.mkdir(parents=True, exist_ok=True)
item_icon_dir.mkdir(parents=True, exist_ok=True)

# =====================================================================
# LOAD BANNED_ITEMS DATA
# =====================================================================

def load_banned_items(path=data_folder / "banned_items.json"):
    """Load banned items list from JSON file in the data folder."""
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("banned_items", [])

BANNED_ITEMS = load_banned_items()

# =====================================================================
# LOAD DATA
# =====================================================================
# Champions
with open(data_folder / "champions_full.json", "r", encoding="utf-8") as f:
    champions = json.load(f)

champ_df = pd.DataFrame(champions)
champion_list = sorted([champ["name"] for champ in champions], key=lambda x: x.lower())

# Items
with open(data_folder / "items_full.json", "r", encoding="utf-8") as f:
    items = json.load(f)

all_items = []
for item in items:
    if item.get("name") not in BANNED_ITEMS:  # uses JSON now
        item_id = item.get("image", {}).get("full", "").replace(".png", "")
        all_items.append({
            "id": item_id,
            "name": item.get("name"),
            "depth": item.get("depth", 0)
        })

# =====================================================================
# STREAMLIT UI START
# =====================================================================
st.set_page_config(page_title="LoL Build Simulator", layout="wide")
st.title("⚔️ League of Legends Build Simulator")

# =====================================================================
# SIDEBAR: CHAMPION SELECTION
# =====================================================================
st.sidebar.header("Champion Selection")
selected_champion = st.sidebar.selectbox("Choose your champion", champion_list)

# Champion level slider
champ_level = st.sidebar.slider(
    "Select Champion Level",
    min_value=1,
    max_value=18,
    value=1,  # default starting level
    step=1
)

# =====================================================================
# SIDEBAR: ITEM SELECTION
# =====================================================================
st.sidebar.header("Item Build")

selected_items = []
num_slots = 6
for slot in range(num_slots):
    available_items = [
        it["name"]
        for it in all_items
        if not (it["depth"] == 3 and it["name"] in selected_items)  # no duplicate legendaries
    ]

    choice = st.sidebar.selectbox(
        f"Item Slot {slot+1}",
        ["None"] + available_items,
        key=f"item_slot_{slot}"
    )

    if choice != "None":
        selected_items.append(choice)

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
# MAIN PANEL: SIMULATION OUTPUT
# =====================================================================
st.subheader("Simulation Results")

# Champion
champ_icon_path = champ_icon_dir / f"{selected_champion}.png"  # or the exact file name if needed
st.write("**Champion:**")
col1, col2 = st.columns([1, 4])
with col1:
    if champ_icon_path.exists():
        st.image(str(champ_icon_path), width=64)
    st.write(selected_champion)  # name under icon
with col2:
    st.write("")  # optional: other info, or leave empty
    
# Items
st.write("**Items:**")

if selected_items:
    # Inject CSS to reduce space between columns
    st.markdown(
        """
        <style>
        .stColumns [class*="stColumn"] {
            padding-left: 2px;
            padding-right: 2px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    item_cols = st.columns(len(selected_items))
    for i, item_name in enumerate(selected_items):
        # Match item name to its icon file (numbers like 1001.png)
        file_name = next((it["image"]["full"] for it in items if it["name"] == item_name), None)
        if file_name:
            img_path = item_icon_dir / file_name
            with item_cols[i]:
                if img_path.exists():
                    st.image(str(img_path), width=48)
                st.write(item_name)
else:
    st.write("No items selected")


# Enemy
st.write(f"**Enemy:** {enemy_type} (HP: {enemy_hp}, Armor: {enemy_armor}, MR: {enemy_mr})")

# --- Compute stats ---
if selected_champion:
    stats = compute_stats(selected_champion, selected_items, level=champ_level)  # ✅ pass string, not dict

    st.subheader("Simulation Stats")

    # Define stat pairs for table layout
    stat_pairs = [
        ("AD", "AP"),
        ("Armor", "MR"),
        ("Attack Speed", "Ability Haste"),
        ("Crit Chance", "Move Speed"),
        ("HP Regen", "Resource Regen"),
        ("Armor Penetration", None),   # ✅ its own row
        ("Magic Penetration", None),   # ✅ its own row
        ("Lifesteal", "Omnivamp"),
        ("Range", "Tenacity"),
    ]


    # Add HP + dynamic resource
    champ_data = next((c for c in champions if c["name"] == selected_champion), None)
    resource_type = stats.get("resource_type", "None")

    if resource_type and resource_type.lower() != "none":
        stat_pairs.append(("HP", resource_type))
    else:
        stat_pairs.append(("HP", None))

    # Build table rows
    rows = []
    for left, right in stat_pairs:
        left_key = left.lower().replace(" ", "_")
        right_key = right.lower().replace(" ", "_") if right else None

        # Handle Magic Penetration
        if left == "Magic Penetration" or right == "Magic Penetration":
            flat = stats.get("flat_magic_pen", 0)
            percent = stats.get("percent_magic_pen", 0)
            value = f"{flat}|{percent:.0%}"
            if left == "Magic Penetration":
                rows.append([f"{left}: {value}", f"{right}: {stats.get(right.lower().replace(' ', '_'), '')}" if right else ""])
            else:
                rows.append([f"{left}: {stats.get(left_key, '')}", f"{right}: {value}"])
            continue

        # Handle Armor Penetration + Lethality
        # Handle Armor Penetration
        if left == "Armor Penetration" or right == "Armor Penetration":
            flat = stats.get("flat_armor_pen", 0)
            percent = stats.get("percent_armor_pen", 0)
            value = f"{flat}|{percent:.0%}"
            if left == "Armor Penetration":
                rows.append([
                    f"{left}: {value}",
                    f"{right}: {stats.get(right.lower().replace(' ', '_'), '')}" if right else ""
                ])
            else:
                rows.append([
                    f"{left}: {stats.get(left_key, '')}",
                    f"{right}: {value}"
                ])
            continue






        left_val = stats.get(left_key, 0)
        right_val = stats.get(right_key, "") if right_key else ""

        if left_key == "attack_speed":
            left_val = round(left_val, 3)
        if right_key == "attack_speed" and right_val != "":
            right_val = round(right_val, 3)

        rows.append([
            f"{left}: {left_val}",
            f"{right}: {right_val}" if right else ""
        ])



    # Render as a table
    st.table(rows)
    st.write([f"Magic Penetration: {stats['flat_magic_pen']}|{stats['percent_magic_pen']:.0%}", ""])
    st.write([f"Armor Penetration: {stats['flat_armor_pen']}|{stats['percent_armor_pen']:.0%}", ""])


# =====================================================================
# TABS: START OF TABS
# =====================================================================


tab1, tab2, tab3 = st.tabs(["Overview", "Skill Tooltips", "Item Damage"])

with tab1:
    st.subheader("Fight Overview")


with tab2:
    st.subheader("Skill Tooltips")
    st.write("Damage values, ratios, cooldowns, etc.")

with tab3:
    st.subheader("Item Damage")
    st.write("Damage breakdown from items like Spear of Shojin, Liandry's, Teemo shrooms, etc.")