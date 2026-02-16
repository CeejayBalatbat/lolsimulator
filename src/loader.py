from engine import StatType
from item import ItemConfig, StatModifier, StatModType
from item_overrides import ITEM_OVERRIDES
from description_parser import DescriptionParser # Import the new tool

# Standard JSON keys
STAT_MAP = {
    'FlatPhysicalDamageMod': StatType.AD,
    'FlatMagicDamageMod': StatType.AP,
    'FlatHPPoolMod': StatType.HP,
    'FlatMPPoolMod': StatType.MANA,
    'FlatArmorMod': StatType.ARMOR,
    'FlatSpellBlockMod': StatType.MR,
    # 'FlatMovementSpeedMod': StatType.MS, # Often redundant with description
    'PercentAttackSpeedMod': StatType.AS,
    'FlatCritChanceMod': StatType.CRIT_CHANCE,
}

class ItemLoader:
    @staticmethod
    def parse_item(item_id: str, riot_data: dict) -> ItemConfig:
        name = riot_data['name']
        cost = riot_data['gold']['total']
        
        modifiers = []
        parsed_stat_types = set()

        # 1. Parse JSON 'stats' (The Easy Stuff)
        stats = riot_data.get('stats', {})
        for key, value in stats.items():
            if key in STAT_MAP:
                st = STAT_MAP[key]
                modifiers.append(StatModifier(st, float(value), StatModType.FLAT))
                parsed_stat_types.add(st)
        
        # 2. Parse Description (The Deep Dive)
        description = riot_data.get('description', "")
        if description:
            hidden_mods = DescriptionParser.parse(description)
            
            for mod in hidden_mods:
                # OPTIONAL: Don't double-add if we already found it in JSON?
                # Usually parsing description is safer for "missing" stats like Haste.
                # If JSON has AD and Desc has AD, usually they match.
                # Let's add it only if NOT in JSON to be safe from duplicates.
                if mod.stat not in parsed_stat_types:
                     modifiers.append(mod)

        # 3. Apply Overrides (PASSIVES ONLY)
        # We assume stats are handled by the parser now.
        passive_objects = [] 
        if name in ITEM_OVERRIDES:
            override_data = ITEM_OVERRIDES[name]
            if "passives" in override_data:
                passive_objects = override_data["passives"]
                
        return ItemConfig(
            name=name, 
            modifiers=modifiers, 
            cost=cost, 
            passives=passive_objects
        )

    @staticmethod
    def load_all(raw_data: dict) -> dict:
        library = {}
        for item_id, data in raw_data.items():
            if not data.get('gold', {}).get('purchasable', False): continue
            
            maps = data.get('maps', {})
            if str(11) not in maps or not maps[str(11)]: continue

            item = ItemLoader.parse_item(item_id, data)
            
            # Post-Process Overrides
            if item.name in ITEM_OVERRIDES:
                data = ITEM_OVERRIDES[item.name]
                if "passives" in data:
                    item.passives = data["passives"]

            library[item.name] = item
            
        return library