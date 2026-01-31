"""Skills system for D&D 5e (2024 edition)."""

from enum import Enum

from pydantic import BaseModel, Field

from .abilities import Ability


class Skill(str, Enum):
    """The 18 skills in D&D 5e, each associated with an ability score."""

    # Strength
    ATHLETICS = "athletics"

    # Dexterity
    ACROBATICS = "acrobatics"
    SLEIGHT_OF_HAND = "sleight_of_hand"
    STEALTH = "stealth"

    # Intelligence
    ARCANA = "arcana"
    HISTORY = "history"
    INVESTIGATION = "investigation"
    NATURE = "nature"
    RELIGION = "religion"

    # Wisdom
    ANIMAL_HANDLING = "animal_handling"
    INSIGHT = "insight"
    MEDICINE = "medicine"
    PERCEPTION = "perception"
    SURVIVAL = "survival"

    # Charisma
    DECEPTION = "deception"
    INTIMIDATION = "intimidation"
    PERFORMANCE = "performance"
    PERSUASION = "persuasion"


# Mapping of skills to their governing ability
SKILL_ABILITIES: dict[Skill, Ability] = {
    # Strength
    Skill.ATHLETICS: Ability.STRENGTH,
    # Dexterity
    Skill.ACROBATICS: Ability.DEXTERITY,
    Skill.SLEIGHT_OF_HAND: Ability.DEXTERITY,
    Skill.STEALTH: Ability.DEXTERITY,
    # Intelligence
    Skill.ARCANA: Ability.INTELLIGENCE,
    Skill.HISTORY: Ability.INTELLIGENCE,
    Skill.INVESTIGATION: Ability.INTELLIGENCE,
    Skill.NATURE: Ability.INTELLIGENCE,
    Skill.RELIGION: Ability.INTELLIGENCE,
    # Wisdom
    Skill.ANIMAL_HANDLING: Ability.WISDOM,
    Skill.INSIGHT: Ability.WISDOM,
    Skill.MEDICINE: Ability.WISDOM,
    Skill.PERCEPTION: Ability.WISDOM,
    Skill.SURVIVAL: Ability.WISDOM,
    # Charisma
    Skill.DECEPTION: Ability.CHARISMA,
    Skill.INTIMIDATION: Ability.CHARISMA,
    Skill.PERFORMANCE: Ability.CHARISMA,
    Skill.PERSUASION: Ability.CHARISMA,
}


def get_skill_ability(skill: Skill) -> Ability:
    """Get the ability score that governs a skill."""
    return SKILL_ABILITIES[skill]


class SkillProficiency(BaseModel):
    """Tracks proficiency level for a single skill."""

    skill: Skill
    proficient: bool = False
    expertise: bool = False  # Double proficiency bonus

    def get_proficiency_multiplier(self) -> int:
        """Return the proficiency bonus multiplier (0, 1, or 2 for expertise)."""
        if self.expertise:
            return 2
        if self.proficient:
            return 1
        return 0


class SkillSet(BaseModel):
    """Container for all skill proficiencies."""

    proficiencies: dict[Skill, SkillProficiency] = Field(default_factory=dict)

    def model_post_init(self, __context: object) -> None:
        """Initialize all skills with no proficiency if not provided."""
        for skill in Skill:
            if skill not in self.proficiencies:
                self.proficiencies[skill] = SkillProficiency(skill=skill)

    def is_proficient(self, skill: Skill) -> bool:
        """Check if proficient in a skill."""
        return self.proficiencies[skill].proficient

    def has_expertise(self, skill: Skill) -> bool:
        """Check if has expertise in a skill."""
        return self.proficiencies[skill].expertise

    def set_proficiency(self, skill: Skill, proficient: bool = True) -> None:
        """Set proficiency for a skill."""
        self.proficiencies[skill].proficient = proficient

    def set_expertise(self, skill: Skill, expertise: bool = True) -> None:
        """Set expertise for a skill. Also grants proficiency if expertise is True."""
        if expertise:
            self.proficiencies[skill].proficient = True
        self.proficiencies[skill].expertise = expertise

    def get_proficiency_multiplier(self, skill: Skill) -> int:
        """Get the proficiency bonus multiplier for a skill."""
        return self.proficiencies[skill].get_proficiency_multiplier()

    def get_proficient_skills(self) -> list[Skill]:
        """Get a list of all skills the character is proficient in."""
        return [skill for skill, prof in self.proficiencies.items() if prof.proficient]

    def get_expertise_skills(self) -> list[Skill]:
        """Get a list of all skills the character has expertise in."""
        return [skill for skill, prof in self.proficiencies.items() if prof.expertise]


def get_proficiency_bonus(level: int) -> int:
    """Calculate the proficiency bonus based on character level.

    Proficiency bonus increases at levels 5, 9, 13, and 17.
    """
    if level < 1:
        return 2
    return (level - 1) // 4 + 2
