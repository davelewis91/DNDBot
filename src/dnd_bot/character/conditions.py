"""Conditions tracking for D&D 5e (2024 edition).

Conditions are status effects that modify a creature's capabilities.
Each condition has specific rules about what it does and how it can be removed.
"""

from enum import Enum

from pydantic import BaseModel, Field


class Condition(str, Enum):
    """Standard D&D 5e conditions."""

    BLINDED = "blinded"
    CHARMED = "charmed"
    DEAFENED = "deafened"
    FRIGHTENED = "frightened"
    GRAPPLED = "grappled"
    INCAPACITATED = "incapacitated"
    INVISIBLE = "invisible"
    PARALYZED = "paralyzed"
    PETRIFIED = "petrified"
    POISONED = "poisoned"
    PRONE = "prone"
    RESTRAINED = "restrained"
    STUNNED = "stunned"
    UNCONSCIOUS = "unconscious"


# Conditions that grant advantage on attacks against the creature
ADVANTAGE_AGAINST: set[Condition] = {
    Condition.BLINDED,
    Condition.PARALYZED,
    Condition.PETRIFIED,
    Condition.RESTRAINED,
    Condition.STUNNED,
    Condition.UNCONSCIOUS,
}

# Conditions that cause disadvantage on attack rolls
DISADVANTAGE_ON_ATTACKS: set[Condition] = {
    Condition.BLINDED,
    Condition.FRIGHTENED,
    Condition.POISONED,
    Condition.PRONE,
    Condition.RESTRAINED,
}

# Conditions that cause disadvantage on ability checks
DISADVANTAGE_ON_CHECKS: set[Condition] = {
    Condition.FRIGHTENED,
    Condition.POISONED,
}

# Conditions that cause disadvantage on DEX saves
DISADVANTAGE_ON_DEX_SAVES: set[Condition] = {
    Condition.RESTRAINED,
}

# Conditions that cause advantage on DEX saves
ADVANTAGE_ON_DEX_SAVES: set[Condition] = {
    Condition.INVISIBLE,
}

# Conditions that prevent movement
PREVENTS_MOVEMENT: set[Condition] = {
    Condition.GRAPPLED,
    Condition.PARALYZED,
    Condition.PETRIFIED,
    Condition.RESTRAINED,
    Condition.STUNNED,
    Condition.UNCONSCIOUS,
}

# Conditions that prevent actions
PREVENTS_ACTIONS: set[Condition] = {
    Condition.INCAPACITATED,
    Condition.PARALYZED,
    Condition.PETRIFIED,
    Condition.STUNNED,
    Condition.UNCONSCIOUS,
}

# Conditions that cause automatic critical hits on melee attacks
AUTO_CRIT_MELEE: set[Condition] = {
    Condition.PARALYZED,
    Condition.UNCONSCIOUS,
}


class ActiveCondition(BaseModel):
    """An active condition affecting a character.

    Tracks the condition type, its source, and optional duration.
    """

    condition: Condition
    source: str = Field(
        default="",
        description="What caused this condition (e.g., 'Hold Person spell', 'Grappled by Orc')",
    )
    duration: int | None = Field(
        default=None,
        description="Rounds remaining. None means until removed.",
        ge=0,
    )

    def tick(self) -> bool:
        """Decrease duration by 1 round.

        Returns:
            True if the condition is still active, False if it expired.
        """
        if self.duration is None:
            return True
        self.duration -= 1
        return self.duration > 0


class ConditionManager(BaseModel):
    """Manages all active conditions on a character."""

    active: list[ActiveCondition] = Field(default_factory=list)

    def add(
        self,
        condition: Condition,
        source: str = "",
        duration: int | None = None,
    ) -> ActiveCondition:
        """Add a condition to the character.

        Args:
            condition: The condition to add
            source: What caused this condition
            duration: Rounds until it expires (None = until removed)

        Returns:
            The ActiveCondition that was added
        """
        active_condition = ActiveCondition(
            condition=condition,
            source=source,
            duration=duration,
        )
        self.active.append(active_condition)
        return active_condition

    def remove(self, condition: Condition, source: str | None = None) -> int:
        """Remove a condition from the character.

        Args:
            condition: The condition to remove
            source: If provided, only remove conditions from this source

        Returns:
            Number of conditions removed
        """
        before_count = len(self.active)
        if source is None:
            self.active = [ac for ac in self.active if ac.condition != condition]
        else:
            self.active = [
                ac for ac in self.active
                if not (ac.condition == condition and ac.source == source)
            ]
        return before_count - len(self.active)

    def remove_all(self) -> int:
        """Remove all conditions.

        Returns:
            Number of conditions removed
        """
        count = len(self.active)
        self.active = []
        return count

    def has(self, condition: Condition) -> bool:
        """Check if the character has a specific condition."""
        return any(ac.condition == condition for ac in self.active)

    def get(self, condition: Condition) -> list[ActiveCondition]:
        """Get all instances of a specific condition."""
        return [ac for ac in self.active if ac.condition == condition]

    def tick_all(self) -> list[Condition]:
        """Tick all conditions and remove expired ones.

        Call this at the end of each round.

        Returns:
            List of conditions that expired
        """
        expired = []
        still_active = []
        for ac in self.active:
            if ac.tick():
                still_active.append(ac)
            else:
                expired.append(ac.condition)
        self.active = still_active
        return expired

    @property
    def has_disadvantage_on_attacks(self) -> bool:
        """Check if any condition causes disadvantage on attack rolls."""
        return any(ac.condition in DISADVANTAGE_ON_ATTACKS for ac in self.active)

    @property
    def has_disadvantage_on_checks(self) -> bool:
        """Check if any condition causes disadvantage on ability checks."""
        return any(ac.condition in DISADVANTAGE_ON_CHECKS for ac in self.active)

    @property
    def grants_advantage_to_attackers(self) -> bool:
        """Check if any condition grants advantage to attackers."""
        return any(ac.condition in ADVANTAGE_AGAINST for ac in self.active)

    @property
    def is_incapacitated(self) -> bool:
        """Check if the character cannot take actions."""
        return any(ac.condition in PREVENTS_ACTIONS for ac in self.active)

    @property
    def cannot_move(self) -> bool:
        """Check if the character's speed is 0."""
        return any(ac.condition in PREVENTS_MOVEMENT for ac in self.active)

    @property
    def auto_crit_on_melee(self) -> bool:
        """Check if melee attacks auto-crit against this character."""
        return any(ac.condition in AUTO_CRIT_MELEE for ac in self.active)

    def list_conditions(self) -> list[Condition]:
        """Get a list of all unique conditions currently active."""
        return list({ac.condition for ac in self.active})
