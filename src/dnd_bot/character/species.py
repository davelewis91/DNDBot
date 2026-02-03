"""Species definitions for D&D 5e (2024 edition)."""

from enum import Enum
from functools import lru_cache

from pydantic import BaseModel, Field

from dnd_bot.data import load_species


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
    darkvision: int = Field(default=0, ge=0)
    traits: list[Trait] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=lambda: ["Common"])
    resistances: list[str] = Field(default_factory=list)


def _parse_species(species_id: str, data: dict) -> Species:
    """Parse YAML data into a Species model.

    Parameters
    ----------
    species_id : str
        The species identifier (e.g., 'human', 'elf').
    data : dict
        Raw YAML data for the species.

    Returns
    -------
    Species
        The parsed species model.
    """
    traits = [Trait(name=t["name"], description=t["description"])
              for t in data.get("traits", [])]

    return Species(
        name=SpeciesName(species_id),
        size=Size(data.get("size", "medium")),
        speed=data.get("speed", 30),
        creature_type=CreatureType(data.get("creature_type", "humanoid")),
        darkvision=data.get("darkvision", 0),
        traits=traits,
        languages=data.get("languages", ["Common"]),
        resistances=data.get("resistances", []),
    )


@lru_cache(maxsize=1)
def _get_species_registry() -> dict[SpeciesName, Species]:
    """Build the species registry from YAML data."""
    data = load_species()
    return {SpeciesName(species_id): _parse_species(species_id, species_data)
            for species_id, species_data in data.items()}


def get_species(name: SpeciesName) -> Species:
    """Get a species definition by name.

    Parameters
    ----------
    name : SpeciesName
        The species to retrieve.

    Returns
    -------
    Species
        A copy of the species definition.

    Raises
    ------
    KeyError
        If the species name is not found.
    """
    return _get_species_registry()[name].model_copy(deep=True)


def list_species() -> list[str]:
    """List all available species IDs.

    Returns
    -------
    list[str]
        List of species identifiers.
    """
    return [s.value for s in _get_species_registry().keys()]


def get_all_species() -> list[Species]:
    """Get all species definitions.

    Returns
    -------
    list[Species]
        List of all species.
    """
    return list(_get_species_registry().values())
