"""Exhaustion tracking for D&D 5e (2024 edition).

In the 2024 rules, exhaustion is simplified:
- Levels range from 0 (none) to 10 (death)
- Each level gives a cumulative -1 penalty to d20 tests (ability checks,
  attack rolls, and saving throws)
- At level 10, the character dies
- One level is removed per long rest
"""

from pydantic import BaseModel, Field


class Exhaustion(BaseModel):
    """Tracks exhaustion levels and calculates penalties.

    D&D 2024 exhaustion rules:
    - Each level gives -1 to all d20 tests (ability checks, saves, attacks)
    - Level 10 = death
    - Remove 1 level per long rest
    """

    level: int = Field(default=0, ge=0, le=10)

    @property
    def penalty(self) -> int:
        """Get the penalty to apply to all d20 tests.

        Returns a negative number (e.g., -3 at exhaustion level 3).
        """
        return -self.level

    @property
    def is_dead(self) -> bool:
        """Check if the character has died from exhaustion."""
        return self.level >= 10

    def add(self, levels: int = 1) -> int:
        """Add exhaustion levels.

        Args:
            levels: Number of levels to add (default 1)

        Returns:
            The new exhaustion level
        """
        self.level = min(10, self.level + levels)
        return self.level

    def remove(self, levels: int = 1) -> int:
        """Remove exhaustion levels (typically from a long rest).

        Args:
            levels: Number of levels to remove (default 1)

        Returns:
            The new exhaustion level
        """
        self.level = max(0, self.level - levels)
        return self.level

    def reset(self) -> None:
        """Reset exhaustion to 0."""
        self.level = 0
