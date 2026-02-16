from dataclasses import dataclass, field
from typing import List, Dict
from item import StatModifier

@dataclass
class BuffConfig:
    name: str
    duration: float
    max_stacks: int
    modifiers: List[StatModifier]   # Move this ABOVE refresh_on_stack
    refresh_on_stack: bool = True   # Fields with defaults must be last

class ActiveBuff:
    def __init__(self, config: BuffConfig, start_time: float):
        self.config = config
        self.stacks = 1
        self.start_time = start_time
        self.expiration_time = start_time + config.duration

    def add_stack(self, current_time: float):
        if self.stacks < self.config.max_stacks:
            self.stacks += 1
        
        if self.config.refresh_on_stack:
            self.expiration_time = current_time + self.config.duration

    @property
    def is_expired(self, current_time: float) -> bool:
        # Note: We pass current_time in to check
        return False # Handled by manager logic usually, simpler there

class BuffManager:
    def __init__(self):
        # Map: BuffName -> ActiveBuff Instance
        self.active_buffs: Dict[str, ActiveBuff] = {}

    def apply_buff(self, config: BuffConfig, current_time: float):
        if config.name in self.active_buffs:
            # Existing buff: Add Stack
            self.active_buffs[config.name].add_stack(current_time)
        else:
            # New buff: Create
            self.active_buffs[config.name] = ActiveBuff(config, current_time)
            print(f"[{current_time:.2f}s] BUFF APPLIED: {config.name}")

    def tick(self, current_time: float):
        """Removes expired buffs."""
        expired = []
        for name, buff in self.active_buffs.items():
            if current_time >= buff.expiration_time:
                expired.append(name)
        
        for name in expired:
            del self.active_buffs[name]
            print(f"[{current_time:.2f}s] BUFF EXPIRED: {name}")

    def get_all_buffs(self) -> List[ActiveBuff]:
        return list(self.active_buffs.values())