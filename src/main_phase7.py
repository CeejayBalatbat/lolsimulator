# src/main_phase7.py
from engine import Stats, DamageEngine
from ability import Ability, AbilityConfig, AbilityLevelData, ScalingRatio, StatType, DamageType, ProcType
from events import EventType
from pipeline import EventManager, CombatSystem
from simulation import TimeEngine

def run_phase_7_test():
    # 1. Setup
    bus = EventManager()
    engine = DamageEngine()
    combat = CombatSystem(bus, engine)

    # 2. Stats (Ezreal with Ionian Boots)
    attacker = Stats(
        base_ad=100.0,
        base_attack_speed=0.625,
        bonus_attack_speed=0.5, # +50% AS
        ability_haste=20.0      # ~16% CDR
    )
    
    target = Stats(base_hp=5000, current_health=5000, base_armor=50)

    # 3. Ability (Mystic Shot)
    # CD: 4.0s Base
    q_config = AbilityConfig(
        name="Mystic Shot",
        damage_type=DamageType.PHYSICAL,
        ratios=[ScalingRatio(StatType.TOTAL_AD, 1.3)],
        level_data=[AbilityLevelData(base_damage=120, mana_cost=30, cooldown=4.0)],
        proc_type=ProcType.SPELL | ProcType.ON_HIT
    )
    ezreal_q = Ability(q_config, rank=1)

    # 4. Run Simulation
    sim = TimeEngine(bus, attacker, target)
    sim.run([ezreal_q])

if __name__ == "__main__":
    run_phase_7_test()