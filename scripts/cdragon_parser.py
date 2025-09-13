import json
import os

# Folders
INPUT_FOLDER = os.path.join("data", "cdragon", "raw")
OUTPUT_FOLDER = os.path.join("data", "cdragon", "processed")
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Load champion list
with open(os.path.join("data", "champion_ids.json"), "r", encoding="utf-8") as f:
    champion_ids = json.load(f)

def capitalize_champion(name: str) -> str:
    """Fix CDragon capitalization for champions."""
    special_cases = {
        "kha'zix": "KhaZix",
        "reksai": "RekSai",
        "missfortune": "MissFortune",
        "monkeyking": "MonkeyKing",
        "aurelionsol": "AurelionSol",
        "tahmkench": "TahmKench",
        "chogath": "Chogath",
        "belveth": "Belveth",
        "xinzhao": "XinZhao",
        "drmundo": "DrMundo",
        "jarvaniv": "JarvanIV",
        "kogmaw": "KogMaw",
        "ksante": "KSante",
        "leesin": "LeeSin",
        "masteryi": "MasterYi",
        "twistedfate": "TwistedFate"
    }
    return special_cases.get(name.lower(), name.capitalize())

for champ_name in champion_ids:
    input_file = os.path.join(INPUT_FOLDER, f"{champ_name}_cdragon.json")
    output_file = os.path.join(OUTPUT_FOLDER, f"{champ_name}_spells_processed.json")

    if not os.path.exists(input_file):
        print(f"⚠️ Missing CDragon file for {champ_name}: {input_file}")
        continue

    with open(input_file, "r", encoding="utf-8") as f:
        champ_data = json.load(f)

    champ_spells = {}
    proper_name = capitalize_champion(champ_name)

    for key, spell_data in champ_data.items():
        if key.startswith(f"Characters/{proper_name}/Spells/"):
            spell_name = key.split("/")[-1]
            mspell = spell_data.get("mSpell", {})
            if not mspell:
                continue

            calcs = mspell.get("mSpellCalculations", {})
            data_values_list = mspell.get("DataValues", [])
            data_values_dict = {dv.get("mName"): dv.get("mValues", dv) for dv in data_values_list}

            champ_spells[spell_name] = {
                "calculations": calcs,
                "dataValues": data_values_dict
            }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(champ_spells, f, ensure_ascii=False, indent=2)

    print(f"✅ Processed {champ_name} → {output_file.replace(os.sep, '/')}")

print("🎉 All champions processed.")
