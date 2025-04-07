"""
Myth caste icons enumeration module.
"""

from enum import IntEnum, auto

class MythCaste(IntEnum):
    """Myth caste icons enumeration"""
    DAGGER = auto()
    DAGGER_WITH_HILT = auto()
    KRIS_KNIFE = auto()
    SWORD_AND_DAGGER = auto()
    CROSSED_SWORDS = auto()
    CROSSED_AXES = auto()
    SHIELD = auto()
    SHIELD_CROSSED_SWORDS = auto()
    SHIELD_CROSSED_AXES = auto()
    SIMPLE_CROWN = auto()
    CROWN = auto()
    NICE_CROWN = auto()
    MOON_ECLIPSED = auto()
    MOON = auto()
    SUN_ECLIPSED = auto()
    SUN = auto()
    COMET = auto()

    # Special values
    NUMBER_OF_MYTH_CASTE_ICONS = auto()
    ADMINISTRATOR_CASTE_ICON = NUMBER_OF_MYTH_CASTE_ICONS

    # First name rank caste
    FIRST_NAME_RANK_CASTE = MOON_ECLIPSED
