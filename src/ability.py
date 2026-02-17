from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Set, Optional
from engine import Stats, DamageInstance, DamageType, ProcType, StatType

class StatSource(Enum):
    ATTACKER = auto()
    TARGET = auto()

@dataclass
class ScalingRatio:
    stat_type: StatType
    coefficient: float
    source: StatSource = StatSource.ATTACKER

@dataclass
class AbilityLevelData:
    # FIX: All fields must have defaults to prevent "non-default argument" errors
    base_damage: float = 0.0
    cooldown: float = 0.0
    mana_cost: float = 0.0 

@dataclass
class AbilityConfig:
    name: str
    damage_type: DamageType
    
    # Default factories for lists
    ratios: List[ScalingRatio] = field(default_factory=list)
    level_data: List[AbilityLevelData] = field(default_factory=list)
    
    # Proc Rules (Restored proc_coefficient)
    proc_type: ProcType = ProcType.SPELL 
    proc_coefficient: float = 1.0        
    
    tags: Set[str] = field(default_factory=set)

class Ability:
    def __init__(self, config: AbilityConfig, rank: int = 1):
        self.config = config
        self.rank = rank
        
    def _get_stat_value(self, ratio: ScalingRatio, attacker: Stats, target: Stats) -> float:
        """
        Maps the Enum (StatType) to the actual object property.
        Restored your original robust mapping logic.
        """
        source_stats = attacker if ratio.source == StatSource.ATTACKER else target
        
        if ratio.stat_type == StatType.AD:
            return source_stats.total_ad
        elif ratio.stat_type == StatType.BONUS_AD:
            return source_stats.bonus_ad
        elif ratio.stat_type == StatType.AP:
            return source_stats.total_ap
        elif ratio.stat_type == StatType.HP:
            return source_stats.total_hp
        elif ratio.stat_type == StatType.MANA:
            return source_stats.current_mana
        elif ratio.stat_type == StatType.AS:
            return source_stats.total_attack_speed
        elif ratio.stat_type == StatType.AH:
            return source_stats.ability_haste
        elif ratio.stat_type == StatType.LETHALITY:
            return source_stats.lethality
            
        return 0.0

    def get_data(self) -> AbilityLevelData:
        # Safe rank access
        idx = min(self.rank - 1, len(self.config.level_data) - 1)
        return self.config.level_data[idx]

    def cast(self, attacker: Stats, target: Stats) -> DamageInstance:
        """
        Converts Ability Data -> Raw Damage.
        """
        rank_data = self.get_data()
        
        # 1. Base Damage
        total_raw_damage = rank_data.base_damage
        
        # 2. Add Scalings (Using your original helper method)
        for ratio in self.config.ratios:
            stat_value = self._get_stat_value(ratio, attacker, target)
            total_raw_damage += stat_value * ratio.coefficient
            
        # 3. Create the Event Packet
        # Copy tags so we don't modify the config in place
        instance_tags = self.config.tags.copy()
        instance_tags.add(self.config.name)

        return DamageInstance(
            raw_damage=total_raw_damage,
            damage_type=self.config.damage_type,
            source_stats=attacker, 
            proc_type=self.config.proc_type,
            proc_coefficient=self.config.proc_coefficient, # Restored!
            tags=instance_tags
        )