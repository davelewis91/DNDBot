"""Items system for D&D 5e (2024 edition).

This module provides item definitions including weapons, armor, and consumables.
"""

from .armor import (
    ARMOR_REGISTRY,
    SHIELD_REGISTRY,
    get_armor,
    get_shield,
    list_armor,
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
    AMMUNITION_REGISTRY,
    CONSUMABLE_REGISTRY,
    get_ammunition,
    get_consumable,
    list_potions,
)
from .weapons import (
    WEAPON_REGISTRY,
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
    # Registries
    "AMMUNITION_REGISTRY",
    "ARMOR_REGISTRY",
    "CONSUMABLE_REGISTRY",
    "SHIELD_REGISTRY",
    "WEAPON_REGISTRY",
    # Functions
    "get_ammunition",
    "get_armor",
    "get_consumable",
    "get_shield",
    "get_weapon",
    "list_armor",
    "list_potions",
    "list_weapons",
]
