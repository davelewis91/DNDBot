"""Weapon definitions for D&D 5e (2024 edition)."""

from functools import lru_cache

from dnd_bot.data import load_weapons

from .base import DamageType, Weapon, WeaponCategory, WeaponProperty


def _parse_weapon(weapon_id: str, data: dict) -> Weapon:
    """Parse YAML data into a Weapon model.

    Parameters
    ----------
    weapon_id : str
        The weapon's unique identifier.
    data : dict
        Raw YAML data for the weapon.

    Returns
    -------
    Weapon
        The parsed weapon model.
    """
    return Weapon(
        id=weapon_id,
        name=data["name"],
        category=WeaponCategory(data["category"]),
        damage_dice=data["damage_dice"],
        damage_type=DamageType(data["damage_type"]),
        properties=[WeaponProperty(p) for p in data.get("properties", [])],
        range_normal=data.get("range_normal"),
        range_long=data.get("range_long"),
        versatile_dice=data.get("versatile_dice"),
        weight=data.get("weight", 0.0),
        value=data.get("value", 0),
    )


@lru_cache(maxsize=1)
def _get_weapon_registry() -> dict[str, Weapon]:
    """Build the weapon registry from YAML data.

    Returns
    -------
    dict[str, Weapon]
        Dictionary mapping weapon IDs to Weapon objects.
    """
    data = load_weapons()
    return {weapon_id: _parse_weapon(weapon_id, weapon_data)
            for weapon_id, weapon_data in data.items()}


def get_weapon(weapon_id: str) -> Weapon:
    """Get a weapon by ID.

    Parameters
    ----------
    weapon_id : str
        The weapon's unique identifier.

    Returns
    -------
    Weapon
        A copy of the weapon.

    Raises
    ------
    KeyError
        If weapon_id is not found.
    """
    return _get_weapon_registry()[weapon_id].model_copy(deep=True)


def list_weapons(category: WeaponCategory | None = None) -> list[str]:
    """List all available weapon IDs, optionally filtered by category.

    Parameters
    ----------
    category : WeaponCategory, optional
        Category to filter by (SIMPLE or MARTIAL).

    Returns
    -------
    list[str]
        List of weapon IDs.
    """
    registry = _get_weapon_registry()
    if category is None:
        return list(registry.keys())
    return [wid for wid, w in registry.items() if w.category == category]


def get_all_weapons(category: WeaponCategory | None = None) -> list[Weapon]:
    """Get all weapons, optionally filtered by category.

    Parameters
    ----------
    category : WeaponCategory, optional
        Category to filter by (SIMPLE or MARTIAL).

    Returns
    -------
    list[Weapon]
        List of weapon copies.
    """
    registry = _get_weapon_registry()
    weapons = list(registry.values())
    if category is not None:
        weapons = [w for w in weapons if w.category == category]
    return weapons
