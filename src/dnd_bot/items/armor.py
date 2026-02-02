"""Armor definitions for D&D 5e (2024 edition)."""

from .base import Armor, ArmorType, Shield

# Light Armor
PADDED = Armor(
    id="padded",
    name="Padded Armor",
    description="Quilted layers of cloth and batting.",
    armor_type=ArmorType.LIGHT,
    base_ac=11,
    max_dex_bonus=None,  # No cap on DEX
    stealth_disadvantage=True,
    weight=8.0,
    value=500,  # 5 gp
)

LEATHER = Armor(
    id="leather",
    name="Leather Armor",
    description="Leather breastplate and shoulder protectors.",
    armor_type=ArmorType.LIGHT,
    base_ac=11,
    max_dex_bonus=None,
    stealth_disadvantage=False,
    weight=10.0,
    value=1000,  # 10 gp
)

STUDDED_LEATHER = Armor(
    id="studded_leather",
    name="Studded Leather",
    description="Leather armor reinforced with close-set rivets or spikes.",
    armor_type=ArmorType.LIGHT,
    base_ac=12,
    max_dex_bonus=None,
    stealth_disadvantage=False,
    weight=13.0,
    value=4500,  # 45 gp
)

# Medium Armor
HIDE = Armor(
    id="hide",
    name="Hide Armor",
    description="Crude armor made from thick furs and pelts.",
    armor_type=ArmorType.MEDIUM,
    base_ac=12,
    max_dex_bonus=2,
    stealth_disadvantage=False,
    weight=12.0,
    value=1000,  # 10 gp
)

CHAIN_SHIRT = Armor(
    id="chain_shirt",
    name="Chain Shirt",
    description="Interlocking metal rings worn between layers of clothing.",
    armor_type=ArmorType.MEDIUM,
    base_ac=13,
    max_dex_bonus=2,
    stealth_disadvantage=False,
    weight=20.0,
    value=5000,  # 50 gp
)

SCALE_MAIL = Armor(
    id="scale_mail",
    name="Scale Mail",
    description="Coat and leggings covered with overlapping metal scales.",
    armor_type=ArmorType.MEDIUM,
    base_ac=14,
    max_dex_bonus=2,
    stealth_disadvantage=True,
    weight=45.0,
    value=5000,  # 50 gp
)

BREASTPLATE = Armor(
    id="breastplate",
    name="Breastplate",
    description="Fitted metal chest piece worn with flexible leather.",
    armor_type=ArmorType.MEDIUM,
    base_ac=14,
    max_dex_bonus=2,
    stealth_disadvantage=False,
    weight=20.0,
    value=40000,  # 400 gp
)

HALF_PLATE = Armor(
    id="half_plate",
    name="Half Plate",
    description="Metal plates covering vital areas with chain and leather.",
    armor_type=ArmorType.MEDIUM,
    base_ac=15,
    max_dex_bonus=2,
    stealth_disadvantage=True,
    weight=40.0,
    value=75000,  # 750 gp
)

# Heavy Armor
RING_MAIL = Armor(
    id="ring_mail",
    name="Ring Mail",
    description="Leather armor with heavy rings sewn into it.",
    armor_type=ArmorType.HEAVY,
    base_ac=14,
    max_dex_bonus=0,
    stealth_disadvantage=True,
    weight=40.0,
    value=3000,  # 30 gp
)

CHAIN_MAIL = Armor(
    id="chain_mail",
    name="Chain Mail",
    description="Interlocking metal rings with a layer of quilted fabric.",
    armor_type=ArmorType.HEAVY,
    base_ac=16,
    max_dex_bonus=0,
    strength_required=13,
    stealth_disadvantage=True,
    weight=55.0,
    value=7500,  # 75 gp
)

SPLINT = Armor(
    id="splint",
    name="Splint Armor",
    description="Metal strips riveted to a backing of leather.",
    armor_type=ArmorType.HEAVY,
    base_ac=17,
    max_dex_bonus=0,
    strength_required=15,
    stealth_disadvantage=True,
    weight=60.0,
    value=20000,  # 200 gp
)

PLATE = Armor(
    id="plate",
    name="Plate Armor",
    description="Shaped, interlocking metal plates covering the entire body.",
    armor_type=ArmorType.HEAVY,
    base_ac=18,
    max_dex_bonus=0,
    strength_required=15,
    stealth_disadvantage=True,
    weight=65.0,
    value=150000,  # 1500 gp
)

# Shields
SHIELD = Shield(
    id="shield",
    name="Shield",
    description="A wooden or metal shield carried in one hand.",
    ac_bonus=2,
    weight=6.0,
    value=1000,  # 10 gp
)


# Armor registry
ARMOR_REGISTRY: dict[str, Armor] = {
    # Light
    "padded": PADDED,
    "leather": LEATHER,
    "studded_leather": STUDDED_LEATHER,
    # Medium
    "hide": HIDE,
    "chain_shirt": CHAIN_SHIRT,
    "scale_mail": SCALE_MAIL,
    "breastplate": BREASTPLATE,
    "half_plate": HALF_PLATE,
    # Heavy
    "ring_mail": RING_MAIL,
    "chain_mail": CHAIN_MAIL,
    "splint": SPLINT,
    "plate": PLATE,
}

SHIELD_REGISTRY: dict[str, Shield] = {
    "shield": SHIELD,
}


def get_armor(armor_id: str) -> Armor:
    """Get armor by ID.

    Args:
        armor_id: The armor's unique identifier

    Returns:
        A copy of the armor

    Raises:
        KeyError: If armor_id is not found
    """
    return ARMOR_REGISTRY[armor_id].model_copy(deep=True)


def get_shield(shield_id: str) -> Shield:
    """Get shield by ID.

    Args:
        shield_id: The shield's unique identifier

    Returns:
        A copy of the shield

    Raises:
        KeyError: If shield_id is not found
    """
    return SHIELD_REGISTRY[shield_id].model_copy(deep=True)


def list_armor(armor_type: ArmorType | None = None) -> list[Armor]:
    """List all available armor, optionally filtered by type.

    Args:
        armor_type: Optional type to filter by (LIGHT, MEDIUM, HEAVY)

    Returns:
        List of armor
    """
    armor = list(ARMOR_REGISTRY.values())
    if armor_type is not None:
        armor = [a for a in armor if a.armor_type == armor_type]
    return armor
