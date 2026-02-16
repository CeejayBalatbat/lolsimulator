import re
from typing import List
from engine import StatType
from item import StatModifier, StatModType

class DescriptionParser:
    # Regex Patterns
    # Format: (Regex, StatType, Is_Percent?)
    # \+?  -> Matches optional "+"
    # \s* -> Matches any amount of whitespace
    PATTERNS = [
        (r"\+?\s*(\d+)\s+Ability\s+Haste", StatType.AH, False),
        (r"\+?\s*(\d+)\s+Move\s+Speed", StatType.MS, False),
        (r"\+?\s*(\d+)%\s+Move\s+Speed", StatType.MS, True),
        (r"\+?\s*(\d+)\s+Lethality", StatType.LETHALITY, False),
        (r"\+?\s*(\d+)\s+Magic\s+Penetration", StatType.MR, False),
        (r"\+?\s*(\d+)%\s+Magic\s+Penetration", StatType.MR, True),
        (r"\+?\s*(\d+)\s+Armor\s+Penetration", StatType.ARMOR, False),
        (r"\+?\s*(\d+)%\s+Armor\s+Penetration", StatType.ARMOR, True),
        (r"\+?\s*(\d+)%\s+Crit\s+Chance", StatType.CRIT_CHANCE, False),
    ]

    @staticmethod
    def parse(description: str) -> List[StatModifier]:
        modifiers = []
        
        # 1. SURGICAL EXTRACTION (<stats> block)
        stats_match = re.search(r"<stats>(.*?)</stats>", description, re.DOTALL)
        
        if stats_match:
            target_text = stats_match.group(1)
        else:
            # Fallback: If no stats block, use everything (risky but needed sometimes)
            target_text = description
            
        # 2. CLEANUP
        # Replace HTML tags with a single space to prevent "15<br>Ability" becoming "15Ability"
        clean_text = re.sub(r"<[^>]+>", " ", target_text)
        
        # 3. SCAN
        for pattern, stat_type, is_percent in DescriptionParser.PATTERNS:
            matches = re.findall(pattern, clean_text)
            for value in matches:
                try:
                    val = float(value)
                    
                    if is_percent:
                        if stat_type == StatType.CRIT_CHANCE:
                            val = val / 100.0
                            mod_type = StatModType.FLAT 
                        else:
                            val = val / 100.0 
                            mod_type = StatModType.PERCENT_BASE
                    else:
                        mod_type = StatModType.FLAT

                    modifiers.append(StatModifier(stat_type, val, mod_type))
                    
                except ValueError:
                    continue
                
        return modifiers