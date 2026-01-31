"""Core ability scores for D&D 5e (2024 edition)."""

from enum import Enum

from pydantic import BaseModel, Field, field_validator


class Ability(str, Enum):
    """The six core ability scores in D&D."""

    STRENGTH = "strength"
    DEXTERITY = "dexterity"
    CONSTITUTION = "constitution"
    INTELLIGENCE = "intelligence"
    WISDOM = "wisdom"
    CHARISMA = "charisma"

    # Short aliases
    STR = "strength"
    DEX = "dexterity"
    CON = "constitution"
    INT = "intelligence"
    WIS = "wisdom"
    CHA = "charisma"


def calculate_modifier(score: int) -> int:
    """Calculate the ability modifier from a score.

    The modifier is (score - 10) // 2, so:
    - Score 10-11 = +0
    - Score 12-13 = +1
    - Score 8-9 = -1
    etc.
    """
    return (score - 10) // 2


class AbilityScores(BaseModel):
    """Container for all six ability scores with modifier calculations."""

    strength: int = Field(default=10, ge=1, le=30)
    dexterity: int = Field(default=10, ge=1, le=30)
    constitution: int = Field(default=10, ge=1, le=30)
    intelligence: int = Field(default=10, ge=1, le=30)
    wisdom: int = Field(default=10, ge=1, le=30)
    charisma: int = Field(default=10, ge=1, le=30)

    @field_validator("*", mode="before")
    @classmethod
    def validate_score_range(cls, v: int) -> int:
        """Ensure ability scores are within valid D&D range (1-30)."""
        if isinstance(v, int) and not 1 <= v <= 30:
            raise ValueError("Ability scores must be between 1 and 30")
        return v

    def get_score(self, ability: Ability) -> int:
        """Get the score for a specific ability."""
        # Normalize to the base value (handles STR -> strength, etc.)
        ability_name = ability.value
        return getattr(self, ability_name)

    def get_modifier(self, ability: Ability) -> int:
        """Get the modifier for a specific ability."""
        return calculate_modifier(self.get_score(ability))

    @property
    def strength_modifier(self) -> int:
        """Strength modifier."""
        return calculate_modifier(self.strength)

    @property
    def dexterity_modifier(self) -> int:
        """Dexterity modifier."""
        return calculate_modifier(self.dexterity)

    @property
    def constitution_modifier(self) -> int:
        """Constitution modifier."""
        return calculate_modifier(self.constitution)

    @property
    def intelligence_modifier(self) -> int:
        """Intelligence modifier."""
        return calculate_modifier(self.intelligence)

    @property
    def wisdom_modifier(self) -> int:
        """Wisdom modifier."""
        return calculate_modifier(self.wisdom)

    @property
    def charisma_modifier(self) -> int:
        """Charisma modifier."""
        return calculate_modifier(self.charisma)


class AbilityBonus(BaseModel):
    """Represents a temporary or permanent bonus/penalty to an ability score."""

    ability: Ability
    value: int
    source: str = ""  # e.g., "Belt of Giant Strength", "Exhaustion"
    is_temporary: bool = True
