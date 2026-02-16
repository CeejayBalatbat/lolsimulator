from engine import ProcType, Stats, DamageType, DamageInstance
from events import EventType, CombatEvent, Priority
from pipeline import EventManager
from buffs import BuffConfig

class OnHitDamagePassive:
    """
    Adds flat damage to attacks (e.g., Recurve Bow, Nashor's Tooth).
    """
    def __init__(self, amount: float, damage_type: DamageType):
        self.amount = amount
        self.damage_type = damage_type

    def register(self, event_manager: EventManager):
        event_manager.subscribe(EventType.PRE_MITIGATION_HIT, self._on_hit, Priority.HIGH)

    def _on_hit(self, event: CombatEvent):
        # 1. Check if this instance triggers On-Hit effects
        if not (event.base_instance.proc_type & ProcType.ON_HIT):
            return

        # 2. Check Coefficient (e.g. Kata R reduces on-hit effectiveness)
        eff = event.base_instance.proc_coefficient
        if eff <= 0: return

        # 3. Create the Extra Damage Instance
        final_amt = self.amount * eff
        
        extra = DamageInstance(
            raw_damage=final_amt,
            damage_type=self.damage_type,
            source_stats=event.source,
            proc_type=ProcType.NONE, # Don't chain proc infinite loops
            tags={'passive_proc', 'on_hit'}
        )
        
        # 4. Attach to the Event
        event.add_instance(extra)


class SpellbladePassive:
    def __init__(self, damage_percent_base_ad: float):
        self.ratio = damage_percent_base_ad
        self.active = False
        self.cooldown = 1.5
        self.last_proc_time = -999.0 

    def register(self, event_manager: EventManager):
        event_manager.subscribe(EventType.CAST_COMPLETE, self._on_cast)
        event_manager.subscribe(EventType.PRE_MITIGATION_HIT, self._on_hit, Priority.HIGH)

    def _on_cast(self, event: CombatEvent):
        # Charge the blade only if it is off cooldown
        if event.timestamp >= self.last_proc_time + self.cooldown:
            self.active = True

    def _on_hit(self, event: CombatEvent):
        if not self.active:
            return
            
        # Standard Spellblade internal CD check (safety)
        if event.timestamp < self.last_proc_time + self.cooldown:
            return

        if not (event.base_instance.proc_type & ProcType.ON_HIT):
            return

        # Use the base_ad from the snapshot source stats
        bonus_dmg = event.source.base_ad * self.ratio
        event.base_instance.raw_damage += bonus_dmg
        
        self.active = False
        self.last_proc_time = event.timestamp


class GrantBuffOnHitPassive:
    """
    Applies a buff when you hit a target.
    (Trinity Force 'Quicken', Black Cleaver 'Carve', Phantom Dancer)
    """
    def __init__(self, buff_config: BuffConfig):
        self.buff_config = buff_config
        self.bus = None # Will store reference to event manager

    def register(self, event_manager: EventManager):
        self.bus = event_manager
        event_manager.subscribe(EventType.PRE_MITIGATION_HIT, self._on_hit)

    def _on_hit(self, event: CombatEvent):
        # 1. Filter: Triggers on Basic Attacks
        if not (event.base_instance.proc_type & ProcType.BASIC_ATTACK):
            return

        # 2. Fire Buff Request Event
        # We publish a new event asking the Engine to apply a buff
        buff_event = CombatEvent(
            event_type=EventType.BUFF_APPLY,
            timestamp=event.timestamp,
            source=event.source,
            target=event.target,
            buff_config=self.buff_config
        )
        self.bus.publish(buff_event)