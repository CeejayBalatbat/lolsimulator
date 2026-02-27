import json
from typing import Dict, Any
from item import ItemConfig, StatModifier, StatModType
from engine import StatType
from passives import SpellbladePassive, CarvePassive, AwePassive, ShockPassive, RuinedKingPassive # <--- Import your new passive!

class ItemLoader:
    @staticmethod
    def load_all(raw_data: Dict[str, Any]) -> Dict[str, ItemConfig]:
        """
        Parses Riot API JSON into our internal ItemConfig format.
        """
        library = {}
        
        for item_id, data in raw_data.items():
            name = data.get("name", "Unknown Item")
            stats_block = data.get("stats", {})
            gold = data.get("gold", {}).get("total", 0)
            
            # Create Config
            config = ItemConfig(name=name, cost=gold)
            
            # --- PARSE STATS ---
            # Riot uses specific keys, we map them to our ItemConfig fields
            # Note: We rely on the 'Paranoid Pipeline' to read these, 
            # so we can just store them as attributes or modifiers.
            
            # Direct Mapping (Simple)
            if "FlatPhysicalDamageMod" in stats_block:
                config.base_ad = stats_block["FlatPhysicalDamageMod"]
            if "FlatMagicDamageMod" in stats_block:
                config.base_ap = stats_block["FlatMagicDamageMod"]
            if "FlatHPPoolMod" in stats_block:
                config.base_hp = stats_block["FlatHPPoolMod"]
            if "FlatArmorMod" in stats_block:
                config.base_armor = stats_block["FlatArmorMod"]
            if "FlatSpellBlockMod" in stats_block:
                config.base_mr = stats_block["FlatSpellBlockMod"]
                
            # Parse Modifiers list for complex stats (AS, Haste, Crit)
            # (Riot data varies, this is a simplified example of parsing)
            if "PercentAttackSpeedMod" in stats_block:
                config.modifiers.append(StatModifier(
                    stat=StatType.AS, 
                    value=stats_block["PercentAttackSpeedMod"], 
                    mod_type=StatModType.PERCENT_BONUS
                ))
            
            # ... (Add other parsers for Haste/Crit as needed) ...
            
            # Store in library
            library[name] = config

        # ------------------------------------------------------------------
        # MANUAL OVERRIDES (The "Hardcoded Backup")
        # ------------------------------------------------------------------
        
        # 1. TRINITY FORCE (Fix Stats & Add Spellblade)
        if "Trinity Force" in library:
            tf = library["Trinity Force"]
            # Ensure stats are correct (API sometimes misses Haste/AS on mythics)
            tf.base_ad = 45.0
            tf.bonus_attack_speed = 0.33
            tf.ability_haste = 20.0
            tf.base_hp = 300.0
            
            # Add Passives
            tf.passives.append(SpellbladePassive(damage_percent_base_ad=2.0))
            # (You can add Quicken here too if you want)

        # 2. BLACK CLEAVER (Add Carve)
        if "Black Cleaver" in library:
            bc = library["Black Cleaver"]
            bc.base_ad = 55.0
            bc.base_hp = 400.0
            bc.ability_haste = 20.0
            
            # Inject Phase 12 Passive
            bc.passives.append(CarvePassive())
            print(f"✅ Loaded Black Cleaver with Carve Passive")
            
        # 3. THE COLLECTOR (Add Lethality)
        if "The Collector" in library:
            col = library["The Collector"]
            col.base_ad = 60.0
            col.crit_chance = 0.20
            col.lethality = 12.0 # Force Lethality

        # 4. MURAMANA (Add Awe and Shock)
        if "Muramana" in library:
            mur = library["Muramana"]
            mur.base_ad = 35.0
            mur.bonus_mana = 860.0
            mur.ability_haste = 15.0
            
            
            mur.passives.append(AwePassive(0.025))
            mur.passives.append(ShockPassive(0.015))
            print("✅ Loaded Muramana with Awe and Shock Passives")

        # 5. BLADE OF THE RUINED KING 
        # (Using .lower() search so Riot's capitalization doesn't break our code)
        for item_name, item_config in library.items():
            if "ruined king" in item_name.lower():
                item_config.base_ad = 40.0
                item_config.bonus_attack_speed = 0.25
                
                from passives import RuinedKingPassive
                if not any(isinstance(p, RuinedKingPassive) for p in item_config.passives):
                    item_config.passives.append(RuinedKingPassive(0.06)) 
                    print(f"✅ Loaded BoRK passive onto: {item_name}")
            
        # 6. INFINITY EDGE
        if "Infinity Edge" in library:
            ie = library["Infinity Edge"]
            ie.base_ad = 80.0
            ie.crit_chance = 0.25 # 25% Crit
            ie.bonus_crit_damage = 0.40 # IE passive: +40% Crit Damage
            print("✅ Loaded Infinity Edge with Crit modifiers")

        # 7. LORD DOMINIK'S REGARDS
        if "Lord Dominik's Regards" in library:
            ldr = library["Lord Dominik's Regards"]
            ldr.base_ad = 40.0
            ldr.crit_chance = 0.25
            ldr.armor_pen_percent = 0.45
            print("✅ Loaded LDR with 45% Armor Pen")

        return library