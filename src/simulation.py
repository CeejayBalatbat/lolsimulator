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
        
        # Initialize Stats immediately so we have a starting state
        self.buff_manager = BuffManager()
        self.attacker = StatPipeline.resolve(self.base_attacker, self.items, [])
        
        self.target = target
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

        # Listen for damage to track DPS
        self.bus.subscribe(EventType.POST_MITIGATION_DAMAGE, self._on_damage_dealt, Priority.NORMAL)

        self.bus.subscribe(EventType.BUFF_APPLY, self._on_buff_apply, Priority.HIGHEST)

    def _on_buff_apply(self, event: CombatEvent):
        if event.buff_config:
            self.buff_manager.apply_buff(event.buff_config, event.timestamp)
            # print(f"[{event.timestamp:.2f}s] Event Triggered Buff: {event.buff_config.name}")

    def schedule_event(self, event: CombatEvent):
        heapq.heappush(self.event_queue, (event.timestamp, event))

    def _on_damage_dealt(self, event: CombatEvent):
        if event.damage_result:
            self.total_damage_done += event.damage_result.post_mitigation_damage
            
            # ADD THIS BLOCK:
            if not hasattr(self, 'damage_history'):
                self.damage_history = []
                
            self.damage_history.append({
                "Time": event.timestamp,
                "Source": event.ability_name,
                "Type": event.base_instance.damage_type.name,
                "Pre-Mitigation": event.damage_result.pre_mitigation_damage,
                "Post-Mitigation": event.damage_result.post_mitigation_damage
            })

    def run(self, abilities: list[Ability]):
        print(f"--- STARTING SIMULATION ({self.max_duration}s) ---")
        
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
            haste_mult = self.attacker.cooldown_reduction_multiplier # Uses Dynamic Stats!
            
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

        # Summary
        dps = self.total_damage_done / self.max_duration if self.max_duration > 0 else 0
        print(f"\n--- SIMULATION ENDED ---")
        print(f"Total Damage: {self.total_damage_done:.1f}")
        print(f"DPS: {dps:.1f}")

    def _tick(self):
        self.current_time += self.time_step
        
        # --- PHASE 9: THE BUFF LOOP ---
        
        # A. Update Buff Timers
        self.buff_manager.tick(self.current_time)
        
        # B. Re-Resolve Stats
        # We take Base + Items + Current Active Buffs -> New 'self.attacker'
        active_buffs = self.buff_manager.get_all_buffs()
        
        # Only re-calculate if necessary (optimization for later), 
        # but for now we do it every frame to catch expirations exactly.
        self.attacker = StatPipeline.resolve(
            self.base_attacker, 
            self.items, 
            active_buffs
        )

    def _perform_cast(self, ability: Ability, haste_mult: float):
        print(f"[{self.current_time:.2f}s] CAST: {ability.config.name}")
        
        cast_time = 0.25 
        travel_time = 0.25
        
        # Cast Complete (Immediate)
        cast_event = CombatEvent(
            event_type=EventType.CAST_COMPLETE,
            timestamp=self.current_time,
            source=self.attacker, # Uses current dynamic stats
            target=self.target,
            ability_name=ability.config.name,
            base_instance=None 
        )
        self.bus.publish(cast_event)

        # Calculate Damage (Snapshot!)
        snapshot_stats = self.attacker.snapshot()
        dmg_instance = ability.cast(snapshot_stats, self.target)
        
        # Schedule Hit
        hit_event = CombatEvent(
            event_type=EventType.PRE_MITIGATION_HIT,
            timestamp=self.current_time + travel_time, 
            source=snapshot_stats,
            target=self.target,
            base_instance=dmg_instance,
            ability_name=ability.config.name
        )
        self.schedule_event(hit_event)

        # Update Cooldowns
        rank_data = ability.config.level_data[ability.rank - 1]
        self.cd_manager.put_on_cooldown(
            ability.config.name, 
            rank_data.cooldown, 
            haste_mult, 
            self.current_time
        )
        self.cd_manager.trigger_gcd(cast_time, self.current_time)

    def _perform_attack(self):
        # Uses Dynamic Attack Speed
        as_value = self.attacker.total_attack_speed
        
        if as_value <= 0:
            return

        delay = 1.0 / as_value
        windup = delay * 0.2 
        
        print(f"[{self.current_time:.2f}s] ATTACK LAUNCH (AS: {as_value:.2f})")

        # Snapshot Stats at Launch
        snapshot_stats = self.attacker.snapshot()
        
        dmg = DamageInstance(
            raw_damage=snapshot_stats.total_ad,
            damage_type=DamageType.PHYSICAL,
            source_stats=snapshot_stats,
            proc_type=ProcType.BASIC_ATTACK,
            tags={'auto_attack'}
        )
        
        # Fire Launch Event (Triggers on-attack buffs like Rageblade/Lethal Tempo)
        launch_event = CombatEvent(
            event_type=EventType.ATTACK_LAUNCH,
            timestamp=self.current_time,
            source=snapshot_stats,
            target=self.target,
            base_instance=dmg,
            ability_name="Auto Attack"
        )
        self.bus.publish(launch_event)

        # Schedule Hit
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