from dataclasses import dataclass, field, replace
from enum import Enum, auto, Flag
from typing import Any, Set, List
from copy import deepcopy

# ==========================================
# 1. ENUMS & FLAGS
# ==========================================

class DamageType(Enum):
    PHYSICAL = auto()
    MAGIC = auto()
    TRUE = auto()

class ProcType(Flag):
    NONE = 0
    ON_HIT = auto()      # Triggers BotRK, Nashor's
    ON_ATTACK = auto()   # Triggers Kraken, Rageblade
    SPELL = auto()       # Triggers Luden's
    PERIODIC = auto()    # DoT (Teemo/Cassio)
    
    # Common Combinations
    BASIC_ATTACK = ON_HIT | ON_ATTACK
    ABILITY = SPELL


class StatType(Enum):
    # Primary
    AD = auto()  # Attack Damage
    AP = auto()  # Ability Power
    HP = auto()  # Health
    MANA = auto()
    ARMOR = auto()
    MR = auto()  # Magic Resist
    
    # Secondary
    AS = auto()  # Attack Speed
    AH = auto()  # Ability Haste
    MS = auto()  # Move Speed
    
    # Crit / Pen
    CRIT_CHANCE = auto()
    LETHALITY = auto()
    
    # Special
    BONUS_AD = auto() # Specific target for modifiers
    
# ==========================================
# 2. THE STATS CLASS (State + Definitions)
# ==========================================

@dataclass
class Stats:
    # --- A. MUTABLE STATE (Changes constantly) ---
    current_health: float = 0.0
    current_mana: float = 0.0

    # --- B. PRIMARY STATS (Base vs Bonus) ---
    # Health
    base_hp: float = 0.0
    bonus_hp: float = 0.0
    
    # Attack Damage
    base_ad: float = 0.0
    bonus_ad: float = 0.0
    
    # Ability Power
    base_ap: float = 0.0
    bonus_ap: float = 0.0
    
    # Armor & MR
    base_armor: float = 0.0
    bonus_armor: float = 0.0
    base_mr: float = 0.0
    bonus_mr: float = 0.0
    
    # --- C. OFFENSIVE STATS ---
    # Attack Speed (Base is usually ~0.625)
    base_attack_speed: float = 0.625 
    bonus_attack_speed: float = 0.0  # 0.50 = +50%
    
    # Haste & Crit
    ability_haste: float = 0.0
    crit_chance: float = 0.0         # 0.0 to 1.0
    crit_damage_multiplier: float = 1.75 # 175%
    
    # Penetration
    lethality: float = 0.0
    armor_pen_percent: float = 0.0   # 0.30 = 30% Pen
    magic_pen_flat: float = 0.0
    magic_pen_percent: float = 0.0

    # --- D. COMPUTED PROPERTIES (Public API) ---
    @property
    def total_hp(self) -> float:
        return self.base_hp + self.bonus_hp

    @property
    def total_ad(self) -> float:
        return self.base_ad + self.bonus_ad

    @property
    def total_ap(self) -> float:
        return self.base_ap + self.bonus_ap

    @property
    def total_armor(self) -> float:
        return self.base_armor + self.bonus_armor

    @property
    def total_mr(self) -> float:
        return self.base_mr + self.bonus_mr

    @property
    def total_attack_speed(self) -> float:
        """Returns Attacks Per Second. Hard capped at 2.50."""
        val = self.base_attack_speed * (1.0 + self.bonus_attack_speed)
        return min(2.5, val)

    @property
    def cooldown_reduction_multiplier(self) -> float:
        """Converts Haste -> Cooldown Multiplier (e.g. 100 Haste = 0.5)"""
        if self.ability_haste < 0: return 1.0
        return 100.0 / (100.0 + self.ability_haste)

    def snapshot(self) -> 'Stats':
        """Creates a frozen copy of stats."""
        return deepcopy(self)

# ==========================================
# 3. DATA PACKETS
# ==========================================

@dataclass
class DamageInstance:
    raw_damage: float
    damage_type: DamageType
    source_stats: Stats # Snapshot of attacker
    
    # Context
    proc_type: ProcType = ProcType.NONE
    proc_coefficient: float = 1.0
    tags: Set[str] = field(default_factory=set)

@dataclass
class DamageResult:
    damage_type: Any # DamageType
    pre_mitigation_damage: float # The "Raw" number
    post_mitigation_damage: float # The "Final" number after armor

# ==========================================
# 4. THE LOGIC ENGINE
# ==========================================

class DamageEngine:
    """
    The Math Core. Purely functional. 
    Input: Instance + Target Stats -> Output: Result
    """
    
    def calculate_damage(self, instance: DamageInstance, target: Stats) -> DamageResult:
        # 1. True Damage Check (Bypasses everything)
        if instance.damage_type == DamageType.TRUE:
            return DamageResult(
                post_mitigation_damage=instance.raw_damage,
                mitigated_amount=0.0,
                breakdown={'raw': instance.raw_damage, 'mitigated': 0}
            )

        # 2. Select Resistance & Penetration
        if instance.damage_type == DamageType.PHYSICAL:
            defense = target.total_armor
            flat_pen = instance.source_stats.lethality 
            percent_pen = instance.source_stats.armor_pen_percent
        else: # MAGIC
            defense = target.total_mr
            flat_pen = instance.source_stats.magic_pen_flat
            percent_pen = instance.source_stats.magic_pen_percent

        # 3. Calculate Effective Resistance
        # Order: % Pen -> Flat Pen -> Floor at 0
        effective_defense = defense * (1.0 - percent_pen)
        effective_defense = effective_defense - flat_pen
        
        if effective_defense < 0:
            effective_defense = 0

        # 4. Mitigation Formula: 100 / (100 + Def)
        mitigation_multiplier = 100.0 / (100.0 + effective_defense)
        
        final_damage = instance.raw_damage * mitigation_multiplier

        return DamageResult(
            post_mitigation_damage=final_damage,
            mitigated_amount=instance.raw_damage - final_damage,
            breakdown={
                'raw': instance.raw_damage,
                'defense_raw': defense,
                'defense_eff': effective_defense,
                'final': final_damage
            }
        )