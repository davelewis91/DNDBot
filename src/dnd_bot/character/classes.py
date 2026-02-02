"""Character class definitions for D&D 5e (2024 edition).

MVP: Martial classes only (Fighter, Rogue, Barbarian, Monk).
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from .abilities import Ability
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


class RestType(str, Enum):
    """Rest types for resource recovery (duplicated to avoid circular import)."""

    SHORT = "short"
    LONG = "long"


class FeatureMechanicType(str, Enum):
    """Types of class feature mechanics."""

    PASSIVE = "passive"  # Always active (e.g., Sneak Attack, Unarmored Defense)
    RESOURCE = "resource"  # Uses per rest (e.g., Second Wind, Rage)
    TOGGLE = "toggle"  # Can be activated/deactivated (e.g., Rage while active)
    REACTION = "reaction"  # Uses reaction (e.g., Uncanny Dodge)


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
    skill_choices: list[Skill]  # Skills available to choose from
    num_skill_choices: int = Field(ge=1, le=4)
    armor_proficiencies: list[str] = Field(default_factory=list)
    weapon_proficiencies: list[str] = Field(default_factory=list)
    features: list[ClassFeature] = Field(default_factory=list)

    def get_features_at_level(self, level: int) -> list[ClassFeature]:
        """Get all features gained at or before a specific level."""
        return [f for f in self.features if f.level <= level]


# Pre-defined martial classes

FIGHTER = CharacterClass(
    name=ClassName.FIGHTER,
    hit_die=HitDie.D10,
    saving_throw_proficiencies=[Ability.STRENGTH, Ability.CONSTITUTION],
    skill_choices=[
        Skill.ACROBATICS,
        Skill.ANIMAL_HANDLING,
        Skill.ATHLETICS,
        Skill.HISTORY,
        Skill.INSIGHT,
        Skill.INTIMIDATION,
        Skill.PERCEPTION,
        Skill.SURVIVAL,
    ],
    num_skill_choices=2,
    armor_proficiencies=["Light Armor", "Medium Armor", "Heavy Armor", "Shields"],
    weapon_proficiencies=["Simple Weapons", "Martial Weapons"],
    features=[
        ClassFeature(
            name="Fighting Style",
            level=1,
            description=(
                "You have trained in a particular style of combat. Choose a Fighting Style option."
            ),
            mechanic=FeatureMechanic(mechanic_type=FeatureMechanicType.PASSIVE),
        ),
        ClassFeature(
            name="Second Wind",
            level=1,
            description=(
                "You have a limited well of stamina. On your turn, you can use a Bonus Action "
                "to regain Hit Points equal to 1d10 plus your Fighter level. Once you use this "
                "feature, you must finish a Short or Long Rest before you can use it again."
            ),
            mechanic=FeatureMechanic(
                mechanic_type=FeatureMechanicType.RESOURCE,
                resource_name="Second Wind",
                uses_per_rest=1,
                recover_on=RestType.SHORT,
                dice="1d10",
                extra_data={"add_level": True},
            ),
        ),
        ClassFeature(
            name="Weapon Mastery",
            level=1,
            description=(
                "Your training with weapons allows you to use the mastery properties of weapons."
            ),
            mechanic=FeatureMechanic(mechanic_type=FeatureMechanicType.PASSIVE),
        ),
        ClassFeature(
            name="Action Surge",
            level=2,
            description=(
                "You can push yourself beyond your normal limits. On your turn, you can take "
                "one additional action. Once you use this feature, you must finish a Short "
                "or Long Rest before you can use it again."
            ),
            mechanic=FeatureMechanic(
                mechanic_type=FeatureMechanicType.RESOURCE,
                resource_name="Action Surge",
                uses_per_rest=1,
                recover_on=RestType.SHORT,
            ),
        ),
        ClassFeature(
            name="Tactical Mind",
            level=2,
            description=(
                "You have a mind for tactics. When you fail an ability check, you can expend "
                "a use of Second Wind to add 1d10 to the roll."
            ),
            mechanic=FeatureMechanic(
                mechanic_type=FeatureMechanicType.PASSIVE,
                extra_data={"uses_second_wind": True, "dice": "1d10"},
            ),
        ),
        ClassFeature(
            name="Fighter Subclass",
            level=3,
            description="You gain a Fighter subclass of your choice.",
        ),
        ClassFeature(
            name="Ability Score Improvement",
            level=4,
            description="You can increase one ability score by 2, or two ability scores by 1.",
        ),
        ClassFeature(
            name="Extra Attack",
            level=5,
            description=(
                "You can attack twice, instead of once, whenever you take the Attack action."
            ),
            mechanic=FeatureMechanic(
                mechanic_type=FeatureMechanicType.PASSIVE,
                extra_data={"extra_attacks": 1},
            ),
        ),
    ],
)

ROGUE = CharacterClass(
    name=ClassName.ROGUE,
    hit_die=HitDie.D8,
    saving_throw_proficiencies=[Ability.DEXTERITY, Ability.INTELLIGENCE],
    skill_choices=[
        Skill.ACROBATICS,
        Skill.ATHLETICS,
        Skill.DECEPTION,
        Skill.INSIGHT,
        Skill.INTIMIDATION,
        Skill.INVESTIGATION,
        Skill.PERCEPTION,
        Skill.PERFORMANCE,
        Skill.PERSUASION,
        Skill.SLEIGHT_OF_HAND,
        Skill.STEALTH,
    ],
    num_skill_choices=4,
    armor_proficiencies=["Light Armor"],
    weapon_proficiencies=["Simple Weapons", "Martial Weapons with Finesse or Light property"],
    features=[
        ClassFeature(
            name="Expertise",
            level=1,
            description=(
                "You gain Expertise in two of your skill proficiencies."
            ),
            mechanic=FeatureMechanic(mechanic_type=FeatureMechanicType.PASSIVE),
        ),
        ClassFeature(
            name="Sneak Attack",
            level=1,
            description=(
                "Once per turn, you can deal extra damage to one creature you hit with an "
                "attack roll if you have Advantage on the roll and are using a Finesse or "
                "Ranged weapon. The extra damage is 1d6 (increases with level)."
            ),
            mechanic=FeatureMechanic(
                mechanic_type=FeatureMechanicType.PASSIVE,
                dice_per_level="1d6",
                extra_data={"levels_per_die": 2, "once_per_turn": True},
            ),
        ),
        ClassFeature(
            name="Thieves' Cant",
            level=1,
            description=(
                "You know Thieves' Cant, a secret mix of dialect, jargon, and code."
            ),
            mechanic=FeatureMechanic(mechanic_type=FeatureMechanicType.PASSIVE),
        ),
        ClassFeature(
            name="Weapon Mastery",
            level=1,
            description=(
                "Your training with weapons allows you to use the mastery properties of weapons."
            ),
            mechanic=FeatureMechanic(mechanic_type=FeatureMechanicType.PASSIVE),
        ),
        ClassFeature(
            name="Cunning Action",
            level=2,
            description=(
                "You can take a Bonus Action to take the Dash, Disengage, or Hide action."
            ),
            mechanic=FeatureMechanic(
                mechanic_type=FeatureMechanicType.PASSIVE,
                extra_data={"bonus_actions": ["Dash", "Disengage", "Hide"]},
            ),
        ),
        ClassFeature(
            name="Rogue Subclass",
            level=3,
            description="You gain a Rogue subclass of your choice.",
        ),
        ClassFeature(
            name="Steady Aim",
            level=3,
            description=(
                "As a Bonus Action, you give yourself Advantage on your next attack roll "
                "on the current turn. Your Speed becomes 0 until the end of the turn."
            ),
            mechanic=FeatureMechanic(
                mechanic_type=FeatureMechanicType.PASSIVE,
                extra_data={"grants_advantage": True, "sets_speed_zero": True},
            ),
        ),
        ClassFeature(
            name="Ability Score Improvement",
            level=4,
            description="You can increase one ability score by 2, or two ability scores by 1.",
        ),
        ClassFeature(
            name="Cunning Strike",
            level=5,
            description=(
                "When you deal Sneak Attack damage, you can forgo some of that damage "
                "to apply special effects."
            ),
            mechanic=FeatureMechanic(mechanic_type=FeatureMechanicType.PASSIVE),
        ),
        ClassFeature(
            name="Uncanny Dodge",
            level=5,
            description=(
                "When an attacker you can see hits you with an attack roll, you can use "
                "your Reaction to halve the attack's damage against you."
            ),
            mechanic=FeatureMechanic(
                mechanic_type=FeatureMechanicType.REACTION,
                extra_data={"halves_damage": True},
            ),
        ),
    ],
)

BARBARIAN = CharacterClass(
    name=ClassName.BARBARIAN,
    hit_die=HitDie.D12,
    saving_throw_proficiencies=[Ability.STRENGTH, Ability.CONSTITUTION],
    skill_choices=[
        Skill.ANIMAL_HANDLING,
        Skill.ATHLETICS,
        Skill.INTIMIDATION,
        Skill.NATURE,
        Skill.PERCEPTION,
        Skill.SURVIVAL,
    ],
    num_skill_choices=2,
    armor_proficiencies=["Light Armor", "Medium Armor", "Shields"],
    weapon_proficiencies=["Simple Weapons", "Martial Weapons"],
    features=[
        ClassFeature(
            name="Rage",
            level=1,
            description=(
                "You can enter a rage as a Bonus Action. While raging, you gain bonus "
                "damage on Strength-based attacks, resistance to physical damage, and "
                "advantage on Strength checks and saves. You have 2 Rages (increases with level)."
            ),
            mechanic=FeatureMechanic(
                mechanic_type=FeatureMechanicType.TOGGLE,
                resource_name="Rage",
                uses_per_rest=2,
                recover_on=RestType.LONG,
                extra_data={
                    "damage_bonus": 2,
                    "resistances": ["bludgeoning", "piercing", "slashing"],
                    "advantage_on": ["strength_checks", "strength_saves"],
                },
            ),
        ),
        ClassFeature(
            name="Unarmored Defense",
            level=1,
            description=(
                "While not wearing armor, your AC equals 10 + Dexterity modifier + "
                "Constitution modifier. You can use a shield and still gain this benefit."
            ),
            mechanic=FeatureMechanic(
                mechanic_type=FeatureMechanicType.PASSIVE,
                extra_data={"ac_formula": "10 + dex + con"},
            ),
        ),
        ClassFeature(
            name="Weapon Mastery",
            level=1,
            description=(
                "Your training with weapons allows you to use the mastery properties of weapons."
            ),
            mechanic=FeatureMechanic(mechanic_type=FeatureMechanicType.PASSIVE),
        ),
        ClassFeature(
            name="Danger Sense",
            level=2,
            description=(
                "You have Advantage on Dexterity saving throws against effects you can see."
            ),
            mechanic=FeatureMechanic(
                mechanic_type=FeatureMechanicType.PASSIVE,
                extra_data={"advantage_on": ["dex_saves_visible"]},
            ),
        ),
        ClassFeature(
            name="Reckless Attack",
            level=2,
            description=(
                "You can throw aside all concern for defense to attack with fierce desperation. "
                "When you make your first attack on your turn, you can decide to attack "
                "recklessly, giving you Advantage on attack rolls using Strength, but attack "
                "rolls against you have Advantage until your next turn."
            ),
            mechanic=FeatureMechanic(
                mechanic_type=FeatureMechanicType.PASSIVE,
                extra_data={
                    "optional": True,
                    "grants_advantage": True,
                    "enemies_have_advantage": True,
                },
            ),
        ),
        ClassFeature(
            name="Barbarian Subclass",
            level=3,
            description="You gain a Barbarian subclass of your choice.",
        ),
        ClassFeature(
            name="Primal Knowledge",
            level=3,
            description=(
                "You gain proficiency in one skill from the Barbarian skill list."
            ),
            mechanic=FeatureMechanic(mechanic_type=FeatureMechanicType.PASSIVE),
        ),
        ClassFeature(
            name="Ability Score Improvement",
            level=4,
            description="You can increase one ability score by 2, or two ability scores by 1.",
        ),
        ClassFeature(
            name="Extra Attack",
            level=5,
            description=(
                "You can attack twice, instead of once, whenever you take the Attack action."
            ),
            mechanic=FeatureMechanic(
                mechanic_type=FeatureMechanicType.PASSIVE,
                extra_data={"extra_attacks": 1},
            ),
        ),
        ClassFeature(
            name="Fast Movement",
            level=5,
            description=(
                "Your Speed increases by 10 feet while you aren't wearing Heavy Armor."
            ),
            mechanic=FeatureMechanic(
                mechanic_type=FeatureMechanicType.PASSIVE,
                extra_data={"speed_bonus": 10},
            ),
        ),
    ],
)

MONK = CharacterClass(
    name=ClassName.MONK,
    hit_die=HitDie.D8,
    saving_throw_proficiencies=[Ability.STRENGTH, Ability.DEXTERITY],
    skill_choices=[
        Skill.ACROBATICS,
        Skill.ATHLETICS,
        Skill.HISTORY,
        Skill.INSIGHT,
        Skill.RELIGION,
        Skill.STEALTH,
    ],
    num_skill_choices=2,
    armor_proficiencies=[],
    weapon_proficiencies=["Simple Weapons", "Martial Weapons with Light property"],
    features=[
        ClassFeature(
            name="Martial Arts",
            level=1,
            description=(
                "You can use Dexterity instead of Strength for unarmed strikes and Monk "
                "weapons. Your unarmed strikes deal 1d6 damage (increases with level)."
            ),
            mechanic=FeatureMechanic(
                mechanic_type=FeatureMechanicType.PASSIVE,
                dice="1d6",
                extra_data={"use_dex_for_unarmed": True, "scales_at_levels": [5, 11, 17]},
            ),
        ),
        ClassFeature(
            name="Unarmored Defense",
            level=1,
            description=(
                "While not wearing armor or wielding a Shield, your AC equals "
                "10 + Dexterity modifier + Wisdom modifier."
            ),
            mechanic=FeatureMechanic(
                mechanic_type=FeatureMechanicType.PASSIVE,
                extra_data={"ac_formula": "10 + dex + wis", "no_shield": True},
            ),
        ),
        ClassFeature(
            name="Focus",
            level=2,
            description=(
                "You can channel your focus to perform extraordinary feats. You have "
                "Focus Points equal to your Monk level. You can spend Focus Points on "
                "various Focus features."
            ),
            mechanic=FeatureMechanic(
                mechanic_type=FeatureMechanicType.RESOURCE,
                resource_name="Focus Points",
                uses_per_rest_formula="level",
                recover_on=RestType.SHORT,
            ),
        ),
        ClassFeature(
            name="Monk's Focus",
            level=2,
            description=(
                "You can use Step of the Wind (Bonus Action Dash or Disengage), "
                "Patient Defense (Bonus Action Dodge), or Flurry of Blows "
                "(two unarmed strikes as a Bonus Action) by spending Focus Points."
            ),
            mechanic=FeatureMechanic(
                mechanic_type=FeatureMechanicType.PASSIVE,
                extra_data={
                    "focus_options": {
                        "step_of_the_wind": {"cost": 1, "actions": ["Dash", "Disengage"]},
                        "patient_defense": {"cost": 1, "actions": ["Dodge"]},
                        "flurry_of_blows": {"cost": 1, "extra_unarmed_strikes": 2},
                    }
                },
            ),
        ),
        ClassFeature(
            name="Unarmored Movement",
            level=2,
            description=(
                "Your Speed increases by 10 feet while not wearing armor or a Shield."
            ),
            mechanic=FeatureMechanic(
                mechanic_type=FeatureMechanicType.PASSIVE,
                extra_data={"speed_bonus": 10},
            ),
        ),
        ClassFeature(
            name="Deflect Attacks",
            level=3,
            description=(
                "When you're hit by an attack, you can use your Reaction to reduce "
                "the damage. If you reduce the damage to 0, you can spend a Focus Point "
                "to make a ranged attack with the deflected projectile or energy."
            ),
            mechanic=FeatureMechanic(
                mechanic_type=FeatureMechanicType.REACTION,
                extra_data={"reduces_damage": True, "can_redirect": True, "redirect_cost": 1},
            ),
        ),
        ClassFeature(
            name="Monk Subclass",
            level=3,
            description="You gain a Monk subclass of your choice.",
        ),
        ClassFeature(
            name="Ability Score Improvement",
            level=4,
            description="You can increase one ability score by 2, or two ability scores by 1.",
        ),
        ClassFeature(
            name="Extra Attack",
            level=5,
            description=(
                "You can attack twice, instead of once, whenever you take the Attack action."
            ),
            mechanic=FeatureMechanic(
                mechanic_type=FeatureMechanicType.PASSIVE,
                extra_data={"extra_attacks": 1},
            ),
        ),
        ClassFeature(
            name="Stunning Strike",
            level=5,
            description=(
                "When you hit a creature with a Monk weapon or unarmed strike, you can "
                "spend a Focus Point to attempt to stun the target."
            ),
            mechanic=FeatureMechanic(
                mechanic_type=FeatureMechanicType.PASSIVE,
                extra_data={"focus_cost": 1, "save_dc_ability": "wisdom"},
            ),
        ),
    ],
)


# Registry of all available classes
CLASS_REGISTRY: dict[ClassName, CharacterClass] = {
    ClassName.FIGHTER: FIGHTER,
    ClassName.ROGUE: ROGUE,
    ClassName.BARBARIAN: BARBARIAN,
    ClassName.MONK: MONK,
}


def get_class(name: ClassName) -> CharacterClass:
    """Get a class definition by name."""
    return CLASS_REGISTRY[name].model_copy(deep=True)


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

    Args:
        feature: The ClassFeature with resource mechanics
        level: The character's level

    Returns:
        Number of uses for the resource
    """
    if feature.mechanic is None:
        return 0

    # Fixed uses per rest
    if feature.mechanic.uses_per_rest is not None:
        return feature.mechanic.uses_per_rest

    # Formula-based uses
    if feature.mechanic.uses_per_rest_formula is not None:
        formula = feature.mechanic.uses_per_rest_formula
        if formula == "level":
            return level
        if formula.startswith("level/"):
            divisor = int(formula.split("/")[1])
            return max(1, level // divisor)

    return 1  # Default to 1 use


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
