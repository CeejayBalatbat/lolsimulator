from dataclasses import dataclass
from typing import List
from engine import Stats

@dataclass
class Scenario:
    name: str
    duration: float          # e.g., 10.0 seconds
    attacker_level: int      # Affects base stats (Phase 9 feature, but placeholder now)
    target_stats: Stats      # The Dummy (HP, Armor, MR)
    
    # Optional: Restrictions (e.g. "Must include Boots")
    required_item_ids: List[str] = None