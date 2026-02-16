from engine import StatType, DamageType
from item import StatModifier, StatModType
from passives import SpellbladePassive, OnHitDamagePassive, GrantBuffOnHitPassive
from buffs import BuffConfig, StatModifier

# Define Quicken Buff (20 MS for 2s)
QUICKEN_BUFF = BuffConfig(
    name="Quicken",
    duration=2.0,
    max_stacks=1,
    modifiers=[StatModifier(StatType.MS, 20.0, StatModType.FLAT)],
    refresh_on_stack=True
)

ITEM_OVERRIDES = {
    "Trinity Force": {
        # NO STATS! The parser handles AH now.
        "passives": [
            SpellbladePassive(damage_percent_base_ad=2.0),
            GrantBuffOnHitPassive(QUICKEN_BUFF)  # <--- Add this!
        ]
    },
    "Blade of the Ruined King": {
        "passives": [
            # The "Mist's Edge" Passive (Simplified to flat dmg for now, usually % HP)
            OnHitDamagePassive(amount=40.0, damage_type=DamageType.PHYSICAL)
        ]
    },
    "Kraken Slayer": {
        "stats": [
             # Often missing from API if it's a unique stat line
             StatModifier(StatType.MS, 7.0, StatModType.PERCENT_BASE) 
        ]
    }
}