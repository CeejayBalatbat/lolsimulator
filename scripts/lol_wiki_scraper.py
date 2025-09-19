# scripts/lol_wiki_scraper.py

import requests
from pathlib import Path

# ============================================================
# CONFIG
# ============================================================
BASE_URL = "https://leagueoflegends.fandom.com/wiki/"
SAVE_DIR = Path(__file__).resolve().parent.parent / "data" / "lolwiki"
RAW_DIR = SAVE_DIR / "raw"
PROCESSED_DIR = SAVE_DIR / "processed"

RAW_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# These are the known Lua modules on the wiki
MODULES = {
    "items": "Module:ItemData/data",
}

# ============================================================
# HELPER: fetch module raw lua
# ============================================================
def fetch_module(name: str, module: str) -> Path | None:
    """Fetch a Lua module and save it under raw/ folder."""
    url = f"{BASE_URL}{module}?action=raw"
    save_path = RAW_DIR / f"{name}.lua"

    print(f"Fetching {name} from {url} ...")
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"❌ Failed to fetch {name}: {e}")
        return None

    save_path.write_text(resp.text, encoding="utf-8")
    print(f"✅ Saved {name} → {save_path}")
    return save_path

# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    print("=== League Wiki Scraper ===")
    fetched = {}

    for name, module in MODULES.items():
        path = fetch_module(name, module)
        if path:
            fetched[name] = path

    print("\nFetched modules:")
    for name, path in fetched.items():
        print(f" - {name}: {path}")
