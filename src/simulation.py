import heapq
from typing import List, Tuple
from copy import deepcopy

from engine import Stats, DamageInstance, DamageType, ProcType
from ability import Ability
from cooldowns import CooldownManager
from events import EventType, CombatEvent, Priority
from pipeline import EventManager
from item import ItemConfig

# Phase 9 Imports
from buffs import BuffManager
from stat_pipeline import StatPipeline

class TimeEngine:
    def __init__(self, bus: EventManager, base_attacker: Stats, target: Stats, items: List[ItemConfig]):
        self.bus = bus
        
        # --- DYNAMIC STAT ENGINE ---
        self.base_attacker = base_attacker   # Immutable (Naked Stats)
        self.items = items                   # Immutable (Inventory)
        
        self.buff_manager = BuffManager()    # Player Buffs (Trinity Force, Conqueror)
        self.attacker = StatPipeline.resolve(self.base_attacker, self.items, [])
        
        # --- TARGET STATE (Phase 12) ---
        self.base_target = target            # Immutable (Base Enemy)
        self.debuff_manager = BuffManager()  # Enemy Debuffs (Black Cleaver, Exhaust)
        self.target = target                 # Dynamic Enemy (Recalculated every tick)
        
        self.cd_manager = CooldownManager()
        
        # Simulation Parameters
        self.current_time = 0.0
        self.time_step = 0.033 
        self.max_duration = 10.0
        
        # State Tracking
        self.next_attack_time = 0.0
        self.total_damage_done = 0.0
        self.damage_history = []
        
        # Event Queue
        self.event_queue: List[Tuple[float, CombatEvent]] = []

        # Subscriptions
        self.bus.subscribe(EventType.POST_MITIGATION_DAMAGE, self._on_damage_dealt, Priority.NORMAL)
        self.bus.subscribe(EventType.BUFF_APPLY, self._on_buff_apply, Priority.HIGHEST)

    def _on_buff_apply(self, event: CombatEvent):
        if event.buff_config:
            # PHASE 12: Route buff to the correct manager based on who is the 'target' of the event
            # If the event target is the ENEMY, it's a Debuff.
            # If the event target is the PLAYER, it's a Self-Buff.
            
            # Simple identity check: 
            # In our sim, self.target is the Enemy. self.attacker is the Player.
            # Note: We compare against self.base_target or self.target to be safe.
            
            # For now, we assume if the buff source is Player and target is Enemy -> Debuff
            if event.target == self.target or event.target == self.base_target:
                 self.debuff_manager.apply_buff(event.buff_config, event.timestamp)
                 # print(f"[{event.timestamp:.2f}s] DEBUFF APPLIED: {event.buff_config.name}")
            else:
                 self.buff_manager.apply_buff(event.buff_config, event.timestamp)

    def schedule_event(self, event: CombatEvent):
        heapq.heappush(self.event_queue, (event.timestamp, event))

    def _on_damage_dealt(self, event: CombatEvent):
        if event.damage_result:
            dmg = event.damage_result.post_mitigation_damage
            self.total_damage_done += dmg
            
            # Log for UI
            self.damage_history.append({
                "Time": round(event.timestamp, 2),
                "Source": event.ability_name,
                "Type": event.base_instance.damage_type.name,
                "Damage": round(dmg, 1)
            })

    def run(self, abilities: list[Ability]):
        # print(f"--- STARTING SIMULATION ({self.max_duration}s) ---")
        
        while self.current_time < self.max_duration:
            # 1. Process Due Events
            while self.event_queue and self.event_queue[0][0] <= self.current_time:
                timestamp, event = heapq.heappop(self.event_queue)
                self.bus.publish(event)

            # 2. Check Global Cooldown
            if self.current_time < self.cd_manager.global_cooldown:
                self._tick()
                continue

            # 3. PRIORITY 1: Cast Abilities
            action_taken = False
            haste_mult = self.attacker.cooldown_reduction_multiplier
            
            for abil in abilities:
                if self.cd_manager.is_ready(abil.config.name, self.current_time):
                    self._perform_cast(abil, haste_mult)
                    action_taken = True
                    break 
            
            if action_taken:
                self._tick()
                continue

            # 4. PRIORITY 2: Auto Attack
            if self.current_time >= self.next_attack_time:
                self._perform_attack()
                action_taken = True

            # 5. Advance Time
            self._tick()

    def _tick(self):
        self.current_time += self.time_step
        
        # A. Update Timers
        self.buff_manager.tick(self.current_time)
        self.debuff_manager.tick(self.current_time)
        
        # B. Re-Resolve Player Stats
        self.attacker = StatPipeline.resolve(
            self.base_attacker, 
            self.items, 
            self.buff_manager.get_all_buffs()
        )
        
        # C. Re-Resolve Enemy Stats (Apply Armor Shred)
        self.target = StatPipeline.resolve_target(
            self.base_target,
            self.debuff_manager
        )

    def _perform_cast(self, ability: Ability, haste_mult: float):
        # print(f"[{self.current_time:.2f}s] CAST: {ability.config.name}")
        
        cast_time = 0.25 
        travel_time = 0.25
        
        cast_event = CombatEvent(
            event_type=EventType.CAST_COMPLETE,
            timestamp=self.current_time,
            source=self.attacker, 
            target=self.target, # Current dynamic target
            ability_name=ability.config.name,
            base_instance=None 
        )
        self.bus.publish(cast_event)

        snapshot_stats = self.attacker.snapshot()
        dmg_instance = ability.cast(snapshot_stats, self.target)
        
        hit_event = CombatEvent(
            event_type=EventType.PRE_MITIGATION_HIT,
            timestamp=self.current_time + travel_time, 
            source=snapshot_stats,
            target=self.target,
            base_instance=dmg_instance,
            ability_name=ability.config.name
        )
        self.schedule_event(hit_event)

        rank_data = ability.config.level_data[ability.rank - 1]
        self.cd_manager.put_on_cooldown(
            ability.config.name, 
            rank_data.cooldown, 
            haste_mult, 
            self.current_time
        )
        self.cd_manager.trigger_gcd(cast_time, self.current_time)

    def _perform_attack(self):
        as_value = self.attacker.total_attack_speed
        if as_value <= 0: return

        delay = 1.0 / as_value
        windup = delay * 0.2 
        
        # print(f"[{self.current_time:.2f}s] ATTACK LAUNCH (AS: {as_value:.2f})")

        snapshot_stats = self.attacker.snapshot()
        
        dmg = DamageInstance(
            raw_damage=snapshot_stats.total_ad,
            damage_type=DamageType.PHYSICAL,
            source_stats=snapshot_stats,
            proc_type=ProcType.BASIC_ATTACK,
            tags={'auto_attack'}
        )
        
        launch_event = CombatEvent(
            event_type=EventType.ATTACK_LAUNCH,
            timestamp=self.current_time,
            source=snapshot_stats,
            target=self.target,
            base_instance=dmg,
            ability_name="Auto Attack"
        )
        self.bus.publish(launch_event)

        hit_event = CombatEvent(
            event_type=EventType.PRE_MITIGATION_HIT,
            timestamp=self.current_time + windup, 
            source=snapshot_stats,
            target=self.target,
            base_instance=dmg,
            ability_name="Auto Attack"
        )
        self.schedule_event(hit_event)

        self.next_attack_time = self.current_time + delay
        self.cd_manager.trigger_gcd(windup, self.current_time)