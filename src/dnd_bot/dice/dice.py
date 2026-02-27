"""Dice rolling module for D&D notation.

Provides abstractions for parsing and rolling D&D dice notation (e.g., "2d6+3")
with support for advantage/disadvantage on d20 rolls.
"""

from __future__ import annotations

import random
import re
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class DiceResult(BaseModel):
    """Result of rolling dice.

    Attributes
    ----------
    rolls : list[int]
        Individual die roll results.
    modifier : int
        The modifier added to the roll.
    total : int
        Sum of rolls plus modifier.
    notation : str
        Original dice notation that was rolled.
    """

    rolls: list[int] = Field(default_factory=list)
    modifier: int = 0
    total: int = 0
    notation: str = ""

    def __str__(self) -> str:
        """Format as 'total (rolls + modifier)'."""
        if not self.rolls:
            return str(self.total)
        rolls_str = ", ".join(str(r) for r in self.rolls)
        if self.modifier == 0:
            return f"{self.total} [{rolls_str}]"
        sign = "+" if self.modifier > 0 else ""
        return f"{self.total} [{rolls_str}]{sign}{self.modifier}"


class Dice(BaseModel):
    """Represents a dice roll expression like '2d6+3'.

    Parses D&D dice notation and provides rolling functionality.

    Attributes
    ----------
    count : int
        Number of dice to roll.
    sides : int
        Number of sides on each die.
    modifier : int
        Modifier to add to the total.

    Examples
    --------
    >>> dice = Dice.parse("2d6+3")
    >>> result = dice.roll()
    >>> print(result.total)
    """

    count: int = Field(default=1, ge=1, le=100)
    sides: int = Field(default=20, ge=1, le=100)
    modifier: int = Field(default=0, ge=-100, le=100)

    @field_validator("count", "sides")
    @classmethod
    def validate_positive(cls, v: int, info) -> int:
        """Ensure count and sides are at least 1."""
        if v < 1:
            raise ValueError(f"{info.field_name} must be at least 1")
        return v

    @classmethod
    def parse(cls, notation: str) -> Dice:
        """Parse dice notation string into a Dice object.

        Parameters
        ----------
        notation : str
            Dice notation like "2d6", "1d20+5", "d8-1", "d6".

        Returns
        -------
        Dice
            Parsed dice object.

        Raises
        ------
        ValueError
            If the notation is invalid.

        Examples
        --------
        >>> Dice.parse("2d6+3")
        Dice(count=2, sides=6, modifier=3)
        >>> Dice.parse("d20")
        Dice(count=1, sides=20, modifier=0)
        """
        notation = notation.strip().lower()

        # Match patterns like: 2d6+3, d20, 1d8-2, d6
        pattern = r"^(\d*)d(\d+)([+-]\d+)?$"
        match = re.match(pattern, notation)

        if not match:
            raise ValueError(f"Invalid dice notation: '{notation}'")

        count_str, sides_str, modifier_str = match.groups()

        count = int(count_str) if count_str else 1
        sides = int(sides_str)
        modifier = int(modifier_str) if modifier_str else 0

        return cls(count=count, sides=sides, modifier=modifier)

    def roll(self) -> DiceResult:
        """Roll the dice and return the result.

        Returns
        -------
        DiceResult
            Contains individual rolls, modifier, and total.
        """
        rolls = [random.randint(1, self.sides) for _ in range(self.count)]
        total = sum(rolls) + self.modifier

        return DiceResult(
            rolls=rolls,
            modifier=self.modifier,
            total=total,
            notation=str(self),
        )

    def __str__(self) -> str:
        """Return the dice notation string."""
        base = f"{self.count}d{self.sides}"
        if self.modifier > 0:
            return f"{base}+{self.modifier}"
        elif self.modifier < 0:
            return f"{base}{self.modifier}"
        return base


def roll(notation: str) -> DiceResult:
    """Parse and roll dice from notation string.

    Convenience function that combines parsing and rolling.

    Parameters
    ----------
    notation : str
        Dice notation like "2d6+3", "d20", "1d8-1".

    Returns
    -------
    DiceResult
        The roll result.

    Examples
    --------
    >>> result = roll("2d6+3")
    >>> print(result.total)
    """
    dice = Dice.parse(notation)
    return dice.roll()


def d20(
    advantage: bool = False,
    disadvantage: bool = False,
    modifier: int = 0,
) -> DiceResult:
    """Roll a d20 with optional advantage/disadvantage.

    Parameters
    ----------
    advantage : bool
        Roll twice and take the higher result.
    disadvantage : bool
        Roll twice and take the lower result.
    modifier : int
        Modifier to add to the final roll.

    Returns
    -------
    DiceResult
        The roll result. If advantage/disadvantage, both rolls are in the rolls list.

    Notes
    -----
    If both advantage and disadvantage are True, they cancel out (normal roll).
    """
    roll1 = random.randint(1, 20)

    # If both advantage and disadvantage, they cancel out
    if advantage and disadvantage:
        return DiceResult(
            rolls=[roll1],
            modifier=modifier,
            total=roll1 + modifier,
            notation="1d20",
        )

    if advantage or disadvantage:
        roll2 = random.randint(1, 20)
        chosen = max(roll1, roll2) if advantage else min(roll1, roll2)
        mode: Literal["advantage", "disadvantage"] = "advantage" if advantage else "disadvantage"
        return DiceResult(
            rolls=[roll1, roll2],
            modifier=modifier,
            total=chosen + modifier,
            notation=f"1d20 ({mode})",
        )

    return DiceResult(
        rolls=[roll1],
        modifier=modifier,
        total=roll1 + modifier,
        notation="1d20",
    )
