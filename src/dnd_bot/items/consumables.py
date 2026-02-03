"""Consumable item definitions for D&D 5e (2024 edition)."""

from functools import lru_cache

from dnd_bot.data import load_ammunition, load_consumables

from .base import Ammunition, Consumable, Rarity


def _parse_consumable(consumable_id: str, data: dict) -> Consumable:
    """Parse YAML data into a Consumable model.

    Parameters
    ----------
    consumable_id : str
        The consumable's unique identifier.
    data : dict
        Raw YAML data for the consumable.

    Returns
    -------
    Consumable
        The parsed consumable model.
    """
    return Consumable(
        id=consumable_id,
        name=data["name"],
        description=data.get("description", ""),
        effect=data.get("effect", ""),
        healing_dice=data.get("healing_dice"),
        rarity=Rarity(data.get("rarity", "common")),
        weight=data.get("weight", 0.0),
        value=data.get("value", 0),
    )


def _parse_ammunition(ammo_id: str, data: dict) -> Ammunition:
    """Parse YAML data into an Ammunition model.

    Parameters
    ----------
    ammo_id : str
        The ammunition's unique identifier.
    data : dict
        Raw YAML data for the ammunition.

    Returns
    -------
    Ammunition
        The parsed ammunition model.
    """
    return Ammunition(
        id=ammo_id,
        name=data["name"],
        description=data.get("description", ""),
        quantity=data.get("quantity", 20),
        weapon_types=data.get("weapon_types", []),
        weight=data.get("weight", 0.0),
        value=data.get("value", 0),
    )


@lru_cache(maxsize=1)
def _get_consumable_registry() -> dict[str, Consumable]:
    """Build the consumable registry from YAML data."""
    data = load_consumables()
    return {consumable_id: _parse_consumable(consumable_id, consumable_data)
            for consumable_id, consumable_data in data.items()}


@lru_cache(maxsize=1)
def _get_ammunition_registry() -> dict[str, Ammunition]:
    """Build the ammunition registry from YAML data."""
    data = load_ammunition()
    return {ammo_id: _parse_ammunition(ammo_id, ammo_data)
            for ammo_id, ammo_data in data.items()}


def get_consumable(consumable_id: str) -> Consumable:
    """Get a consumable by ID.

    Parameters
    ----------
    consumable_id : str
        The consumable's unique identifier.

    Returns
    -------
    Consumable
        A copy of the consumable.

    Raises
    ------
    KeyError
        If consumable_id is not found.
    """
    return _get_consumable_registry()[consumable_id].model_copy(deep=True)


def get_ammunition(ammo_id: str) -> Ammunition:
    """Get ammunition by ID.

    Parameters
    ----------
    ammo_id : str
        The ammunition's unique identifier.

    Returns
    -------
    Ammunition
        A copy of the ammunition.

    Raises
    ------
    KeyError
        If ammo_id is not found.
    """
    return _get_ammunition_registry()[ammo_id].model_copy(deep=True)


def list_consumables() -> list[str]:
    """List all available consumable IDs.

    Returns
    -------
    list[str]
        List of consumable IDs.
    """
    return list(_get_consumable_registry().keys())


def list_ammunition() -> list[str]:
    """List all available ammunition IDs.

    Returns
    -------
    list[str]
        List of ammunition IDs.
    """
    return list(_get_ammunition_registry().keys())


def list_potions() -> list[Consumable]:
    """List all healing potions.

    Returns
    -------
    list[Consumable]
        List of consumables with healing_dice set.
    """
    return [c for c in _get_consumable_registry().values() if c.healing_dice is not None]


def get_all_consumables() -> list[Consumable]:
    """Get all consumables.

    Returns
    -------
    list[Consumable]
        List of all consumables.
    """
    return list(_get_consumable_registry().values())


def get_all_ammunition() -> list[Ammunition]:
    """Get all ammunition.

    Returns
    -------
    list[Ammunition]
        List of all ammunition.
    """
    return list(_get_ammunition_registry().values())
