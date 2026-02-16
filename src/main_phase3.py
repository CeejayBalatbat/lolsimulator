from engine import Stats, DamageEngine
from ability import Ability, AbilityConfig, AbilityLevelData, ScalingRatio, StatType, DamageType
from events import EventType, CombatEvent
from pipeline import EventManager, CombatSystem

def run_phase_3_test():
    # 1. Setup Infrastructure
    event_manager = EventManager()
    damage_engine = DamageEngine()
    combat_system = CombatSystem(event_manager, damage_engine)

    # 2. Define a "Listener" (e.g., A Debug Logger or a Rune)
    def debug_logger(event: CombatEvent):
        if event.event_type == EventType.CAST_COMPLETE:
            print(f"[LOG] Spell Cast: {event.ability_name}")
        elif event.event_type == EventType.POST_MITIGATION_DAMAGE:
            print(f"[LOG] DMJ DEALT: {event.damage_result.post_mitigation_damage:.2f} "
                  f"({event.damage_result.mitigated_amount:.2f} mitigated)")

    event_manager.subscribe(EventType.CAST_COMPLETE, debug_logger)
    event_manager.subscribe(EventType.POST_MITIGATION_DAMAGE, debug_logger)

    # 3. Setup Entities (Ezreal & Dummy)
    attacker = Stats(base_attack_damage=100, ability_power=0)
    target = Stats(health=2000, armor=50) # 33% reduction

    # 4. Define Ability (Ezreal Q)
    q_config = AbilityConfig(
        name="Mystic Shot",
        damage_type=DamageType.PHYSICAL,
        tags={'spell', 'projectile', 'applies_on_hit'},
        ratios=[ScalingRatio(StatType.TOTAL_AD, 1.30)],
        level_data=[AbilityLevelData(base_damage=20, mana_cost=0, cooldown=0)]
    )
    ezreal_q = Ability(q_config, rank=1)

    # --- THE SIMULATION STEP ---
    print("--- Phase 3 Simulation Start ---")
    
    # A. Player presses Q
    # (In a real engine, we check cooldowns here)
    cast_event = CombatEvent(
        event_type=EventType.CAST_COMPLETE,
        timestamp=0.1,
        source=attacker,
        target=target,
        ability_name=q_config.name
    )
    event_manager.publish(cast_event)

    # B. The Ability generates a Damage Packet
    dmg_packet = ezreal_q.cast(attacker, target)

    # C. Projectile lands (The Hit)
    hit_event = CombatEvent(
        event_type=EventType.PRE_MITIGATION_HIT,
        timestamp=0.3, # 0.2s travel time
        source=attacker,
        target=target,
        ability_name=q_config.name,
        damage_instance=dmg_packet,
        tags=q_config.tags
    )
    
    # D. System resolves the hit
    combat_system.resolve_hit(hit_event)

if __name__ == "__main__":
    run_phase_3_test()