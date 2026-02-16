from engine import Stats, StatType, DamageType, ProcType, DamageEngine
from item import ItemConfig, StatModifier, StatModType
from buffs import BuffConfig, BuffManager
from events import EventType, CombatEvent
from pipeline import EventManager, CombatSystem
from simulation import TimeEngine
from ability import Ability # Assuming dummy ability for now

# Define the Buff
rage_buff = BuffConfig(
    name="Rage",
    duration=3.0,
    max_stacks=5,
    modifiers=[StatModifier(StatType.AS, 0.10, StatModType.FLAT)], # +10% AS per stack
    refresh_on_stack=True
)

class RagePassive:
    def __init__(self, buff_config):
        self.config = buff_config
        self.engine_ref = None # Will grab reference to simulation

    def register(self, bus: EventManager, engine_ref: TimeEngine):
        self.engine_ref = engine_ref
        bus.subscribe(EventType.ATTACK_LAUNCH, self._on_attack)

    def _on_attack(self, event: CombatEvent):
        # Apply buff to the engine's buff manager
        self.engine_ref.buff_manager.apply_buff(self.config, event.timestamp)

def run_phase_9_test():
    # 1. Setup Infrastructure
    bus = EventManager()
    damage_engine = DamageEngine() # Create Math Core
    
    # CRITICAL MISSING LINE:
    # Connect the Combat System to the Event Bus so hits are processed!
    combat_system = CombatSystem(bus, damage_engine) 

    # 2. Setup Entities
    base_ezreal = Stats(base_ad=100, base_attack_speed=0.625)
    target = Stats(base_hp=2000, current_health=2000, base_armor=0) # 0 Armor for raw damage check
    
    # 3. Setup Simulation
    sim = TimeEngine(bus, base_ezreal, target, items=[])
    
    # 4. Run
    # We pass an empty ability list, so he will just Auto Attack
    sim.run(abilities=[])

if __name__ == "__main__":
    run_phase_9_test()