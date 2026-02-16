from engine import Stats, StatType, DamageType, ProcType
from ability import Ability, AbilityConfig, AbilityLevelData, ScalingRatio
from item import ItemConfig, StatModifier, StatModType
from scenario import Scenario
from optimizer import Optimizer

def run_phase_8_test():
    # 1. Scenario: 10s Burst Window against a standard dummy
    dummy = Stats(base_hp=3000, current_health=3000, base_armor=40)
    scenario = Scenario(
        name="Ezreal Early Game",
        duration=10.0,
        attacker_level=1,
        target_stats=dummy
    )

    # 2. Ezreal (High Base AD)
    ezreal_base = Stats(
        base_ad=60.0, 
        base_attack_speed=0.625
    )
    
    # Q: 4.5s CD, 20 Base, 1.3 Total AD
    q_config = AbilityConfig(
        name="Mystic Shot",
        damage_type=DamageType.PHYSICAL,
        # Scalings: 130% Total AD
        ratios=[ScalingRatio(StatType.AD, 1.3)], 
        level_data=[AbilityLevelData(base_damage=20, mana_cost=30, cooldown=4.5)], 
        proc_type=ProcType.SPELL | ProcType.ON_HIT
    )
    abilities = [Ability(q_config, rank=1)]

    # 3. Items Definitions
    
    # Sheen (700g, No Stats, Spellblade Passive)
    sheen = ItemConfig(
        name="Sheen",
        cost=700,
        modifiers=[],
        passive_names=["passive_sheen"]
    )

    # Long Sword (350g, 10 AD)
    long_sword = ItemConfig(
        name="Long Sword",
        cost=350,
        modifiers=[StatModifier(StatType.AD, 10.0, StatModType.FLAT)]
    )
    
    # BF Sword (1300g, 40 AD)
    bf_sword = ItemConfig(
        name="B.F. Sword",
        cost=1300,
        modifiers=[StatModifier(StatType.AD, 40.0, StatModType.FLAT)]
    )

    # 4. Builds to Compare
    builds = [
        ("Naked", []),
        ("Sheen (700g)", [sheen]),
        ("2x Long Sword (700g)", [long_sword, long_sword]),
        ("B.F. Sword (1300g)", [bf_sword])
    ]

    # 5. Run Optimizer
    opt = Optimizer(scenario, ezreal_base, abilities)
    opt.compare_builds(builds)

if __name__ == "__main__":
    run_phase_8_test()