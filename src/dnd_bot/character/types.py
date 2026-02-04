"""Character type union and factory functions.

This module provides the AnyCharacter discriminated union type for serialization
and a factory function for creating characters by class type string.
"""

from __future__ import annotations

from typing import Annotated, Union

from pydantic import Field, TypeAdapter

from .abilities import AbilityScores
from .background import Background
from .barbarian import Barbarian, Berserker
from .fighter import Champion, Fighter
from .monk import Monk, OpenHand
from .rogue import Rogue, Thief
from .skills import Skill
from .species import SpeciesName, get_species

# Discriminated union of all character types for serialization
AnyCharacter = Annotated[
    Union[  # noqa: UP007
        # Base classes first, then subclasses
        Fighter,
        Champion,
        Barbarian,
        Berserker,
        Rogue,
        Thief,
        Monk,
        OpenHand,
    ],
    Field(discriminator="class_type"),
]

# TypeAdapter for serialization/deserialization
_character_adapter = TypeAdapter(AnyCharacter)

# Map of class_type strings to their classes
CHARACTER_CLASSES: dict[str, type] = {
    "fighter": Fighter,
    "champion": Champion,
    "barbarian": Barbarian,
    "berserker": Berserker,
    "rogue": Rogue,
    "thief": Thief,
    "monk": Monk,
    "openhand": OpenHand,
}


def create_character(
    name: str,
    class_type: str,
    species_name: SpeciesName,
    level: int = 1,
    ability_scores: AbilityScores | None = None,
    skill_proficiencies: list[Skill] | None = None,
    background: Background | None = None,
) -> AnyCharacter:
    """Factory function to create a new character with sensible defaults.

    Parameters
    ----------
    name : str
        Character name.
    class_type : str
        Character class type (e.g., "fighter", "champion", "rogue").
    species_name : SpeciesName
        Character species.
    level : int, optional
        Starting level (default 1).
    ability_scores : AbilityScores, optional
        Custom ability scores.
    skill_proficiencies : list[Skill], optional
        List of skill proficiencies.
    background : Background, optional
        Background information.

    Returns
    -------
    AnyCharacter
        A new character instance of the appropriate class.

    Raises
    ------
    ValueError
        If the class_type is not recognized.
    """
    cls = CHARACTER_CLASSES.get(class_type.lower())
    if cls is None:
        valid_types = ", ".join(sorted(CHARACTER_CLASSES.keys()))
        raise ValueError(f"Unknown class_type: {class_type}. Valid types: {valid_types}")

    species = get_species(species_name)

    character = cls(
        name=name,
        level=level,
        ability_scores=ability_scores or AbilityScores(),
        species=species,
        background=background or Background(),
    )

    # Apply skill proficiencies
    if skill_proficiencies:
        for skill in skill_proficiencies:
            character.skills.set_proficiency(skill)

    # Recalculate HP after all modifiers are set
    character.max_hp = character.calculate_max_hp()
    character.current_hp = character.max_hp

    return character


def validate_character(data: dict) -> AnyCharacter:
    """Validate and instantiate a character from a dictionary.

    Uses pydantic's discriminated union to automatically select the
    correct class based on the class_type field.

    Parameters
    ----------
    data : dict
        Character data with class_type discriminator.

    Returns
    -------
    AnyCharacter
        The validated character instance.
    """
    return _character_adapter.validate_python(data)


def list_class_types() -> list[str]:
    """List all available class type identifiers.

    Returns
    -------
    list[str]
        Sorted list of class type strings (e.g., ["barbarian", "berserker", ...]).
    """
    return sorted(CHARACTER_CLASSES.keys())


def get_character_class(class_type: str) -> type:
    """Get the character class for a given type string.

    Parameters
    ----------
    class_type : str
        The class type identifier.

    Returns
    -------
    type
        The character class.

    Raises
    ------
    ValueError
        If the class_type is not recognized.
    """
    cls = CHARACTER_CLASSES.get(class_type.lower())
    if cls is None:
        valid_types = ", ".join(sorted(CHARACTER_CLASSES.keys()))
        raise ValueError(f"Unknown class_type: {class_type}. Valid types: {valid_types}")
    return cls
