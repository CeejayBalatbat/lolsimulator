# scripts/backend_updater.py

import json
import subprocess
from pathlib import Path
import requests

# =========================
# CONFIG
# =========================
DATA_FOLDER = Path(__file__).parent.parent / "data"
VERSION_FILE = DATA_FOLDER / "current_patch.json"

# =========================
# GET LATEST PATCH VERSION
# =========================
def fetch_latest_patch(region="en_US"):
    url = "https://ddragon.leagueoflegends.com/api/versions.json"
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch patch versions: {response.status_code}")
    versions = response.json()
    return versions[0]  # latest version is first in the list

# =========================
# LOAD CURRENT VERSION
# =========================
def load_current_version():
    if VERSION_FILE.exists():
        with open(VERSION_FILE, "r", encoding="utf-8") as f:
            return json.load(f).get("version")
    return None

# =========================
# SAVE CURRENT VERSION
# =========================
def save_current_version(version):
    VERSION_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(VERSION_FILE, "w", encoding="utf-8") as f:
        json.dump({"version": version}, f, ensure_ascii=False, indent=2)

# =========================
# RUN A SCRIPT
# =========================
def run_script(script_name):
    print(f"▶ Running {script_name}...")
    subprocess.run(["python", script_name], check=True)

# =========================
# MAIN UPDATER
# =========================
def main():
    latest_patch = fetch_latest_patch()
    current_patch = load_current_version()

    print(f"Current patch: {current_patch}")
    print(f"Latest patch: {latest_patch}")

    if current_patch == latest_patch:
        print("✅ Data is up-to-date. No updates needed.")
        return

    print("⚡ New patch detected! Updating data...")

    # Run all scrapers in order
    scripts_folder = Path(__file__).parent
    run_script(scripts_folder / "data_scraper.py")
    run_script(scripts_folder / "champion_stats_puller.py")
    run_script(scripts_folder / "champion_id_finder.py")
    run_script(scripts_folder / "cdragon_data_scraper.py")
    run_script(scripts_folder / "cdragon_parser.py")  
    run_script(scripts_folder / "master_champion_spells.py")
    run_script(scripts_folder / "icon_scraper.py")

    # Save the latest patch
    save_current_version(latest_patch)
    print("🎉 Backend update complete!")

if __name__ == "__main__":
    main()
