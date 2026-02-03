"""Base item classes for D&D 5e (2024 edition).

Defines the foundational item types: Item, Weapon, Armor, and Consumable.
"""

from enum import Enum

from pydantic import BaseModel, Field


class ItemType(str, Enum):
    """Categories of items."""

    WEAPON = "weapon"
    ARMOR = "armor"
    SHIELD = "shield"
    CONSUMABLE = "consumable"
    ADVENTURING_GEAR = "adventuring_gear"
    TOOL = "tool"
    AMMUNITION = "ammunition"


class Rarity(str, Enum):
    """Item rarity levels."""

    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    VERY_RARE = "very_rare"
    LEGENDARY = "legendary"
    ARTIFACT = "artifact"


class DamageType(str, Enum):
    """Types of damage in D&D."""

    BLUDGEONING = "bludgeoning"
    PIERCING = "piercing"
    SLASHING = "slashing"
    ACID = "acid"
    COLD = "cold"
    FIRE = "fire"
    FORCE = "force"
    LIGHTNING = "lightning"
    NECROTIC = "necrotic"
    POISON = "poison"
    PSYCHIC = "psychic"
    RADIANT = "radiant"
    THUNDER = "thunder"


class WeaponProperty(str, Enum):
    """Weapon properties that affect how weapons can be used."""

    AMMUNITION = "ammunition"
    FINESSE = "finesse"
    HEAVY = "heavy"
    LIGHT = "light"
    LOADING = "loading"
    RANGE = "range"
    REACH = "reach"
    THROWN = "thrown"
    TWO_HANDED = "two_handed"
    VERSATILE = "versatile"
    MONK = "monk"  # Can be used with Martial Arts


class WeaponCategory(str, Enum):
    """Weapon categories for proficiency."""

    SIMPLE = "simple"
    MARTIAL = "martial"


class ArmorType(str, Enum):
    """Armor weight categories."""

    LIGHT = "light"
    MEDIUM = "medium"
    HEAVY = "heavy"
    SHIELD = "shield"


class Item(BaseModel):
    """Base class for all items."""

    id: str = Field(description="Unique identifier for the item")
    name: str = Field(description="Display name")
    description: str = Field(default="", description="Item description")
    item_type: ItemType
    weight: float = Field(default=0.0, ge=0, description="Weight in pounds")
    value: int = Field(default=0, ge=0, description="Value in copper pieces")
    rarity: Rarity = Field(default=Rarity.COMMON)
    magical: bool = Field(default=False)


class Weapon(Item):
    """A weapon that can be used in combat."""

    item_type: ItemType = ItemType.WEAPON
    category: WeaponCategory = WeaponCategory.SIMPLE
    damage_dice: str = Field(description="Damage dice (e.g., '1d8', '2d6')")
    damage_type: DamageType
    properties: list[WeaponProperty] = Field(default_factory=list)
    range_normal: int | None = Field(
        default=None,
        description="Normal range in feet (for ranged/thrown weapons)",
    )
    range_long: int | None = Field(
        default=None,
        description="Long range in feet (for ranged/thrown weapons)",
    )
    versatile_dice: str | None = Field(
        default=None,
        description="Damage dice when used two-handed (for versatile weapons)",
    )

    @property
    def is_finesse(self) -> bool:
        """Check if weapon can use DEX for attack/damage."""
        return WeaponProperty.FINESSE in self.properties

    @property
    def is_ranged(self) -> bool:
        """Check if weapon is ranged (has ammunition or thrown property)."""
        return (
            WeaponProperty.AMMUNITION in self.properties
            or WeaponProperty.THROWN in self.properties
        )

    @property
    def is_two_handed(self) -> bool:
        """Check if weapon requires two hands."""
        return WeaponProperty.TWO_HANDED in self.properties

    @property
    def is_light(self) -> bool:
        """Check if weapon is light (for dual wielding)."""
        return WeaponProperty.LIGHT in self.properties

    @property
    def is_heavy(self) -> bool:
        """Check if weapon is heavy (disadvantage for small creatures)."""
        return WeaponProperty.HEAVY in self.properties


class Armor(Item):
    """Armor that provides protection."""

    item_type: ItemType = ItemType.ARMOR
    armor_type: ArmorType
    base_ac: int = Field(ge=0, description="Base AC provided")
    max_dex_bonus: int | None = Field(
        default=None,
        description="Maximum DEX bonus to AC (None = unlimited, 0 = no DEX)",
    )
    strength_required: int | None = Field(
        default=None,
        description="Minimum STR to avoid speed penalty",
    )
    stealth_disadvantage: bool = Field(
        default=False,
        description="Whether wearing this armor imposes disadvantage on Stealth",
    )

    def calculate_ac(self, dex_modifier: int) -> int:
        """Calculate AC with this armor for a given DEX modifier.

        Parameters
        ----------
        dex_modifier : int
            The character's Dexterity modifier.

        Returns
        -------
        int
            The calculated AC. Heavy armor ignores DEX, medium armor
            caps DEX bonus at max_dex_bonus, light armor adds full DEX.
        """
        if self.armor_type == ArmorType.HEAVY:
            # Heavy armor doesn't add DEX
            return self.base_ac
        elif self.max_dex_bonus is not None:
            # Medium armor caps DEX bonus
            return self.base_ac + min(dex_modifier, self.max_dex_bonus)
        else:
            # Light armor adds full DEX
            return self.base_ac + dex_modifier


class Shield(Item):
    """A shield that provides bonus AC."""

    item_type: ItemType = ItemType.SHIELD
    ac_bonus: int = Field(default=2, description="Bonus to AC when wielded")


class Consumable(Item):
    """A consumable item like a potion or scroll."""

    item_type: ItemType = ItemType.CONSUMABLE
    uses: int = Field(default=1, ge=1, description="Number of uses")
    effect: str = Field(default="", description="Description of the effect")
    healing_dice: str | None = Field(
        default=None,
        description="Healing dice if applicable (e.g., '2d4+2')",
    )


class Ammunition(Item):
    """Ammunition for ranged weapons."""

    item_type: ItemType = ItemType.AMMUNITION
    quantity: int = Field(default=20, ge=1, description="Number of pieces")
    weapon_types: list[str] = Field(
        default_factory=list,
        description="Weapon types this ammunition works with",
    )
