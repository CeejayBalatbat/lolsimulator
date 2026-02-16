# main_phase2.py
from engine import Stats, DamageEngine
from ability import Ability, AbilityConfig, AbilityLevelData, ScalingRatio, StatType, StatSource, DamageType

def run_phase_2_test():
    # 1. Define Ezreal Q (The "Data")
    ezreal_q_config = AbilityConfig(
        name="Mystic Shot",
        damage_type=DamageType.PHYSICAL,
        tags={'spell', 'projectile', 'applies_on_hit'}, # Tags for later phases
        ratios=[
            ScalingRatio(StatType.TOTAL_AD, 1.30),
            ScalingRatio(StatType.AP, 0.15)
        ],
        level_data=[
            AbilityLevelData(base_damage=20, mana_cost=28, cooldown=5.5), # Rank 1
            AbilityLevelData(base_damage=45, mana_cost=31, cooldown=5.25),
            AbilityLevelData(base_damage=70, mana_cost=34, cooldown=5.0),
            AbilityLevelData(base_damage=95, mana_cost=37, cooldown=4.75),
            AbilityLevelData(base_damage=120, mana_cost=40, cooldown=4.5), # Rank 5
        ]
    )

    # 2. Setup The Simulation Context
    attacker = Stats(
        base_attack_damage=60, # Base AD
        flat_attack_damage=40, # Bonus AD (Items) -> Total 100
        ability_power=50,      # Some AP
        lethality=10
    )
    
    target = Stats(
        health=2000,
        armor=50 # 33% reduction
    )
    
    engine = DamageEngine()

    # 3. Run the Test (Rank 5 Q)
    q_ability = Ability(ezreal_q_config, rank=5)
    
    print(f"--- Casting {q_ability.config.name} (Rank {q_ability.rank}) ---")
    
    # Step A: Ability Logic (The "Cast")
    # This calculates RAW damage: Base 120 + (100 * 1.3) + (50 * 0.15) = 120 + 130 + 7.5 = 257.5
    damage_instance = q_ability.cast(attacker, target)
    
    print(f"Raw Damage Calculated: {damage_instance.raw_damage}")
    
    # Step B: Engine Logic (The "Mitigation")
    # Armor 50 -> Effective 40 (due to 10 Lethality)
    # Multiplier = 100/140 = ~0.714
    # Expected: 257.5 * 0.714 = ~183.9
    final_result = engine.calculate_damage(damage_instance, target)
    
    print(final_result)

if __name__ == "__main__":
    run_phase_2_test()