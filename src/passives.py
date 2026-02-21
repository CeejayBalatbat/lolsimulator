from typing import List, Optional
from engine import ProcType, Stats, DamageType, DamageInstance, StatType
from events import EventType, CombatEvent, Priority
from pipeline import EventManager
from buffs import BuffConfig
from item import StatModifier, StatModType

# ------------------------------------------------------------------
# SIMPLE PASSIVES
# ------------------------------------------------------------------

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
        if not (event.base_instance.proc_type & ProcType.ON_HIT):
            return

        eff = event.base_instance.proc_coefficient
        if eff <= 0: return

        final_amt = self.amount * eff
        
        extra = DamageInstance(
            raw_damage=final_amt,
            damage_type=self.damage_type,
            source_stats=event.source,
            proc_type=ProcType.NONE, 
            tags={'passive_proc', 'on_hit'}
        )
        event.add_instance(extra)

class AwePassive:
    """
    Muramana Passive: Awe
    Grants Bonus AD equal to 2.5% of Max Mana.
    """
    def __init__(self, mana_ratio: float = 0.025):
        self.mana_ratio = mana_ratio

    def modify_stats(self, stats: Stats):
        # We calculate the bonus based on the Total Mana and inject it into Bonus AD
        bonus_ad = stats.total_mana * self.mana_ratio
        stats.bonus_ad += bonus_ad


class ShockPassive:
    """
    Muramana Passive: Shock
    Attacks and Abilities deal 1.5% Max Mana as bonus physical damage.
    """
    def __init__(self, mana_ratio: float = 0.015):
        self.mana_ratio = mana_ratio

    def register(self, event_manager: EventManager):
        # Listen for hits right before mitigation
        event_manager.subscribe(EventType.PRE_MITIGATION_HIT, self._on_hit, Priority.HIGH)

    def _on_hit(self, event: CombatEvent):
        # Only trigger on Auto Attacks (ON_HIT) or Abilities (SPELL)
        if not (event.base_instance.proc_type & (ProcType.ON_HIT | ProcType.SPELL)):
            return

        # Calculate damage based on the Attacker's Total Mana
        bonus_dmg = event.source.total_mana * self.mana_ratio
        
        extra = DamageInstance(
            raw_damage=bonus_dmg,
            damage_type=DamageType.PHYSICAL,
            source_stats=event.source,
            proc_type=ProcType.NONE, # NONE prevents infinite loops!
            tags={'passive_proc', 'shock'}
        )
        event.add_instance(extra)

class RuinedKingPassive:
    def __init__(self, percent_current_hp: float = 0.06): 
        self.percent_current_hp = percent_current_hp

    def register(self, event_manager: EventManager):
        event_manager.subscribe(EventType.PRE_MITIGATION_HIT, self._on_hit, Priority.HIGH)

    def _on_hit(self, event: CombatEvent):
        if not (event.base_instance.proc_type & (ProcType.BASIC_ATTACK | ProcType.ON_HIT)):
            return

        # Calculate based on target's live health
        target_current_hp = event.target.current_health
        bonus_dmg = max(15.0, target_current_hp * self.percent_current_hp)

        # Simply add it directly to the base instance
        event.base_instance.raw_damage += bonus_dmg

# ------------------------------------------------------------------
# STATEFUL PASSIVES (Require Reset)
# ------------------------------------------------------------------

class SpellbladePassive:
    """
    Sheen / Trinity Force logic.
    """
    def __init__(self, damage_percent_base_ad: float):
        self.ratio = damage_percent_base_ad
        self.active = False
        self.cooldown = 1.5
        self.last_proc_time = -999.0 

    def register(self, event_manager: EventManager):
        event_manager.subscribe(EventType.CAST_COMPLETE, self._on_cast)
        event_manager.subscribe(EventType.PRE_MITIGATION_HIT, self._on_hit, Priority.HIGH)

    def _on_cast(self, event: CombatEvent):
        # Only charge if off cooldown
        if event.timestamp >= self.last_proc_time + self.cooldown:
            self.active = True

    def _on_hit(self, event: CombatEvent):
        if not self.active:
            return
            
        # Standard Spellblade internal CD check
        if event.timestamp < self.last_proc_time + self.cooldown:
            return

        # Must be an ON_HIT trigger (usually Basic Attack or Q)
        if not (event.base_instance.proc_type & ProcType.ON_HIT):
            return

        # Apply Bonus
        bonus_dmg = event.source.base_ad * self.ratio
        event.base_instance.raw_damage += bonus_dmg
        
        # Reset
        self.active = False
        self.last_proc_time = event.timestamp


class GrantBuffOnHitPassive:
    """
    Applies a buff to SELF when you hit. (e.g. Trinity Force Move Speed)
    """
    def __init__(self, buff_config: BuffConfig):
        self.buff_config = buff_config
        self.bus = None 

    def register(self, event_manager: EventManager):
        self.bus = event_manager
        event_manager.subscribe(EventType.PRE_MITIGATION_HIT, self._on_hit)

    def _on_hit(self, event: CombatEvent):
        if not (event.base_instance.proc_type & ProcType.BASIC_ATTACK):
            return

        # Apply to SELF (Source)
        buff_event = CombatEvent(
            event_type=EventType.BUFF_APPLY,
            timestamp=event.timestamp,
            source=event.source,
            target=event.source, # <--- Target is Self
            buff_config=self.buff_config
        )
        self.bus.publish(buff_event)


# ------------------------------------------------------------------
# PHASE 12: DEBUFF PASSIVES (Black Cleaver)
# ------------------------------------------------------------------

class CarvePassive:
    """
    Unique Passive: Carve (Black Cleaver)
    Dealing physical damage applies a stack of 5% Armor Reduction.
    """
    def __init__(self):
        self.bus = None
        # Define the Debuff (-5% Armor per stack)
        self.debuff_config = BuffConfig(
            name="Carve",
            duration=6.0,
            max_stacks=6,
            modifiers=[
                StatModifier(
                    stat=StatType.ARMOR, 
                    value=-0.05, 
                    mod_type=StatModType.PERCENT_BASE 
                )
            ]
        )

    def register(self, event_manager: EventManager):
        self.bus = event_manager
        # Listen for ANY damage completion (Auto, Ability, Spellblade, etc.)
        event_manager.subscribe(EventType.POST_MITIGATION_DAMAGE, self._on_damage)

    def _on_damage(self, event: CombatEvent):
        # 1. Check Damage Type
        if event.base_instance.damage_type != DamageType.PHYSICAL:
            return
            
        # 2. Apply Debuff to ENEMY (Target)
        buff_event = CombatEvent(
            event_type=EventType.BUFF_APPLY,
            timestamp=event.timestamp,
            source=event.source,
            target=event.target, # <--- Target is Enemy
            buff_config=self.debuff_config
        )
        self.bus.publish(buff_event)