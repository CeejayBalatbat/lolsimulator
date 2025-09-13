# scripts/data_scraper.py
import requests
import json
from pathlib import Path

# =========================
# CONFIG
# =========================
data_folder = Path(__file__).parent.parent / "data"  # points to /LoLSimulator/data/
data_folder.mkdir(parents=True, exist_ok=True)

# Get the latest version dynamically from DDragon
versions_url = "https://ddragon.leagueoflegends.com/api/versions.json"
version = requests.get(versions_url).json()[0]
print(f"Using latest League of Legends version: {version}\n")

# =========================
# FETCH ITEMS (Summoner's Rift only)
# =========================
item_url = f"https://ddragon.leagueoflegends.com/cdn/{version}/data/en_US/item.json"
print("Fetching items...")
response = requests.get(item_url)
item_data = response.json()["data"]

items_list = []
for idx, (item_id, item) in enumerate(item_data.items(), start=1):
    # Only include items available on Summoner's Rift (map ID 11)
    if item.get("maps", {}).get("11", False):
        print(f"Processing item {idx}/{len(item_data)}: {item.get('name')}")
        items_list.append(item)

with open(data_folder / "items_full.json", "w", encoding="utf-8") as f:
    json.dump(items_list, f, ensure_ascii=False, indent=2)
print(f"Saved {len(items_list)} Summoner's Rift items to {data_folder / 'items_full.json'}\n")

# =========================
# FETCH CHAMPIONS (FULL)
# =========================
champ_url = f"https://ddragon.leagueoflegends.com/cdn/{version}/data/en_US/championFull.json"
print("Fetching full champion data...")
champ_data = requests.get(champ_url).json()["data"]

champions_list = []
for idx, (champ_name, champ) in enumerate(champ_data.items(), start=1):
    spell_names = [s.get("name") for s in champ.get("spells", [])]
    passive_name = champ.get("passive", {}).get("name", "None")
    print(f"Processing champion {idx}/{len(champ_data)}: {champ_name} | Spells: {spell_names} | Passive: {passive_name}")
    champions_list.append(champ)

with open(data_folder / "champions_full.json", "w", encoding="utf-8") as f:
    json.dump(champions_list, f, ensure_ascii=False, indent=2)
print(f"Saved {len(champions_list)} champions to {data_folder / 'champions_full.json'}\n")

# =========================
# FETCH RUNES
# =========================
runes_url = f"https://ddragon.leagueoflegends.com/cdn/{version}/data/en_US/runesReforged.json"
print("Fetching runes...")
runes_data = requests.get(runes_url).json()

runes_list = []
for idx, rune_tree in enumerate(runes_data, start=1):
    print(f"Processing rune tree {idx}/{len(runes_data)}: {rune_tree.get('name')}")
    runes_list.append(rune_tree)

with open(data_folder / "runes_full.json", "w", encoding="utf-8") as f:
    json.dump(runes_list, f, ensure_ascii=False, indent=2)
print(f"Saved {len(runes_list)} rune trees to {data_folder / 'runes_full.json'}\n")

# =========================
# FETCH SUMMONER SPELLS
# =========================
summoner_url = f"https://ddragon.leagueoflegends.com/cdn/{version}/data/en_US/summoner.json"
print("Fetching summoner spells...")
summoner_data = requests.get(summoner_url).json()["data"]

summoners_list = []
for idx, (spell_name, spell) in enumerate(summoner_data.items(), start=1):
    print(f"Processing summoner spell {idx}/{len(summoner_data)}: {spell.get('name')}")
    summoners_list.append(spell)

with open(data_folder / "summoners_full.json", "w", encoding="utf-8") as f:
    json.dump(summoners_list, f, ensure_ascii=False, indent=2)
print(f"Saved {len(summoners_list)} summoner spells to {data_folder / 'summoners_full.json'}")
