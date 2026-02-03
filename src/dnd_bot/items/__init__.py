"""Items system for D&D 5e (2024 edition).

This module provides item definitions including weapons, armor, and consumables.
"""

from .armor import (
    get_all_armor,
    get_armor,
    get_shield,
    list_armor,
    list_shields,
)
from .base import (
    Ammunition,
    Armor,
    ArmorType,
    Consumable,
    DamageType,
    Item,
    ItemType,
    Rarity,
    Shield,
    Weapon,
    WeaponCategory,
    WeaponProperty,
)
from .consumables import (
    get_all_ammunition,
    get_all_consumables,
    get_ammunition,
    get_consumable,
    list_ammunition,
    list_consumables,
    list_potions,
)
from .weapons import (
    get_all_weapons,
    get_weapon,
    list_weapons,
)

__all__ = [
    # Base types
    "Ammunition",
    "Armor",
    "ArmorType",
    "Consumable",
    "DamageType",
    "Item",
    "ItemType",
    "Rarity",
    "Shield",
    "Weapon",
    "WeaponCategory",
    "WeaponProperty",
    # Functions
    "get_ammunition",
    "get_armor",
    "get_consumable",
    "get_shield",
    "get_weapon",
    "list_armor",
    "list_potions",
    "list_shields",
    "list_weapons",
    "get_all_ammunition",
    "get_all_armor",
    "get_all_consumables",
    "get_all_weapons",
    "list_ammunition",
    "list_consumables",
]
