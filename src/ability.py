from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Set
# CRITICAL: Import StatType from engine to avoid mismatches
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
    base_damage: float
    mana_cost: float
    cooldown: float

@dataclass
class AbilityConfig:
    name: str
    damage_type: DamageType
    ratios: List[ScalingRatio]
    level_data: List[AbilityLevelData]
    
    # Phase 6 Updates: Proc Rules
    proc_type: ProcType = ProcType.SPELL 
    proc_coefficient: float = 1.0        
    
    tags: Set[str] = field(default_factory=set)

class Ability:
    def __init__(self, config: AbilityConfig, rank: int = 1):
        self.config = config
        self.rank = rank
        
        if self.rank < 1 or self.rank > len(self.config.level_data):
            raise ValueError(f"Rank {self.rank} is out of bounds for {self.config.name}")

    def _get_stat_value(self, ratio: ScalingRatio, attacker: Stats, target: Stats) -> float:
        """
        Maps the Enum (StatType.AD) to the actual object property (stats.total_ad).
        """
        source_stats = attacker if ratio.source == StatSource.ATTACKER else target
        
        # --- MAPPING LOGIC ---
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

    def cast(self, attacker: Stats, target: Stats) -> DamageInstance:
        """
        Converts Ability Data + Context -> A Raw Damage Packet.
        """
        level_idx = self.rank - 1
        rank_data = self.config.level_data[level_idx]
        
        # 1. Base Damage
        total_raw_damage = rank_data.base_damage
        
        # 2. Add Scalings
        for ratio in self.config.ratios:
            stat_value = self._get_stat_value(ratio, attacker, target)
            total_raw_damage += stat_value * ratio.coefficient
            
        # 3. Create the Event Packet
        return DamageInstance(
            raw_damage=total_raw_damage,
            damage_type=self.config.damage_type,
            source_stats=attacker, 
            proc_type=self.config.proc_type,
            proc_coefficient=self.config.proc_coefficient,
            tags=self.config.tags.copy()
        )