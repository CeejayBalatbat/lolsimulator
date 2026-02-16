from scraper import DataDragon
from loader import ItemLoader
from engine import Stats, StatType, DamageType, ProcType
from ability import Ability, AbilityConfig, AbilityLevelData, ScalingRatio
from scenario import Scenario
from optimizer import Optimizer
from pipeline import EventManager

def run_phase_10_simulation():
    print("\n=== PHASE 10: THE REAL WORLD SIMULATION ===\n")
    
    # 1. DATA INGESTION
    # ---------------------------------------------
    dd = DataDragon()
    # Fetch raw data from Riot
    raw_items = dd.fetch_items()
    
    if not raw_items:
        print("CRITICAL ERROR: Could not download items.")
        return

    # Parse data (Automatic Regex + Manual Overrides)
    print("Parsing Item Database...")
    library = ItemLoader.load_all(raw_items)
    print(f"Successfully loaded {len(library)} items into the Engine.")

    # 2. SELECT ITEMS (The "Shopping List")
    # ---------------------------------------------
    # We grab items by their exact API names.
    try:
        triforce = library["Trinity Force"]
        infinity_edge = library["Infinity Edge"]
        botrk = library["Blade of The Ruined King"]
        kraken = library["Kraken Slayer"]
        
        # Debug: Confirm Trinity Force is the "Smart" version
        print(f"\n[DEBUG] Loaded {triforce.name}")
        has_ah = any(m.stat == StatType.AH for m in triforce.modifiers)
        print(f"   - Has Ability Haste? {'✅ YES' if has_ah else '❌ NO (Parser Failed)'}")
        print(f"   - Passives: {[p.__class__.__name__ for p in triforce.passives]}")
        
    except KeyError as e:
        print(f"\nCRITICAL ERROR: Could not find item {e}.")
        print("Check 'data/items_raw.json' to see the exact name used by Riot.")
        return

    # 3. SETUP SCENARIO (Mid-Game Spike)
    # ---------------------------------------------
    # Target: A Squishy ADC (Level 9)
    # HP: ~1200 Base + Items = ~1600
    # Armor: ~40 Base + Shards = ~50
    target_stats = Stats(
        base_hp=1600, 
        current_health=1600, 
        base_armor=50, 
        base_mr=38
    )
    
    scenario = Scenario(
        name="Ezreal Level 9 (Mid-Game All-In)",
        duration=10.0,
        attacker_level=9,
        target_stats=target_stats
    )

    # 4. SETUP CHAMPION (Ezreal Level 9)
    # ---------------------------------------------
    # Base Stats for Ezreal at Lvl 9
    ezreal_lvl9 = Stats(
        base_ad=62.0 + (3.0 * 9),   # Approx 89 Base AD
        base_attack_speed=0.625, 
        bonus_attack_speed=0.025 * 9 # ~22% Growth
    )

    # Ability: Mystic Shot (Q) - Rank 5
    # Cooldown: 4.5s (Base) - This will be reduced by Haste!
    # Damage: 120 (Base) + 130% AD
    q_config = AbilityConfig(
        name="Mystic Shot",
        damage_type=DamageType.PHYSICAL,
        ratios=[ScalingRatio(StatType.AD, 1.30)], 
        level_data=[AbilityLevelData(base_damage=120, mana_cost=30, cooldown=4.5)], 
        proc_type=ProcType.SPELL | ProcType.ON_HIT
    )
    
    # Ability: Essence Flux (W) - Rank 1
    # Cooldown: 12s
    w_config = AbilityConfig(
        name="Essence Flux",
        damage_type=DamageType.MAGIC,
        ratios=[ScalingRatio(StatType.AD, 0.60)], 
        level_data=[AbilityLevelData(base_damage=80, mana_cost=50, cooldown=12.0)],
        proc_type=ProcType.SPELL
    )
    
    # We give him Rank 5 Q and Rank 1 W
    abilities = [
        Ability(q_config, rank=1), # Our code uses index 0 for Rank 1? Wait, check logic.
        Ability(w_config, rank=1)  # Let's assume list size 1 means Rank 1 data is at index 0
    ]

    # 5. DEFINE BUILDS TO COMPARE
    # ---------------------------------------------
    builds = [
        # Build 1: The Meta (Trinity Force)
        ("Trinity Force", [triforce]),
        
        # Build 2: The Shredder (BotRK)
        ("BotRK", [botrk]),
        
        # Build 3: The Raw DPS (Kraken)
        ("Kraken Slayer", [kraken]),
        
        # Build 4: The Bait (Infinity Edge - No Crit Synergy yet)
        ("Infinity Edge", [infinity_edge])
    ]

    # 6. RUN OPTIMIZER
    # ---------------------------------------------
    opt = Optimizer(scenario, ezreal_lvl9, abilities)
    opt.compare_builds(builds)

if __name__ == "__main__":
    run_phase_10_simulation()