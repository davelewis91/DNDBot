"""Character class definitions for D&D 5e (2024 edition).

MVP: Martial classes only (Fighter, Rogue, Barbarian, Monk).
"""

from enum import Enum
from functools import lru_cache
from typing import Any

from pydantic import BaseModel, Field

from dnd_bot.data import load_classes

from .abilities import Ability
from .resources import RestType
from .skills import Skill


class ClassName(str, Enum):
    """Available character classes (martial only for MVP)."""

    FIGHTER = "fighter"
    ROGUE = "rogue"
    BARBARIAN = "barbarian"
    MONK = "monk"


class HitDie(int, Enum):
    """Hit die types."""

    D6 = 6
    D8 = 8
    D10 = 10
    D12 = 12


class FeatureMechanicType(str, Enum):
    """Types of class feature mechanics."""

    PASSIVE = "passive"
    RESOURCE = "resource"
    TOGGLE = "toggle"
    REACTION = "reaction"


class FeatureMechanic(BaseModel):
    """Mechanical data for a class feature."""

    mechanic_type: FeatureMechanicType
    resource_name: str | None = Field(
        default=None,
        description="Name of the resource to track (for RESOURCE/TOGGLE types)",
    )
    uses_per_rest: int | None = Field(
        default=None,
        description="Number of uses per rest (for RESOURCE types)",
    )
    uses_per_rest_formula: str | None = Field(
        default=None,
        description="Formula for uses (e.g., 'level' for Monk Focus Points)",
    )
    recover_on: RestType | None = Field(
        default=None,
        description="When the resource recovers (SHORT or LONG)",
    )
    dice: str | None = Field(
        default=None,
        description="Dice to roll (e.g., '1d10' for Second Wind)",
    )
    dice_per_level: str | None = Field(
        default=None,
        description="Dice that scale with level (e.g., '1d6' for Sneak Attack per 2 levels)",
    )
    bonus: int | None = Field(
        default=None,
        description="Static bonus value",
    )
    extra_data: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional mechanic-specific data",
    )


class ClassFeature(BaseModel):
    """A class feature gained at a specific level."""

    name: str
    level: int = Field(ge=1, le=20)
    description: str
    mechanic: FeatureMechanic | None = Field(
        default=None,
        description="Mechanical data for features with game effects",
    )


class CharacterClass(BaseModel):
    """Character class definition with features and proficiencies."""

    name: ClassName
    hit_die: HitDie
    saving_throw_proficiencies: list[Ability]
    skill_choices: list[Skill]
    num_skill_choices: int = Field(ge=1, le=4)
    armor_proficiencies: list[str] = Field(default_factory=list)
    weapon_proficiencies: list[str] = Field(default_factory=list)
    features: list[ClassFeature] = Field(default_factory=list)

    def get_features_at_level(self, level: int) -> list[ClassFeature]:
        """Get all features gained at or before a specific level."""
        return [f for f in self.features if f.level <= level]


def _parse_mechanic(data: dict | None) -> FeatureMechanic | None:
    """Parse mechanic data from YAML."""
    if data is None:
        return None

    recover_on = None
    if "recover_on" in data:
        recover_on = RestType.SHORT if data["recover_on"] == "short" else RestType.LONG

    return FeatureMechanic(
        mechanic_type=FeatureMechanicType(data["type"]),
        resource_name=data.get("resource_name"),
        uses_per_rest=data.get("uses_per_rest"),
        uses_per_rest_formula=data.get("uses_per_rest_formula"),
        recover_on=recover_on,
        dice=data.get("dice"),
        dice_per_level=data.get("dice_per_level"),
        bonus=data.get("bonus"),
        extra_data=data.get("extra_data", {}),
    )


def _parse_feature(data: dict) -> ClassFeature:
    """Parse a class feature from YAML."""
    return ClassFeature(
        name=data["name"],
        level=data["level"],
        description=data["description"],
        mechanic=_parse_mechanic(data.get("mechanic")),
    )


