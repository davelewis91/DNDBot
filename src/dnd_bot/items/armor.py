"""Armor definitions for D&D 5e (2024 edition)."""

from functools import lru_cache

from dnd_bot.data import load_armor, load_shields

from .base import Armor, ArmorType, Shield


def _parse_armor(armor_id: str, data: dict) -> Armor:
    """Parse YAML data into an Armor model.

    Parameters
    ----------
    armor_id : str
        The armor's unique identifier.
    data : dict
        Raw YAML data for the armor.

    Returns
    -------
    Armor
        The parsed armor model.
    """
    return Armor(
        id=armor_id,
        name=data["name"],
        description=data.get("description", ""),
        armor_type=ArmorType(data["armor_type"]),
        base_ac=data["base_ac"],
        max_dex_bonus=data.get("max_dex_bonus"),
        strength_required=data.get("strength_required"),
        stealth_disadvantage=data.get("stealth_disadvantage", False),
        weight=data.get("weight", 0.0),
        value=data.get("value", 0),
    )


def _parse_shield(shield_id: str, data: dict) -> Shield:
    """Parse YAML data into a Shield model.

    Parameters
    ----------
    shield_id : str
        The shield's unique identifier.
    data : dict
        Raw YAML data for the shield.

    Returns
    -------
    Shield
        The parsed shield model.
    """
    return Shield(
        id=shield_id,
        name=data["name"],
        description=data.get("description", ""),
        ac_bonus=data.get("ac_bonus", 2),
        weight=data.get("weight", 0.0),
        value=data.get("value", 0),
    )


@lru_cache(maxsize=1)
def _get_armor_registry() -> dict[str, Armor]:
    """Build the armor registry from YAML data."""
    data = load_armor()
    return {armor_id: _parse_armor(armor_id, armor_data)
            for armor_id, armor_data in data.items()}


@lru_cache(maxsize=1)
def _get_shield_registry() -> dict[str, Shield]:
    """Build the shield registry from YAML data."""
    data = load_shields()
    return {shield_id: _parse_shield(shield_id, shield_data)
            for shield_id, shield_data in data.items()}


def get_armor(armor_id: str) -> Armor:
    """Get armor by ID.

    Parameters
    ----------
    armor_id : str
        The armor's unique identifier.

    Returns
    -------
    Armor
        A copy of the armor.

    Raises
    ------
    KeyError
        If armor_id is not found.
    """
    return _get_armor_registry()[armor_id].model_copy(deep=True)


def get_shield(shield_id: str) -> Shield:
    """Get shield by ID.

    Parameters
    ----------
    shield_id : str
        The shield's unique identifier.

    Returns
    -------
    Shield
        A copy of the shield.

    Raises
    ------
    KeyError
        If shield_id is not found.
    """
    return _get_shield_registry()[shield_id].model_copy(deep=True)


def list_armor(armor_type: ArmorType | None = None) -> list[str]:
    """List all available armor IDs, optionally filtered by type.

    Parameters
    ----------
    armor_type : ArmorType, optional
        Type to filter by (LIGHT, MEDIUM, HEAVY).

    Returns
    -------
    list[str]
        List of armor IDs.
    """
    registry = _get_armor_registry()
    if armor_type is None:
        return list(registry.keys())
    return [aid for aid, a in registry.items() if a.armor_type == armor_type]


def list_shields() -> list[str]:
    """List all available shield IDs.

    Returns
    -------
    list[str]
        List of shield IDs.
    """
    return list(_get_shield_registry().keys())


def get_all_armor(armor_type: ArmorType | None = None) -> list[Armor]:
    """Get all armor, optionally filtered by type.

    Parameters
    ----------
    armor_type : ArmorType, optional
        Type to filter by (LIGHT, MEDIUM, HEAVY).

    Returns
    -------
    list[Armor]
        List of armor copies.
    """
    registry = _get_armor_registry()
    armor = list(registry.values())
    if armor_type is not None:
        armor = [a for a in armor if a.armor_type == armor_type]
    return armor
