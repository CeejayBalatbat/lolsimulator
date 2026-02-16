from typing import List
from engine import Stats, StatType
from buffs import BuffManager, ActiveBuff
from item import ItemConfig, StatModType

class StatPipeline:
    @staticmethod
    def resolve(base_stats: Stats, items: List[ItemConfig], buffs: List[ActiveBuff]) -> Stats:
        # 1. Start with Snapshot
        final = base_stats.snapshot()
        
        # 2. Apply Items (Paranoid Check)
        for item in items:
            # CHECK A: Direct Attributes (Common Loader pattern)
            # We use getattr(item, 'field', 0.0) to be safe if fields don't exist
            final.base_ad += getattr(item, 'base_ad', 0.0)
            final.bonus_ad += getattr(item, 'bonus_ad', 0.0)
            final.base_ap += getattr(item, 'base_ap', 0.0)
            final.bonus_ap += getattr(item, 'bonus_ap', 0.0)
            final.base_hp += getattr(item, 'base_hp', 0.0)
            final.bonus_hp += getattr(item, 'bonus_hp', 0.0)
            
            # Map common names (Loader might use 'attack_damage' instead of 'bonus_ad')
            final.bonus_ad += getattr(item, 'attack_damage', 0.0)
            final.bonus_hp += getattr(item, 'health', 0.0)
            final.bonus_ap += getattr(item, 'ability_power', 0.0)
            final.ability_haste += getattr(item, 'ability_haste', 0.0)
            final.bonus_attack_speed += getattr(item, 'attack_speed', 0.0)
            
            # CHECK B: Modifiers List (Phase 4 pattern)
            if hasattr(item, 'modifiers'):
                for mod in item.modifiers:
                    if mod.stat == StatType.AD:
                        final.bonus_ad += mod.value
                    elif mod.stat == StatType.AP:
                        final.bonus_ap += mod.value
                    elif mod.stat == StatType.HP:
                        final.bonus_hp += mod.value
                    elif mod.stat == StatType.AS:
                        final.bonus_attack_speed += mod.value
                    elif mod.stat == StatType.AH:
                        final.ability_haste += mod.value
                    elif mod.stat == StatType.CRIT_CHANCE:
                        final.crit_chance += mod.value
                    elif mod.stat == StatType.LETHALITY:
                        final.lethality += mod.value
                    elif mod.stat == StatType.ARMOR_PEN_PERCENT:
                        final.armor_pen_percent += mod.value

        # 3. Apply Buffs
        for buff in buffs:
            for mod in buff.config.modifiers:
                multiplier = buff.stacks
                val = mod.value * multiplier
                
                if mod.stat == StatType.AD:
                    final.bonus_ad += val
                elif mod.stat == StatType.AP:
                    final.bonus_ap += val
                elif mod.stat == StatType.AS:
                    final.bonus_attack_speed += val
                # Add other buff stats as needed...
                
        return final

    @staticmethod
    def resolve_target(base_target: Stats, debuff_manager: BuffManager) -> Stats:
        # (This remains unchanged from previous step)
        final = base_target.snapshot()
        active_debuffs = debuff_manager.get_all_buffs()
        
        total_armor_shred_percent = 0.0
        
        for buff in active_debuffs:
            for mod in buff.config.modifiers:
                if mod.stat == StatType.ARMOR and mod.value < 0:
                    total_armor_shred_percent += (abs(mod.value) * buff.stacks)
                    
        if total_armor_shred_percent > 0:
            reduction_mult = 1.0 - total_armor_shred_percent
            final.base_armor *= reduction_mult
            final.bonus_armor *= reduction_mult
            
        return final