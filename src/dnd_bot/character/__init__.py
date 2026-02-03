"""D&D character system.

This module provides a complete D&D 5e (2024 edition) character representation
with support for abilities, skills, species, classes, backgrounds, and YAML persistence.
"""

from .abilities import Ability, AbilityBonus, AbilityScores, calculate_modifier
from .background import Background, Motivation, PersonalityTraits
from .character import (
    Character,
    DeathSaveOutcome,
    DeathSaveResult,
    DeathSaves,
    Equipment,
    RestResult,
    create_character,
)
from .classes import (
    CharacterClass,
    ClassFeature,
    ClassName,
    FeatureMechanic,
    FeatureMechanicType,
    HitDie,
    calculate_resource_uses,
    get_class,
    get_martial_arts_die,
    get_rage_damage_bonus,
    get_rage_uses,
    get_resource_features,
    get_sneak_attack_dice,
    list_classes,
)
from .conditions import ActiveCondition, Condition, ConditionManager
from .exhaustion import Exhaustion
from .resources import HitDice, Resource, ResourcePool, RestType
from .skills import (
    Skill,
    SkillProficiency,
    SkillSet,
    get_proficiency_bonus,
    get_skill_ability,
)
from .species import CreatureType, Size, Species, SpeciesName, Trait, get_species, list_species
from .storage import delete_character, list_characters, load_character, save_character
from .subclasses import (
    Subclass,
    get_all_subclasses,
    get_subclass,
    get_subclasses_for_class,
    list_subclasses,
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
    "get_species",
    "list_species",
    # Classes
    "CharacterClass",
    "ClassFeature",
    "ClassName",
    "FeatureMechanic",
    "FeatureMechanicType",
    "HitDie",
    "calculate_resource_uses",
    "get_class",
    "get_martial_arts_die",
    "get_rage_damage_bonus",
    "get_rage_uses",
    "get_resource_features",
    "get_sneak_attack_dice",
    "list_classes",
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
    # Character
    "Character",
    "DeathSaveOutcome",
    "DeathSaveResult",
    "DeathSaves",
    "Equipment",
    "RestResult",
    "create_character",
    # Storage
    "delete_character",
    "list_characters",
    "load_character",
    "save_character",
    # Subclasses
    "Subclass",
    "get_all_subclasses",
    "get_subclass",
    "get_subclasses_for_class",
    "list_subclasses",
]
