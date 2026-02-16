from engine import Stats, DamageEngine, StatType
from events import EventType, CombatEvent, Priority
from pipeline import EventManager, CombatSystem
from item import ItemConfig
from inventory_system import InventoryManager
from ability import Ability, AbilityConfig, ScalingRatio, StatType as StatEnum # Alias to avoid conflict

def run_phase_5_test():
    # 1. Setup Core Systems
    bus = EventManager()
    engine = DamageEngine()
    combat = CombatSystem(bus, engine) # Subscribes to HIT
    inventory = InventoryManager(bus)

    # 2. Setup Ezreal (Base AD 100)
    ezreal_stats = Stats(base_ad=100.0)

    # 3. Create Item: Sheen
    sheen_config = ItemConfig(
        name="Sheen",
        modifiers=[], # Sheen has no raw stats in this simplified version
        passive_names=["passive_sheen"]
    )

    # 4. Equip Item (This registers the listener!)
    inventory.equip_item(sheen_config)

    # 5. Simulation: Cast Q
    print("\n--- SIMULATION START ---")
    
    # Event: Cast Q
    # We use a mock event for the cast
    cast_event = CombatEvent(
        event_type=EventType.CAST_COMPLETE,
        timestamp=1.0,
        source=ezreal_stats,
        target=None # Target doesn't matter for cast
    )
    bus.publish(cast_event)

    # Event: Q Lands (The Hit)
    # Ezreal Q applies on-hit effects
    from engine import DamageInstance, DamageType
    
    # SNAPSHOT: usage of .snapshot() logic (manual here for demo)
    snapshot_stats = ezreal_stats.snapshot()
    
    q_damage = DamageInstance(
        raw_damage=120, # Base Q Dmg
        damage_type=DamageType.PHYSICAL,
        source_stats=snapshot_stats,
        tags={'applies_on_hit'}
    )

    hit_event = CombatEvent(
        event_type=EventType.PRE_MITIGATION_HIT,
        timestamp=1.2,
        source=snapshot_stats,
        target=Stats(base_hp=2000, base_armor=50),
        damage_instance=q_damage,
        tags={'applies_on_hit'}
    )
    
    print("Projectile Lands...")
    bus.publish(hit_event)

if __name__ == "__main__":
    run_phase_5_test()