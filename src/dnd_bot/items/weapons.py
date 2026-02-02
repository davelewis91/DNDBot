"""Weapon definitions for D&D 5e (2024 edition)."""

from .base import DamageType, Weapon, WeaponCategory, WeaponProperty

# Simple Melee Weapons
CLUB = Weapon(
    id="club",
    name="Club",
    damage_dice="1d4",
    damage_type=DamageType.BLUDGEONING,
    category=WeaponCategory.SIMPLE,
    properties=[WeaponProperty.LIGHT],
    weight=2.0,
    value=10,  # 1 sp = 10 cp
)

DAGGER = Weapon(
    id="dagger",
    name="Dagger",
    damage_dice="1d4",
    damage_type=DamageType.PIERCING,
    category=WeaponCategory.SIMPLE,
    properties=[WeaponProperty.FINESSE, WeaponProperty.LIGHT, WeaponProperty.THROWN],
    range_normal=20,
    range_long=60,
    weight=1.0,
    value=200,  # 2 gp
)

GREATCLUB = Weapon(
    id="greatclub",
    name="Greatclub",
    damage_dice="1d8",
    damage_type=DamageType.BLUDGEONING,
    category=WeaponCategory.SIMPLE,
    properties=[WeaponProperty.TWO_HANDED],
    weight=10.0,
    value=20,  # 2 sp
)

HANDAXE = Weapon(
    id="handaxe",
    name="Handaxe",
    damage_dice="1d6",
    damage_type=DamageType.SLASHING,
    category=WeaponCategory.SIMPLE,
    properties=[WeaponProperty.LIGHT, WeaponProperty.THROWN],
    range_normal=20,
    range_long=60,
    weight=2.0,
    value=500,  # 5 gp
)

JAVELIN = Weapon(
    id="javelin",
    name="Javelin",
    damage_dice="1d6",
    damage_type=DamageType.PIERCING,
    category=WeaponCategory.SIMPLE,
    properties=[WeaponProperty.THROWN],
    range_normal=30,
    range_long=120,
    weight=2.0,
    value=50,  # 5 sp
)

MACE = Weapon(
    id="mace",
    name="Mace",
    damage_dice="1d6",
    damage_type=DamageType.BLUDGEONING,
    category=WeaponCategory.SIMPLE,
    weight=4.0,
    value=500,  # 5 gp
)

QUARTERSTAFF = Weapon(
    id="quarterstaff",
    name="Quarterstaff",
    damage_dice="1d6",
    damage_type=DamageType.BLUDGEONING,
    category=WeaponCategory.SIMPLE,
    properties=[WeaponProperty.VERSATILE],
    versatile_dice="1d8",
    weight=4.0,
    value=20,  # 2 sp
)

SPEAR = Weapon(
    id="spear",
    name="Spear",
    damage_dice="1d6",
    damage_type=DamageType.PIERCING,
    category=WeaponCategory.SIMPLE,
    properties=[WeaponProperty.THROWN, WeaponProperty.VERSATILE],
    versatile_dice="1d8",
    range_normal=20,
    range_long=60,
    weight=3.0,
    value=100,  # 1 gp
)

# Simple Ranged Weapons
LIGHT_CROSSBOW = Weapon(
    id="light_crossbow",
    name="Light Crossbow",
    damage_dice="1d8",
    damage_type=DamageType.PIERCING,
    category=WeaponCategory.SIMPLE,
    properties=[WeaponProperty.AMMUNITION, WeaponProperty.LOADING, WeaponProperty.TWO_HANDED],
    range_normal=80,
    range_long=320,
    weight=5.0,
    value=2500,  # 25 gp
)

SHORTBOW = Weapon(
    id="shortbow",
    name="Shortbow",
    damage_dice="1d6",
    damage_type=DamageType.PIERCING,
    category=WeaponCategory.SIMPLE,
    properties=[WeaponProperty.AMMUNITION, WeaponProperty.TWO_HANDED],
    range_normal=80,
    range_long=320,
    weight=2.0,
    value=2500,  # 25 gp
)

# Martial Melee Weapons
BATTLEAXE = Weapon(
    id="battleaxe",
    name="Battleaxe",
    damage_dice="1d8",
    damage_type=DamageType.SLASHING,
    category=WeaponCategory.MARTIAL,
    properties=[WeaponProperty.VERSATILE],
    versatile_dice="1d10",
    weight=4.0,
    value=1000,  # 10 gp
)

GREATSWORD = Weapon(
    id="greatsword",
    name="Greatsword",
    damage_dice="2d6",
    damage_type=DamageType.SLASHING,
    category=WeaponCategory.MARTIAL,
    properties=[WeaponProperty.HEAVY, WeaponProperty.TWO_HANDED],
    weight=6.0,
    value=5000,  # 50 gp
)

GREATAXE = Weapon(
    id="greataxe",
    name="Greataxe",
    damage_dice="1d12",
    damage_type=DamageType.SLASHING,
    category=WeaponCategory.MARTIAL,
    properties=[WeaponProperty.HEAVY, WeaponProperty.TWO_HANDED],
    weight=7.0,
    value=3000,  # 30 gp
)

