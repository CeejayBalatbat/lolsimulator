# /scripts/icon_scraper.py

import requests
import os
from pathlib import Path

# --------------------------
# CONFIG
# --------------------------
# Paths
script_dir = Path(__file__).resolve().parent
data_dir = script_dir.parent / "data"
version_file = data_dir / "version.txt"
champ_icon_dir = data_dir / "champion_icons"
item_icon_dir = data_dir / "item_icons"

# Make icon folders if they don't exist
champ_icon_dir.mkdir(parents=True, exist_ok=True)
item_icon_dir.mkdir(parents=True, exist_ok=True)

# --------------------------
# GET PATCH VERSION
# --------------------------
with open(version_file, "r", encoding="utf-8") as f:
    patch_version = f.read().strip()

print(f"Using patch version: {patch_version}")

# --------------------------
# DOWNLOAD DATA FROM DDRAGON
# --------------------------
# Champion data
champ_data_url = f"http://ddragon.leagueoflegends.com/cdn/{patch_version}/data/en_US/champion.json"
resp = requests.get(champ_data_url)
resp.raise_for_status()
champ_data = resp.json()["data"]

# Item data
item_data_url = f"http://ddragon.leagueoflegends.com/cdn/{patch_version}/data/en_US/item.json"
resp = requests.get(item_data_url)
resp.raise_for_status()
item_data = resp.json()["data"]

# --------------------------
# DOWNLOAD CHAMPION ICONS
# --------------------------
for champ_name, champ_info in champ_data.items():
    img_url = f"http://ddragon.leagueoflegends.com/cdn/{patch_version}/img/champion/{champ_info['image']['full']}"
    save_path = champ_icon_dir / champ_info['image']['full']
    
    if not save_path.exists():
        r = requests.get(img_url)
        with open(save_path, "wb") as f:
            f.write(r.content)
        print(f"Downloaded {champ_info['image']['full']}")
    else:
        print(f"Already exists: {champ_info['image']['full']}")

# --------------------------
# DOWNLOAD ITEM ICONS
# --------------------------
for item_id, item_info in item_data.items():
    img_url = f"http://ddragon.leagueoflegends.com/cdn/{patch_version}/img/item/{item_info['image']['full']}"
    save_path = item_icon_dir / item_info['image']['full']

    if not save_path.exists():
        r = requests.get(img_url)
        with open(save_path, "wb") as f:
            f.write(r.content)
        print(f"Downloaded {item_info['image']['full']}")
    else:
        print(f"Already exists: {item_info['image']['full']}")

print("All icons downloaded!")
