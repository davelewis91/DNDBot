"""Species definitions for D&D 5e (2024 edition)."""

from enum import Enum

from pydantic import BaseModel, Field


class Size(str, Enum):
    """Character size categories."""

    TINY = "tiny"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    HUGE = "huge"
    GARGANTUAN = "gargantuan"


class CreatureType(str, Enum):
    """Creature type categories."""

    HUMANOID = "humanoid"
    FEY = "fey"
    CELESTIAL = "celestial"
    FIEND = "fiend"
    UNDEAD = "undead"
    CONSTRUCT = "construct"
    ELEMENTAL = "elemental"
    GIANT = "giant"
    DRAGON = "dragon"
    ABERRATION = "aberration"
    BEAST = "beast"
    MONSTROSITY = "monstrosity"
    OOZE = "ooze"
    PLANT = "plant"


class SpeciesName(str, Enum):
    """Available species options."""

    HUMAN = "human"
    ELF = "elf"
    DWARF = "dwarf"
    HALFLING = "halfling"


class Trait(BaseModel):
    """A species trait or special ability."""

    name: str
    description: str


class Species(BaseModel):
    """Base species definition with traits and characteristics."""

    name: SpeciesName
    size: Size = Size.MEDIUM
    speed: int = Field(default=30, ge=0)
    creature_type: CreatureType = CreatureType.HUMANOID
    darkvision: int = Field(default=0, ge=0)  # Range in feet, 0 means no darkvision
    traits: list[Trait] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=lambda: ["Common"])
    resistances: list[str] = Field(default_factory=list)


# Pre-defined species following 2024 rules
HUMAN = Species(
    name=SpeciesName.HUMAN,
    size=Size.MEDIUM,
    speed=30,
    darkvision=0,
    traits=[
        Trait(
            name="Resourceful",
            description=(
                "You gain Heroic Inspiration whenever you finish a Long Rest."
            ),
        ),
        Trait(
            name="Skillful",
            description="You gain proficiency in one skill of your choice.",
        ),
        Trait(
            name="Versatile",
            description=(
                "You gain an Origin feat of your choice."
            ),
        ),
    ],
    languages=["Common", "One additional language"],
)

ELF = Species(
    name=SpeciesName.ELF,
    size=Size.MEDIUM,
    speed=30,
    darkvision=60,
    creature_type=CreatureType.HUMANOID,
    traits=[
        Trait(
            name="Darkvision",
            description=(
                "You have Darkvision with a range of 60 feet."
            ),
        ),
        Trait(
            name="Elven Lineage",
            description=(
                "You are part of a lineage that grants you supernatural abilities. "
                "Choose a lineage from Drow, High Elf, or Wood Elf."
            ),
        ),
        Trait(
            name="Fey Ancestry",
            description=(
                "You have Advantage on saving throws you make to avoid or end the "
                "Charmed condition."
            ),
        ),
        Trait(
            name="Keen Senses",
            description="You have proficiency in the Perception skill.",
        ),
        Trait(
            name="Trance",
            description=(
                "You don't need to sleep, and magic can't put you to sleep. "
                "You can finish a Long Rest in 4 hours if you spend those hours "
                "in a trancelike meditation, during which you retain consciousness."
            ),
        ),
    ],
    languages=["Common", "Elvish"],
)

DWARF = Species(
    name=SpeciesName.DWARF,
    size=Size.MEDIUM,
    speed=30,
    darkvision=120,
    traits=[
        Trait(
            name="Darkvision",
            description="You have Darkvision with a range of 120 feet.",
        ),
        Trait(
            name="Dwarven Resilience",
            description=(
                "You have Resistance to Poison damage. You also have Advantage on "
                "saving throws you make to avoid or end the Poisoned condition."
            ),
        ),
        Trait(
            name="Dwarven Toughness",
            description=(
                "Your Hit Point maximum increases by 1, and it increases by 1 again "
                "whenever you gain a level."
            ),
        ),
        Trait(
            name="Stonecunning",
            description=(
                "As a Bonus Action, you gain Tremorsense with a range of 60 feet "
                "for 10 minutes. You must be on a stone surface or touching a stone "
                "surface to use this Tremorsense. The stone can be natural or worked. "
                "You can use this Bonus Action a number of times equal to your "
                "Proficiency Bonus, and you regain all expended uses when you finish "
                "a Long Rest."
            ),
        ),
    ],
    languages=["Common", "Dwarvish"],
    resistances=["Poison"],
)

HALFLING = Species(
    name=SpeciesName.HALFLING,
    size=Size.SMALL,
    speed=30,
    darkvision=0,
    traits=[
        Trait(
            name="Brave",
            description=(
                "You have Advantage on saving throws you make to avoid or end "
                "the Frightened condition."
            ),
        ),
        Trait(
            name="Halfling Nimbleness",
            description=(
                "You can move through the space of any creature that is a size "
                "larger than you, but you can't stop in the same space."
            ),
        ),
        Trait(
            name="Luck",
            description=(
                "When you roll a 1 on the d20 of a D20 Test, you can reroll the die, "
                "and you must use the new roll."
            ),
        ),
        Trait(
            name="Naturally Stealthy",
            description=(
                "You can take the Hide action even when you are obscured only by "
                "a creature that is at least one size larger than you."
            ),
        ),
    ],
    languages=["Common", "Halfling"],
)


# Registry of all available species
SPECIES_REGISTRY: dict[SpeciesName, Species] = {
    SpeciesName.HUMAN: HUMAN,
    SpeciesName.ELF: ELF,
    SpeciesName.DWARF: DWARF,
    SpeciesName.HALFLING: HALFLING,
}


def get_species(name: SpeciesName) -> Species:
    """Get a species definition by name."""
    return SPECIES_REGISTRY[name].model_copy(deep=True)
