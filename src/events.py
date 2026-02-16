from dataclasses import dataclass, field
from enum import Enum, auto, IntEnum
from typing import List, Optional, Any
from engine import Stats, DamageInstance, DamageResult

# We need BuffConfig but can't import it due to circular imports.
# We will use 'Any' for the buff_config field.

class EventType(Enum):
    CAST_START = auto()
    CAST_COMPLETE = auto()
    ATTACK_LAUNCH = auto()
    PRE_MITIGATION_HIT = auto()
    POST_MITIGATION_DAMAGE = auto()
    # NEW: Event to trigger a buff application
    BUFF_APPLY = auto()

class Priority(IntEnum):
    HIGHEST = 0
    HIGH = 10
    NORMAL = 20
    LOW = 30
    LOWEST = 40

@dataclass
class CombatEvent:
    event_type: EventType
    timestamp: float
    source: Stats
    target: Stats
    
    base_instance: Optional[DamageInstance] = None
    _instances: List[DamageInstance] = field(default_factory=list)
    damage_result: Optional[DamageResult] = None
    
    # NEW: Payload for Buffs
    buff_config: Any = None 
    
    ability_name: str = "Unknown"
    
    def __post_init__(self):
        if self.base_instance and not self._instances:
            self._instances.append(self.base_instance)

    @property
    def all_instances(self) -> List[DamageInstance]:
        return self._instances

    def add_instance(self, instance: DamageInstance):
        self._instances.append(instance)