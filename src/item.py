from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Any 

class StatModType(Enum):
    FLAT = auto()
    PERCENT_BASE = auto()
    PERCENT_BONUS = auto()

@dataclass
class StatModifier:
    stat: Any # StatType
    value: float
    mod_type: StatModType

@dataclass
class ItemConfig:
    # 1. NO DEFAULT VALUE (Must come first)
    name: str

    # 2. HAS DEFAULT VALUE (Must come after)
    base_ad: float = 0.0
    
    # FIX: Added default_factory=list
    modifiers: List[StatModifier] = field(default_factory=list)
    
    cost: int = 0
    passives: List[Any] = field(default_factory=list) 
    passive_names: List[str] = field(default_factory=list)