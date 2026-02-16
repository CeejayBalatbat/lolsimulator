from engine import Stats, DamageEngine, DamageInstance, DamageType, ProcType
from events import EventType, CombatEvent, Priority
from pipeline import EventManager, CombatSystem
from passives import OnHitDamagePassive
from inventory_system import InventoryManager 
from item import ItemConfig

def run_phase_6_test():
    # 1. Setup Infrastructure
    bus = EventManager()
    engine = DamageEngine()
    combat = CombatSystem(bus, engine)
    inventory = InventoryManager(bus)
    
    # 2. Setup Attacker (Katarina)
    attacker = Stats(base_ad=100.0)
    
    # 3. Register "BotRK" Passive manually for this test
    # (Simulating equipping the item)
    print(">> Registering BotRK Passive (40 Physical Damage)")
    bork_passive = OnHitDamagePassive(amount=40.0, damage_type=DamageType.PHYSICAL)
    bork_passive.register(bus)

    # 4. Define "Death Lotus" (Katarina R) Instance
    # - Base Damage: 10
    # - Type: Magic
    # - Proc: On-Hit Enabled (25% effectiveness)
    kata_r_instance = DamageInstance(
        raw_damage=10.0,
        damage_type=DamageType.MAGIC,
        source_stats=attacker,
        proc_type=ProcType.SPELL | ProcType.ON_HIT, # Hybrid Flag
        proc_coefficient=0.25, # 25% On-Hit Eff
        tags={'spell'}
    )

    # 5. Define Target
    # High Armor (reduces BotRK), Low MR (weak to Kat R)
    target_stats = Stats(
        base_hp=1000.0,
        current_health=1000.0, # <--- IMPORTANT: Initialize Current HP
        base_armor=100.0,      # 50% Phys Reduction
        base_mr=0.0            # 0% Magic Reduction
    )
    
    print("\n--- Phase 6: The 'Katarina' Hybrid Damage Test ---")
    print(f"   Target Stats: Armor={target_stats.base_armor}, MR={target_stats.base_mr}")

    # 6. Fire Event
    hit_event = CombatEvent(
        event_type=EventType.PRE_MITIGATION_HIT,
        timestamp=1.0,
        source=attacker,
        target=target_stats,
        base_instance=kata_r_instance
    )
    
    bus.publish(hit_event)

    # --- EXPECTED OUTPUT EXPLANATION ---
    # 1. Base Damage (Magic):
    #    10 Raw -> 0 MR -> 10.0 Final
    #
    # 2. BotRK Passive (Physical):
    #    40 Raw * 0.25 (Eff) = 10.0 Adjusted Raw
    #    10.0 Raw -> 100 Armor (50% red) -> 5.0 Final
    #
    # Total HP Loss: 15.0
    
    print("\n[VERIFICATION]")
    print(f"Final Target HP: {target_stats.current_health:.1f} / {target_stats.base_hp:.1f}")

if __name__ == "__main__":
    run_phase_6_test()