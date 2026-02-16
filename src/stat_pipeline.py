from typing import List
from engine import Stats, StatType
from item import ItemConfig, StatModType
from buffs import ActiveBuff # Import the new class

class StatPipeline:
    @staticmethod
    def resolve(base_stats: Stats, items: List[ItemConfig], buffs: List[ActiveBuff] = None) -> Stats:
        # 1. Deep Copy Base
        final = base_stats.snapshot() 
        
        # Initialize Modifiers Bucket
        # Structure: mods[StatType] = {'flat': 0, 'percent_base': 0, 'percent_bonus': 0}
        mods = {}

        # Helper to accumulate mods
        def add_mod(stat_mod, stacks=1):
            if stat_mod.stat not in mods:
                mods[stat_mod.stat] = {'flat': 0.0, 'percent_base': 0.0, 'percent_bonus': 0.0}
            
            if stat_mod.mod_type == StatModType.FLAT:
                mods[stat_mod.stat]['flat'] += stat_mod.value * stacks
            elif stat_mod.mod_type == StatModType.PERCENT_BASE:
                mods[stat_mod.stat]['percent_base'] += stat_mod.value * stacks
            elif stat_mod.mod_type == StatModType.PERCENT_BONUS:
                mods[stat_mod.stat]['percent_bonus'] += stat_mod.value * stacks

        # 2. Aggregation Loop (Items)
        for item in items:
            for mod in item.modifiers:
                add_mod(mod)

        # 3. Aggregation Loop (Buffs) - NEW!
        if buffs:
            for buff in buffs:
                for mod in buff.config.modifiers:
                    add_mod(mod, stacks=buff.stacks) # Multiply by stacks!

        # 4. Application Loop (Apply to 'final' stats)
        # Apply AD
        if StatType.AD in mods:
            m = mods[StatType.AD]
            added_bonus = m['flat'] + (final.base_ad * m['percent_base'])
            final.bonus_ad += added_bonus

        # Apply Attack Speed
        if StatType.AS in mods:
            # Remember: AS mods usually add to the Bonus Ratio
            final.bonus_attack_speed += mods[StatType.AS]['flat']

        # Apply Haste
        if StatType.AH in mods:
            final.ability_haste += mods[StatType.AH]['flat']

        # (Add other stats like HP/AP/Armor as needed following the pattern)

        return final