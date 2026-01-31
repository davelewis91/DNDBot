"""Character class definitions for D&D 5e (2024 edition).

MVP: Martial classes only (Fighter, Rogue, Barbarian, Monk).
"""

from enum import Enum

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


class ClassFeature(BaseModel):
    """A class feature gained at a specific level."""

    name: str
    level: int = Field(ge=1, le=20)
    description: str


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
        ),
        ClassFeature(
            name="Second Wind",
            level=1,
            description=(
                "You have a limited well of stamina. On your turn, you can use a Bonus Action "
                "to regain Hit Points equal to 1d10 plus your Fighter level. Once you use this "
                "feature, you must finish a Short or Long Rest before you can use it again."
            ),
        ),
        ClassFeature(
            name="Weapon Mastery",
            level=1,
            description=(
                "Your training with weapons allows you to use the mastery properties of weapons."
            ),
        ),
        ClassFeature(
            name="Action Surge",
            level=2,
            description=(
                "You can push yourself beyond your normal limits. On your turn, you can take "
                "one additional action. Once you use this feature, you must finish a Short "
                "or Long Rest before you can use it again."
            ),
        ),
        ClassFeature(
            name="Tactical Mind",
            level=2,
            description=(
                "You have a mind for tactics. When you fail an ability check, you can expend "
                "a use of Second Wind to add 1d10 to the roll."
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
        ),
        ClassFeature(
            name="Sneak Attack",
            level=1,
            description=(
                "Once per turn, you can deal extra damage to one creature you hit with an "
                "attack roll if you have Advantage on the roll and are using a Finesse or "
                "Ranged weapon. The extra damage is 1d6 (increases with level)."
            ),
        ),
        ClassFeature(
            name="Thieves' Cant",
            level=1,
            description=(
                "You know Thieves' Cant, a secret mix of dialect, jargon, and code."
            ),
        ),
        ClassFeature(
            name="Weapon Mastery",
            level=1,
            description=(
                "Your training with weapons allows you to use the mastery properties of weapons."
            ),
        ),
        ClassFeature(
            name="Cunning Action",
            level=2,
            description=(
                "You can take a Bonus Action to take the Dash, Disengage, or Hide action."
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
        ),
        ClassFeature(
            name="Uncanny Dodge",
            level=5,
            description=(
                "When an attacker you can see hits you with an attack roll, you can use "
                "your Reaction to halve the attack's damage against you."
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
        ),
        ClassFeature(
            name="Unarmored Defense",
            level=1,
            description=(
                "While not wearing armor, your AC equals 10 + Dexterity modifier + "
                "Constitution modifier. You can use a shield and still gain this benefit."
            ),
        ),
        ClassFeature(
            name="Weapon Mastery",
            level=1,
            description=(
                "Your training with weapons allows you to use the mastery properties of weapons."
            ),
        ),
        ClassFeature(
            name="Danger Sense",
            level=2,
            description=(
                "You have Advantage on Dexterity saving throws against effects you can see."
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
        ),
        ClassFeature(
            name="Fast Movement",
            level=5,
            description=(
                "Your Speed increases by 10 feet while you aren't wearing Heavy Armor."
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
        ),
        ClassFeature(
            name="Unarmored Defense",
            level=1,
            description=(
                "While not wearing armor or wielding a Shield, your AC equals "
                "10 + Dexterity modifier + Wisdom modifier."
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
        ),
        ClassFeature(
            name="Monk's Focus",
            level=2,
            description=(
                "You can use Step of the Wind (Bonus Action Dash or Disengage), "
                "Patient Defense (Bonus Action Dodge), or Flurry of Blows "
                "(two unarmed strikes as a Bonus Action) by spending Focus Points."
            ),
        ),
        ClassFeature(
            name="Unarmored Movement",
            level=2,
            description=(
                "Your Speed increases by 10 feet while not wearing armor or a Shield."
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
        ),
        ClassFeature(
            name="Stunning Strike",
            level=5,
            description=(
                "When you hit a creature with a Monk weapon or unarmed strike, you can "
                "spend a Focus Point to attempt to stun the target."
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
