from engine import Stats
from item import Item, ItemConfig, StatModifier, StatModType
from stat_pipeline import StatPipeline

def run_phase_4_test():
    # 1. Define Items
    long_sword = ItemConfig(
        name="Long Sword",
        cost=350,
        modifiers=[
            StatModifier('flat_attack_damage', 10.0, StatModType.FLAT)
        ]
    )
    
    rabadon = ItemConfig(
        name="Rabadon's Deathcap",
        cost=3600,
        modifiers=[
            StatModifier('ability_power', 120.0, StatModType.FLAT),
            StatModifier('ability_power', 0.35, StatModType.MULTIPLIER) # +35% Total AP
        ]
    )
    
    amp_tome = ItemConfig(
        name="Amplifying Tome",
        cost=400,
        modifiers=[
            StatModifier('ability_power', 20.0, StatModType.FLAT)
        ]
    )

    # 2. Define Base Champion (Ezreal Level 1)
    base_ezreal = Stats(
        base_attack_damage=60.0,
        ability_power=0.0,
        health=500.0
    )

    # 3. Create Inventory
    inventory = [
        Item(long_sword),
        Item(rabadon),
        Item(amp_tome)
    ]

    print("--- Phase 4: Stat Pipeline Test ---")
    print(f"Base AP: {base_ezreal.ability_power}")

    # 4. Resolve Stats
    final_stats = StatPipeline.resolve(base_ezreal, inventory)

    print(f"Final AP: {final_stats.ability_power}")
    
    # Verification:
    # Flat AP = 120 (Rab) + 20 (Amp) = 140
    # Multiplier = 1.35 (Rab Passive)
    # Total = 140 * 1.35 = 189
    
    expected = 140 * 1.35
    print(f"Expected: {expected}")
    
    if abs(final_stats.ability_power - expected) < 0.1:
        print(">> SUCCESS: Deathcap math works.")
    else:
        print(">> FAILURE: Math is wrong.")

    print(f"Final AD: {final_stats.attack_damage}") 
    # Should be 60 (Base) + 10 (Long Sword) = 70

if __name__ == "__main__":
    run_phase_4_test()