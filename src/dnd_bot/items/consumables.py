"""Consumable item definitions for D&D 5e (2024 edition)."""

from .base import Ammunition, Consumable, Rarity

# Potions
POTION_OF_HEALING = Consumable(
    id="potion_of_healing",
    name="Potion of Healing",
    description="A red liquid that glimmers when agitated. Heals 2d4+2 HP.",
    effect="Regain 2d4+2 hit points when you drink this potion.",
    healing_dice="2d4+2",
    rarity=Rarity.COMMON,
    weight=0.5,
    value=5000,  # 50 gp
)

POTION_OF_GREATER_HEALING = Consumable(
    id="potion_of_greater_healing",
    name="Potion of Greater Healing",
    description="A red liquid that glimmers when agitated. Heals 4d4+4 HP.",
    effect="Regain 4d4+4 hit points when you drink this potion.",
    healing_dice="4d4+4",
    rarity=Rarity.UNCOMMON,
    weight=0.5,
    value=15000,  # 150 gp
)

POTION_OF_SUPERIOR_HEALING = Consumable(
    id="potion_of_superior_healing",
    name="Potion of Superior Healing",
    description="A red liquid that glimmers when agitated. Heals 8d4+8 HP.",
    effect="Regain 8d4+8 hit points when you drink this potion.",
    healing_dice="8d4+8",
    rarity=Rarity.RARE,
    weight=0.5,
    value=50000,  # 500 gp
)

POTION_OF_SUPREME_HEALING = Consumable(
    id="potion_of_supreme_healing",
    name="Potion of Supreme Healing",
    description="A red liquid that glimmers when agitated. Heals 10d4+20 HP.",
    effect="Regain 10d4+20 hit points when you drink this potion.",
    healing_dice="10d4+20",
    rarity=Rarity.VERY_RARE,
    weight=0.5,
    value=135000,  # 1350 gp
)

ANTITOXIN = Consumable(
    id="antitoxin",
    name="Antitoxin",
    description="A creature that drinks this gains advantage on saves vs poison for 1 hour.",
    effect="Advantage on saving throws against poison for 1 hour.",
    rarity=Rarity.COMMON,
    weight=0.0,
    value=5000,  # 50 gp
)

# Ammunition
ARROWS = Ammunition(
    id="arrows",
    name="Arrows (20)",
    description="A quiver of 20 arrows for bows.",
    quantity=20,
    weapon_types=["shortbow", "longbow"],
    weight=1.0,
    value=100,  # 1 gp
)

BOLTS = Ammunition(
    id="bolts",
    name="Crossbow Bolts (20)",
    description="A case of 20 bolts for crossbows.",
    quantity=20,
    weapon_types=["light_crossbow", "heavy_crossbow", "hand_crossbow"],
    weight=1.5,
    value=100,  # 1 gp
)

SLING_BULLETS = Ammunition(
    id="sling_bullets",
    name="Sling Bullets (20)",
    description="A pouch of 20 sling bullets.",
    quantity=20,
    weapon_types=["sling"],
    weight=1.5,
    value=4,  # 4 cp
)


# Consumable registries
CONSUMABLE_REGISTRY: dict[str, Consumable] = {
    "potion_of_healing": POTION_OF_HEALING,
    "potion_of_greater_healing": POTION_OF_GREATER_HEALING,
    "potion_of_superior_healing": POTION_OF_SUPERIOR_HEALING,
    "potion_of_supreme_healing": POTION_OF_SUPREME_HEALING,
    "antitoxin": ANTITOXIN,
}

AMMUNITION_REGISTRY: dict[str, Ammunition] = {
    "arrows": ARROWS,
    "bolts": BOLTS,
    "sling_bullets": SLING_BULLETS,
}


def get_consumable(consumable_id: str) -> Consumable:
    """Get a consumable by ID.

    Args:
        consumable_id: The consumable's unique identifier

    Returns:
        A copy of the consumable

    Raises:
        KeyError: If consumable_id is not found
    """
    return CONSUMABLE_REGISTRY[consumable_id].model_copy(deep=True)


def get_ammunition(ammo_id: str) -> Ammunition:
    """Get ammunition by ID.

    Args:
        ammo_id: The ammunition's unique identifier

    Returns:
        A copy of the ammunition

    Raises:
        KeyError: If ammo_id is not found
    """
    return AMMUNITION_REGISTRY[ammo_id].model_copy(deep=True)


def list_potions() -> list[Consumable]:
    """List all healing potions."""
    return [c for c in CONSUMABLE_REGISTRY.values() if c.healing_dice is not None]
