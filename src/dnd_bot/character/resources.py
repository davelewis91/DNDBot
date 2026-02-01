"""Resource tracking for D&D 5e (2024 edition).

Tracks expendable resources like hit dice, class feature uses (Second Wind,
Rage, Action Surge, etc.), and rest counters.
"""

from enum import Enum

from pydantic import BaseModel, Field


class RestType(str, Enum):
    """Types of rests in D&D."""

    SHORT = "short"
    LONG = "long"


class Resource(BaseModel):
    """A trackable resource that can be spent and recovered.

    Used for class features like Second Wind, Rage, Action Surge, etc.
    """

    name: str = Field(description="Display name of the resource")
    current: int = Field(ge=0, description="Current available uses")
    maximum: int = Field(ge=1, description="Maximum uses")
    recover_on: RestType = Field(description="When this resource recovers")
    recover_amount: int | None = Field(
        default=None,
        description="Amount to recover (None = full recovery)",
    )

    def spend(self, amount: int = 1) -> bool:
        """Spend resource uses.

        Args:
            amount: Number of uses to spend (default 1)

        Returns:
            True if successful, False if insufficient uses
        """
        if self.current >= amount:
            self.current -= amount
            return True
        return False

    def recover(self, rest_type: RestType) -> int:
        """Recover resource based on rest type.

        Long rests always recover resources (both short and long rest resources).
        Short rests only recover short rest resources.

        Args:
            rest_type: The type of rest taken

        Returns:
            Amount recovered
        """
        # Long rest recovers everything, short rest only recovers short rest resources
        if rest_type == RestType.LONG or self.recover_on == rest_type:
            if self.recover_amount is None:
                # Full recovery
                recovered = self.maximum - self.current
                self.current = self.maximum
            else:
                # Partial recovery
                recovered = min(self.recover_amount, self.maximum - self.current)
                self.current += recovered
            return recovered
        return 0

    def reset(self) -> None:
        """Reset resource to maximum."""
        self.current = self.maximum

    @property
    def is_available(self) -> bool:
        """Check if at least one use is available."""
        return self.current > 0

    @property
    def uses_remaining(self) -> int:
        """Get remaining uses."""
        return self.current


class HitDice(BaseModel):
    """Hit dice pool for healing during short rests.

    Characters have a number of hit dice equal to their level, which can
    be spent during short rests to recover HP.
    """

    die_size: int = Field(ge=4, le=12, description="Size of hit die (d6, d8, d10, d12)")
    total: int = Field(ge=1, description="Total hit dice (equals character level)")
    current: int = Field(ge=0, description="Available hit dice to spend")

    def spend(self, amount: int = 1) -> bool:
        """Spend hit dice.

        Args:
            amount: Number of hit dice to spend

        Returns:
            True if successful, False if insufficient hit dice
        """
        if self.current >= amount:
            self.current -= amount
            return True
        return False

    def recover(self, amount: int) -> int:
        """Recover hit dice (typically on long rest).

        Args:
            amount: Number of hit dice to recover

        Returns:
            Actual amount recovered (may be less if near maximum)
        """
        recovered = min(amount, self.total - self.current)
        self.current += recovered
        return recovered

    def recover_half(self) -> int:
        """Recover half of total hit dice (rounded down, minimum 1).

        This is the standard long rest recovery.

        Returns:
            Amount recovered
        """
        amount = max(1, self.total // 2)
        return self.recover(amount)

    def reset(self) -> None:
        """Reset to full hit dice."""
        self.current = self.total

    @property
    def available(self) -> int:
        """Get available hit dice."""
        return self.current


class ResourcePool(BaseModel):
    """Container for all character resources.

    Manages hit dice, class feature uses, and rest tracking.
    """

    hit_dice: HitDice | None = Field(
        default=None,
        description="Hit dice pool for short rest healing",
    )
    feature_uses: dict[str, Resource] = Field(
        default_factory=dict,
        description="Class feature resources keyed by feature name",
    )
    short_rests_since_long: int = Field(
        default=0,
        ge=0,
        le=2,
        description="Number of short rests taken since last long rest (max 2)",
    )

    def add_feature(
        self,
        name: str,
        maximum: int,
        recover_on: RestType,
        recover_amount: int | None = None,
    ) -> Resource:
        """Add a trackable feature resource.

        Args:
            name: Feature name (e.g., "Second Wind", "Rage")
            maximum: Maximum uses
            recover_on: When the resource recovers
            recover_amount: Amount to recover (None = full)

        Returns:
            The created Resource
        """
        key = name.lower().replace(" ", "_")
        resource = Resource(
            name=name,
            current=maximum,
            maximum=maximum,
            recover_on=recover_on,
            recover_amount=recover_amount,
        )
        self.feature_uses[key] = resource
        return resource

    def get_feature(self, name: str) -> Resource | None:
        """Get a feature resource by name.

        Args:
            name: Feature name (case-insensitive, spaces converted to underscores)

        Returns:
            The Resource if found, None otherwise
        """
        key = name.lower().replace(" ", "_")
        return self.feature_uses.get(key)

    def use_feature(self, name: str, amount: int = 1) -> bool:
        """Use a feature resource.

        Args:
            name: Feature name
            amount: Uses to spend (default 1)

        Returns:
            True if successful, False if resource not found or insufficient uses
        """
        resource = self.get_feature(name)
        if resource is None:
            return False
        return resource.spend(amount)

    def has_feature_available(self, name: str) -> bool:
        """Check if a feature has uses remaining.

        Args:
            name: Feature name

        Returns:
            True if at least one use is available
        """
        resource = self.get_feature(name)
        if resource is None:
            return False
        return resource.is_available

    def recover_short_rest(self) -> dict[str, int]:
        """Recover resources for a short rest.

        Returns:
            Dictionary of resource names to amounts recovered
        """
        recovered = {}
        for resource in self.feature_uses.values():
            amount = resource.recover(RestType.SHORT)
            if amount > 0:
                recovered[resource.name] = amount
        return recovered

    def recover_long_rest(self) -> dict[str, int]:
        """Recover resources for a long rest.

        Also recovers hit dice (half, rounded down, minimum 1).

        Returns:
            Dictionary of resource names to amounts recovered
        """
        recovered = {}

        # Recover all feature uses
        for resource in self.feature_uses.values():
            amount = resource.recover(RestType.LONG)
            if amount > 0:
                recovered[resource.name] = amount

        # Recover hit dice
        if self.hit_dice is not None:
            hd_recovered = self.hit_dice.recover_half()
            if hd_recovered > 0:
                recovered["Hit Dice"] = hd_recovered

        # Reset short rest counter
        self.short_rests_since_long = 0

        return recovered

    def can_short_rest(self) -> bool:
        """Check if a short rest can be taken.

        Characters can take up to 2 short rests between long rests.
        """
        return self.short_rests_since_long < 2

    def record_short_rest(self) -> bool:
        """Record that a short rest was taken.

        Returns:
            True if successful, False if max short rests already taken
        """
        if not self.can_short_rest():
            return False
        self.short_rests_since_long += 1
        return True

    def reset_all(self) -> None:
        """Reset all resources to maximum (for testing/initialization)."""
        if self.hit_dice is not None:
            self.hit_dice.reset()
        for resource in self.feature_uses.values():
            resource.reset()
        self.short_rests_since_long = 0