def _parse_class(class_name: str, data: dict) -> CharacterClass:
    """Parse a character class from YAML data."""
    saving_throws = [Ability(s) for s in data["saving_throws"]]
    skill_choices = [Skill(s) for s in data["skill_choices"]]
    features = [_parse_feature(f) for f in data.get("features", [])]

    return CharacterClass(
        name=ClassName(class_name),
        hit_die=HitDie(data["hit_die"]),
        saving_throw_proficiencies=saving_throws,
        skill_choices=skill_choices,
        num_skill_choices=data["num_skill_choices"],
        armor_proficiencies=data.get("armor_proficiencies", []),
        weapon_proficiencies=data.get("weapon_proficiencies", []),
        features=features,
    )


@lru_cache(maxsize=1)
def _get_class_registry() -> dict[ClassName, CharacterClass]:
    """Build the class registry from YAML data."""
    classes = {}
    raw_data = load_classes()
    for class_name, class_data in raw_data.items():
        classes[ClassName(class_name)] = _parse_class(class_name, class_data)
    return classes


def get_class(name: ClassName) -> CharacterClass:
    """Get a class definition by name.

    Parameters
    ----------
    name : ClassName
        The class to retrieve.

    Returns
    -------
    CharacterClass
        A deep copy of the class definition.
    """
    return _get_class_registry()[name].model_copy(deep=True)


def list_classes() -> list[str]:
    """List all available class IDs.

    Returns
    -------
    list[str]
        List of class identifiers.
    """
    return [c.value for c in _get_class_registry().keys()]


def get_resource_features(char_class: CharacterClass, level: int) -> list[ClassFeature]:
    """Get all features with resource mechanics at or below the given level.

    Returns features that have RESOURCE or TOGGLE mechanic types, which
    need to be registered in the character's ResourcePool.
    """
    resource_types = {FeatureMechanicType.RESOURCE, FeatureMechanicType.TOGGLE}
    return [
        f for f in char_class.features
        if f.level <= level
        and f.mechanic is not None
        and f.mechanic.mechanic_type in resource_types
    ]


def calculate_resource_uses(feature: ClassFeature, level: int) -> int:
    """Calculate the number of uses for a resource feature at a given level.

    Parameters
    ----------
    feature : ClassFeature
        The ClassFeature with resource mechanics.
    level : int
        The character's level.

    Returns
    -------
    int
        Number of uses for the resource.
    """
    if feature.mechanic is None:
        return 0

    if feature.mechanic.uses_per_rest is not None:
        return feature.mechanic.uses_per_rest

    if feature.mechanic.uses_per_rest_formula is not None:
        formula = feature.mechanic.uses_per_rest_formula
        if formula == "level":
            return level
        if formula.startswith("level/"):
            divisor = int(formula.split("/")[1])
            return max(1, level // divisor)

    return 1


def get_sneak_attack_dice(level: int) -> int:
    """Calculate number of Sneak Attack dice for a given Rogue level.

    Sneak Attack starts at 1d6 at level 1 and gains an additional d6
    at every odd level (3, 5, 7, 9, 11, 13, 15, 17, 19).
    """
    return (level + 1) // 2


def get_rage_damage_bonus(level: int) -> int:
    """Calculate Rage damage bonus for a given Barbarian level."""
    if level >= 16:
        return 4
    if level >= 9:
        return 3
    return 2


def get_rage_uses(level: int) -> int:
    """Calculate number of Rage uses for a given Barbarian level."""
    if level >= 17:
        return 6
    if level >= 12:
        return 5
    if level >= 6:
        return 4
    if level >= 3:
        return 3
    return 2


def get_martial_arts_die(level: int) -> str:
    """Calculate Martial Arts die for a given Monk level."""
    if level >= 17:
        return "1d12"
    if level >= 11:
        return "1d10"
    if level >= 5:
        return "1d8"
    return "1d6"
