from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Any # Any allows storing Passive instances

# ... Enums (StatModType) ...

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
    name: str
    modifiers: List[StatModifier]
    cost: int = 0
    # THIS FIELD MUST EXIST for overrides to work:
    passives: List[Any] = field(default_factory=list) 
    passive_names: List[str] = field(default_factory=list)