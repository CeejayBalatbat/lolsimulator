from scraper import DataDragon
from loader import ItemLoader
from engine import StatType
from passives import GrantBuffOnHitPassive

def run_ingestion_test():
    print("=== TESTING DATA INGESTION ===")
    
    # 1. Fetch
    dd = DataDragon()
    raw_items = dd.fetch_items()
    
    if not raw_items:
        print("❌ FAILED: Could not download items.")
        return

    # 2. Parse
    print(f"Parsing {len(raw_items)} raw entries...")
    library = ItemLoader.load_all(raw_items)
    print(f"Successfully loaded {len(library)} playable Rift items.")
    
    # 3. Inspect Trinity Force
    target_item = "Trinity Force"
    
    if target_item in library:
        tf = library[target_item]
        print(f"\n=== {tf.name.upper()} ===")
        print(f"Cost: {tf.cost}g")
        
        # Check Base Stats
        print("Stats:")
        found_ah = False
        found_ms = False
        
        for mod in tf.modifiers:
            stat_name = mod.stat.name 
            print(f" - {stat_name}: {mod.value}")
            
            if mod.stat == StatType.AH: found_ah = True
            if mod.stat == StatType.MS: found_ms = True

        # Check Passives (SMARTER DISPLAY)
        print("Passives:")
        if tf.passives:
            for p in tf.passives:
                # If it's a Buff Passive, print the Buff Name (e.g. "Quicken")
                if hasattr(p, 'buff_config'):
                    print(f" - {p.__class__.__name__} ({p.buff_config.name})")
                    
                    # LOGIC FIX: If this buff gives Speed, we found our missing stats!
                    for mod in p.buff_config.modifiers:
                        if mod.stat == StatType.MS:
                            found_ms = True
                            print(f"   (Found Move Speed in {p.buff_config.name})")
                else:
                    print(f" - {p.__class__.__name__}")
        else:
            print(" - None")
            
        print("\n[VERIFICATION RESULT]")
        if found_ah and found_ms and tf.passives:
            print("✅ SUCCESS: Trinity Force has Haste, Speed (via Quicken), and Spellblade.")
        else:
            print("⚠️ WARNING: Trinity Force is missing data!")
            if not found_ah: print("   - Missing Ability Haste")
            if not found_ms: print("   - Missing Move Speed (Base or Passive)")
            if not tf.passives: print("   - Missing Passive Object")
            
    else:
        print(f"❌ FAILED: Could not find {target_item}.")

if __name__ == "__main__":
    run_ingestion_test()