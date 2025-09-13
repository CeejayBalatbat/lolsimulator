# scripts/backend_updater.py
import json
import os
import subprocess
from pathlib import Path
import requests

# Paths
scripts_folder = Path(__file__).parent
data_folder = scripts_folder.parent / "data"
version_file = data_folder / "version.txt"

# Ensure data folder exists
data_folder.mkdir(parents=True, exist_ok=True)

# =========================
# Check latest version from DDragon
# =========================
versions_url = "https://ddragon.leagueoflegends.com/api/versions.json"
latest_version = requests.get(versions_url).json()[0]
print(f"Latest LoL version: {latest_version}")

# Read saved version
if version_file.exists():
    saved_version = version_file.read_text().strip()
else:
    saved_version = None

if saved_version == latest_version:
    print(f"No update needed. Current version {saved_version} is up-to-date.")
else:
    print(f"New version detected! {saved_version} → {latest_version}\n")
    
    # Save new version
    version_file.write_text(latest_version)
    
    # =========================
    # Run data scrapper
    # =========================
    print("Running data_scrapper.py...")
    subprocess.run(["python", scripts_folder / "data_scrapper.py"])
    
    # =========================
    # Generate champion IDs
    # =========================
    print("Running champion_id_finder.py...")
    subprocess.run(["python", scripts_folder / "champion_id_finder.py"])
    
    # =========================
    # Pull champion stats
    # =========================
    print("Running champion_stats_puller.py...")
    subprocess.run(["python", scripts_folder / "champion_stats_puller.py"])
    
    # =========================
    # Fetch CDragon raw champion files
    # =========================
    print("Running cdragon_data_scrapper.py...")
    subprocess.run(["python", scripts_folder / "cdragon_data_scrapper.py"])
    
    # =========================
    # Process CDragon spells
    # =========================
    print("Running cdragon_parser.py...")
    subprocess.run(["python", scripts_folder / "cdragon_parser.py"])
    
    # =========================
    # Merge into master champion spells
    # =========================
    print("Running master_champion_spells.py...")
    subprocess.run(["python", scripts_folder / "master_champion_spells.py"])
    
    print("\n✅ Backend update complete!")
