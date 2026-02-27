from collections import defaultdict
from engine import DamageInstance, DamageResult
from events import EventType, CombatEvent, Priority

class EventManager:
    def __init__(self):
        self.listeners = defaultdict(list) 

    def subscribe(self, event_type: EventType, listener, priority: Priority = Priority.NORMAL):
        self.listeners[event_type].append((priority, listener))
        self.listeners[event_type].sort(key=lambda x: x[0])

    def publish(self, event: CombatEvent):
        if event.event_type in self.listeners:
            for _, listener in self.listeners[event.event_type]:
                listener(event)

class DamageEngine:
    def calculate(self, instance: DamageInstance, target_stats) -> DamageResult:
        raw = instance.raw_damage
        
        # 🟢 NEW: Pull the attacker's stats that were packed into the damage instance!
        attacker = instance.source_stats 
        
        # Determine mitigation based on damage type
        if instance.damage_type.name == "PHYSICAL":
            # 1. Start with the target's current armor (Black Cleaver shred is already applied here)
            armor = target_stats.base_armor 
            
            # 2. Apply Percent Armor Penetration (e.g., LDR's 30%)
            armor = armor * (1.0 - attacker.armor_pen_percent)
            
            # 3. Apply Flat Lethality
            armor = armor - attacker.lethality
            
            # 4. Calculate Final Mitigation (Armor cannot be reduced below 0 by Lethality)
            armor = max(0.0, armor) 
            mitigation = 100.0 / (100.0 + armor)
            final = raw * mitigation
            
        elif instance.damage_type.name == "MAGIC":
            mr = max(0.0, target_stats.base_mr)
            # You can add Magic Pen math here later using the exact same logic!
            mitigation = 100.0 / (100.0 + mr)
            final = raw * mitigation
            
        else:
            final = raw # True damage
            
        return DamageResult(instance.damage_type, raw, final)

class CombatSystem:
    def __init__(self, bus: EventManager, damage_engine: DamageEngine):
        self.bus = bus
        self.damage_engine = damage_engine
        
        # MANDATORY: We must listen for hits to process them
        self.bus.subscribe(EventType.PRE_MITIGATION_HIT, self._handle_hit, Priority.LOWEST)

    def _handle_hit(self, event: CombatEvent):
        """Calculates final damage for every instance in the event."""
        total_post_mitigation = 0
        total_pre_mitigation = 0
        
        # Process every instance (Base attack + On-hits)
        for instance in event.all_instances:
            res = self.damage_engine.calculate(instance, event.target)
            total_pre_mitigation += res.pre_mitigation_damage
            total_post_mitigation += res.post_mitigation_damage
        
        # Store the final result in the event so the Simulation can see it
        event.damage_result = DamageResult(
            event.base_instance.damage_type,
            total_pre_mitigation,
            total_post_mitigation
        )
        
        # Publish that damage has officially been dealt
        post_event = CombatEvent(
            event_type=EventType.POST_MITIGATION_DAMAGE,
            timestamp=event.timestamp,
            source=event.source,
            target=event.target,
            base_instance=event.base_instance,
            damage_result=event.damage_result,
            ability_name=event.ability_name
        )
        self.bus.publish(post_event)