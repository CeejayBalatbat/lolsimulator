import requests
import json
import os

class DataDragon:
    def __init__(self):
        # 1. Create Data Directory
        if not os.path.exists("data"):
            os.makedirs("data")
            
        # 2. Get Latest Patch Version
        # We fetch this every time to ensure we are current.
        # In production, you'd cache this to avoid API spam.
        try:
            print("--- CONNECTING TO RIOT API ---")
            version_url = "https://ddragon.leagueoflegends.com/api/versions.json"
            self.version = requests.get(version_url).json()[0]
            print(f"Detected Patch: {self.version}")
        except Exception as e:
            print(f"CRITICAL: Could not fetch version. {e}")
            # Fallback for offline dev if you have the file
            self.version = "14.3.1" 

        self.base_url = f"https://ddragon.leagueoflegends.com/cdn/{self.version}/data/en_US"

    def fetch_items(self):
        print("Downloading Item Database...")
        url = f"{self.base_url}/item.json"
        
        try:
            response = requests.get(url)
            response.raise_for_status() # Crash early if 404/500
            data = response.json()
            
            # Save raw JSON for debugging (Trust me, you will need this)
            with open("data/items_raw.json", "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
                
            return data['data']
        except Exception as e:
            print(f"Error fetching items: {e}")
            return {}

    def fetch_champion(self, name: str):
        print(f"Downloading {name}...")
        url = f"{self.base_url}/champion/{name}.json"
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            
            with open(f"data/{name}_raw.json", "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
                
            return data['data'][name]
        except Exception as e:
            print(f"Error fetching champion {name}: {e}")
            return {}