LONGSWORD = Weapon(
    id="longsword",
    name="Longsword",
    damage_dice="1d8",
    damage_type=DamageType.SLASHING,
    category=WeaponCategory.MARTIAL,
    properties=[WeaponProperty.VERSATILE],
    versatile_dice="1d10",
    weight=3.0,
    value=1500,  # 15 gp
)

RAPIER = Weapon(
    id="rapier",
    name="Rapier",
    damage_dice="1d8",
    damage_type=DamageType.PIERCING,
    category=WeaponCategory.MARTIAL,
    properties=[WeaponProperty.FINESSE],
    weight=2.0,
    value=2500,  # 25 gp
)

SCIMITAR = Weapon(
    id="scimitar",
    name="Scimitar",
    damage_dice="1d6",
    damage_type=DamageType.SLASHING,
    category=WeaponCategory.MARTIAL,
    properties=[WeaponProperty.FINESSE, WeaponProperty.LIGHT],
    weight=3.0,
    value=2500,  # 25 gp
)

SHORTSWORD = Weapon(
    id="shortsword",
    name="Shortsword",
    damage_dice="1d6",
    damage_type=DamageType.PIERCING,
    category=WeaponCategory.MARTIAL,
    properties=[WeaponProperty.FINESSE, WeaponProperty.LIGHT],
    weight=2.0,
    value=1000,  # 10 gp
)

WARHAMMER = Weapon(
    id="warhammer",
    name="Warhammer",
    damage_dice="1d8",
    damage_type=DamageType.BLUDGEONING,
    category=WeaponCategory.MARTIAL,
    properties=[WeaponProperty.VERSATILE],
    versatile_dice="1d10",
    weight=2.0,
    value=1500,  # 15 gp
)

# Martial Ranged Weapons
HAND_CROSSBOW = Weapon(
    id="hand_crossbow",
    name="Hand Crossbow",
    damage_dice="1d6",
    damage_type=DamageType.PIERCING,
    category=WeaponCategory.MARTIAL,
    properties=[WeaponProperty.AMMUNITION, WeaponProperty.LIGHT, WeaponProperty.LOADING],
    range_normal=30,
    range_long=120,
    weight=3.0,
    value=7500,  # 75 gp
)

HEAVY_CROSSBOW = Weapon(
    id="heavy_crossbow",
    name="Heavy Crossbow",
    damage_dice="1d10",
    damage_type=DamageType.PIERCING,
    category=WeaponCategory.MARTIAL,
    properties=[
        WeaponProperty.AMMUNITION,
        WeaponProperty.HEAVY,
        WeaponProperty.LOADING,
        WeaponProperty.TWO_HANDED,
    ],
    range_normal=100,
    range_long=400,
    weight=18.0,
    value=5000,  # 50 gp
)

LONGBOW = Weapon(
    id="longbow",
    name="Longbow",
    damage_dice="1d8",
    damage_type=DamageType.PIERCING,
    category=WeaponCategory.MARTIAL,
    properties=[WeaponProperty.AMMUNITION, WeaponProperty.HEAVY, WeaponProperty.TWO_HANDED],
    range_normal=150,
    range_long=600,
    weight=2.0,
    value=5000,  # 50 gp
)


# Weapon registry
WEAPON_REGISTRY: dict[str, Weapon] = {
    # Simple Melee
    "club": CLUB,
    "dagger": DAGGER,
    "greatclub": GREATCLUB,
    "handaxe": HANDAXE,
    "javelin": JAVELIN,
    "mace": MACE,
    "quarterstaff": QUARTERSTAFF,
    "spear": SPEAR,
    # Simple Ranged
    "light_crossbow": LIGHT_CROSSBOW,
    "shortbow": SHORTBOW,
    # Martial Melee
    "battleaxe": BATTLEAXE,
    "greatsword": GREATSWORD,
    "greataxe": GREATAXE,
    "longsword": LONGSWORD,
    "rapier": RAPIER,
    "scimitar": SCIMITAR,
    "shortsword": SHORTSWORD,
    "warhammer": WARHAMMER,
    # Martial Ranged
    "hand_crossbow": HAND_CROSSBOW,
    "heavy_crossbow": HEAVY_CROSSBOW,
    "longbow": LONGBOW,
}


def get_weapon(weapon_id: str) -> Weapon:
    """Get a weapon by ID.

    Args:
        weapon_id: The weapon's unique identifier

    Returns:
        A copy of the weapon

    Raises:
        KeyError: If weapon_id is not found
    """
    return WEAPON_REGISTRY[weapon_id].model_copy(deep=True)


def list_weapons(category: WeaponCategory | None = None) -> list[Weapon]:
    """List all available weapons, optionally filtered by category.

    Args:
        category: Optional category to filter by (SIMPLE or MARTIAL)

    Returns:
        List of weapons
    """
    weapons = list(WEAPON_REGISTRY.values())
    if category is not None:
        weapons = [w for w in weapons if w.category == category]
    return weapons
