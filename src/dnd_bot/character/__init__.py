"""D&D character system.

This module provides a complete D&D 5e (2024 edition) character representation
with inheritance-based class hierarchy, skills, species, backgrounds, and YAML persistence.
"""

from .abilities import Ability, AbilityBonus, AbilityScores, calculate_modifier
from .background import Background, Motivation, PersonalityTraits
from .barbarian import Barbarian, Berserker, get_rage_damage_bonus, get_rage_uses
from .base import (
    Character,
    ClassFeature,
    DeathSaveOutcome,
    DeathSaveResult,
    DeathSaves,
    Equipment,
    FeatureMechanic,
    FeatureMechanicType,
    RestResult,
)
from .conditions import ActiveCondition, Condition, ConditionManager
from .exhaustion import Exhaustion
from .fighter import Champion, Fighter
from .monk import Monk, OpenHand, get_martial_arts_die
from .resources import HitDice, Resource, ResourcePool, RestType
from .rogue import Rogue, Thief, get_sneak_attack_dice
from .skills import (
    Skill,
    SkillProficiency,
    SkillSet,
    get_proficiency_bonus,
    get_skill_ability,
)
from .species import (
    CreatureType,
    Size,
    Species,
    SpeciesName,
    Trait,
    get_all_species,
    get_species,
    list_species,
)
from .storage import delete_character, list_characters, load_character, save_character
from .types import (
    CHARACTER_CLASSES,
    AnyCharacter,
    create_character,
    get_character_class,
    list_class_types,
    validate_character,
)

__all__ = [
    # Abilities
    "Ability",
    "AbilityBonus",
    "AbilityScores",
    "calculate_modifier",
    # Skills
    "Skill",
    "SkillProficiency",
    "SkillSet",
    "get_proficiency_bonus",
    "get_skill_ability",
    # Species
    "CreatureType",
    "Size",
    "Species",
    "SpeciesName",
    "Trait",
    "get_all_species",
    "get_species",
    "list_species",
    # Background
    "Background",
    "Motivation",
    "PersonalityTraits",
    # Conditions
    "ActiveCondition",
    "Condition",
    "ConditionManager",
    # Exhaustion
    "Exhaustion",
    # Resources
    "HitDice",
    "Resource",
    "ResourcePool",
    "RestType",
    # Base Character
    "Character",
    "ClassFeature",
    "DeathSaveOutcome",
    "DeathSaveResult",
    "DeathSaves",
    "Equipment",
    "FeatureMechanic",
    "FeatureMechanicType",
    "RestResult",
    # Character Classes
    "Fighter",
    "Champion",
    "Barbarian",
    "Berserker",
    "Rogue",
    "Thief",
    "Monk",
    "OpenHand",
    # Type Union and Factory
    "AnyCharacter",
    "CHARACTER_CLASSES",
    "create_character",
    "get_character_class",
    "list_class_types",
    "validate_character",
    # Class utility functions
    "get_martial_arts_die",
    "get_rage_damage_bonus",
    "get_rage_uses",
    "get_sneak_attack_dice",
    # Storage
    "delete_character",
    "list_characters",
    "load_character",
    "save_character",
]
