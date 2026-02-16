from item import ItemConfig
from pipeline import EventManager
from passives import OnHitDamagePassive, SpellbladePassive
from engine import DamageType

class InventoryManager:
    def __init__(self, event_manager: EventManager):
        self.bus = event_manager
        
    def equip_item(self, item_config: ItemConfig):
        # 1. Register Passives directly attached to the item
        for passive in item_config.passives:
            # Check if it has a register method (Duck Typing)
            if hasattr(passive, 'register'):
                passive.register(self.bus)