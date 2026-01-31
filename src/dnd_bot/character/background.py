"""Background, personality, and motivation system for D&D characters.

These fields are designed to be AI-friendly for agent-based decision making.
"""

from pydantic import BaseModel, Field


class PersonalityTraits(BaseModel):
    """Personality traits that define how a character behaves and interacts."""

    traits: list[str] = Field(
        default_factory=list,
        description="General personality traits (e.g., 'I am always calm')",
    )
    ideals: list[str] = Field(
        default_factory=list,
        description="Core beliefs and principles (e.g., 'Freedom: Everyone should be free')",
    )
    bonds: list[str] = Field(
        default_factory=list,
        description="Connections to people, places, or things",
    )
    flaws: list[str] = Field(
        default_factory=list,
        description="Character weaknesses or vices (e.g., 'I am suspicious of strangers')",
    )


class Motivation(BaseModel):
    """A character's goal or motivation that drives their actions."""

    description: str
    priority: int = Field(
        default=1, ge=1, le=5, description="Priority level from 1 (highest) to 5 (lowest)"
    )
    is_secret: bool = Field(
        default=False, description="Whether this motivation is hidden from other characters"
    )


class Background(BaseModel):
    """Complete background for a character, designed for AI agent context."""

    name: str = Field(default="", description="Background name (e.g., 'Soldier', 'Sage')")

    backstory: str = Field(
        default="",
        description=(
            "The character's history and life before adventuring. "
            "This provides context for AI agents to roleplay the character."
        ),
    )

    personality: PersonalityTraits = Field(default_factory=PersonalityTraits)

    motivations: list[Motivation] = Field(
        default_factory=list,
        description=(
            "What drives this character to action. "
            "AI agents use these to make in-character decisions."
        ),
    )

    fears: list[str] = Field(
        default_factory=list,
        description="Things the character is afraid of or avoids",
    )

    allies: list[str] = Field(
        default_factory=list,
        description="NPCs or organizations the character is allied with",
    )

    enemies: list[str] = Field(
        default_factory=list,
        description="NPCs or organizations that oppose the character",
    )

    notes: str = Field(
        default="",
        description="Additional notes for the AI or DM about playing this character",
    )

    def get_primary_motivation(self) -> Motivation | None:
        """Get the highest priority motivation."""
        if not self.motivations:
            return None
        return min(self.motivations, key=lambda m: m.priority)

    def get_public_motivations(self) -> list[Motivation]:
        """Get all non-secret motivations."""
        return [m for m in self.motivations if not m.is_secret]

    def to_prompt_context(self) -> str:
        """Generate a text summary suitable for AI agent prompts.

        This creates a natural language description of the character's
        background that can be included in prompts for AI agents.
        """
        parts = []

        if self.backstory:
            parts.append(f"Backstory: {self.backstory}")

        if self.personality.traits:
            parts.append(f"Personality: {', '.join(self.personality.traits)}")

        if self.personality.ideals:
            parts.append(f"Ideals: {', '.join(self.personality.ideals)}")

        if self.personality.bonds:
            parts.append(f"Bonds: {', '.join(self.personality.bonds)}")

        if self.personality.flaws:
            parts.append(f"Flaws: {', '.join(self.personality.flaws)}")

        public_motivations = self.get_public_motivations()
        if public_motivations:
            motivation_strs = [m.description for m in public_motivations]
            parts.append(f"Motivations: {', '.join(motivation_strs)}")

        if self.fears:
            parts.append(f"Fears: {', '.join(self.fears)}")

        if self.notes:
            parts.append(f"Notes: {self.notes}")

        return "\n".join(parts)
