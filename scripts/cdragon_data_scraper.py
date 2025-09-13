# cdragon_data_scraper.py

import requests
import json
import os

# Load champion IDs from file
with open("data/champion_ids.json", "r", encoding="utf-8") as f:
    champions = json.load(f)

def fetch_champion_cdragon(champ_name: str, branch: str = "latest"):
    url = f"https://raw.communitydragon.org/{branch}/game/data/characters/{champ_name.lower()}/{champ_name.lower()}.bin.json"
    print(f"Fetching {champ_name} from CDragon...")
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Failed to fetch {champ_name}: {response.status_code}")
        return None
    return response.json()


if __name__ == "__main__":
    output_folder = "data/cdragon/raw"
    os.makedirs(output_folder, exist_ok=True)

    for champ in champions:
        data = fetch_champion_cdragon(champ)
        if data:
            filename = os.path.join(output_folder, f"{champ.lower()}_cdragon.json")
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"Saved {champ} data to {filename}")
