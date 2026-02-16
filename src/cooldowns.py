from dataclasses import dataclass
from typing import Dict

@dataclass
class CooldownState:
    current_time: float = 0.0
    is_ready: bool = True

class CooldownManager:
    def __init__(self):
        # Map ability_name -> state
        self.states: Dict[str, CooldownState] = {}
        self.global_cooldown: float = 0.0 # Time until we can act again

    def is_ready(self, ability_name: str, current_sim_time: float) -> bool:
        # 1. Check Global Cooldown (Animation Lock)
        if current_sim_time < self.global_cooldown:
            return False

        # 2. Check Specific Ability Cooldown
        if ability_name not in self.states:
            return True # Not tracked = Ready
        
        return current_sim_time >= self.states[ability_name].current_time

    def put_on_cooldown(self, ability_name: str, base_cooldown: float, haste_mult: float, current_sim_time: float):
        real_cooldown = base_cooldown * haste_mult
        
        self.states[ability_name] = CooldownState(
            current_time=current_sim_time + real_cooldown,
            is_ready=False
        )

    def trigger_gcd(self, duration: float, current_sim_time: float):
        """Locks the character for 'duration' seconds (Cast Time or Attack Windup)"""
        self.global_cooldown = max(self.global_cooldown, current_sim_time + duration)