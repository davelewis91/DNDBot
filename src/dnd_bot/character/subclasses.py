"""Subclass definitions for D&D 5e (2024 edition).

Each class gains a subclass at level 3. Subclasses provide additional
features at specific levels that enhance or specialize the base class.
"""

from functools import lru_cache

from pydantic import BaseModel, Field

from dnd_bot.data import load_subclasses

from .classes import (
    ClassFeature,
    ClassName,
    FeatureMechanic,
    FeatureMechanicType,
)
from .resources import RestType


class Subclass(BaseModel):
    """A character subclass that provides specialized features."""

    id: str = Field(description="Unique identifier for the subclass")
    name: str = Field(description="Display name of the subclass")
    parent_class: ClassName = Field(description="The class this subclass belongs to")
    description: str = Field(description="Flavor text describing the subclass")
    features: list[ClassFeature] = Field(
        default_factory=list,
        description="Features granted by this subclass",
    )

    def get_features_at_level(self, level: int) -> list[ClassFeature]:
        """Get all subclass features at or below the given level."""
        return [f for f in self.features if f.level <= level]

    def get_feature_by_name(self, name: str) -> ClassFeature | None:
        """Get a specific feature by name."""
        for feature in self.features:
            if feature.name == name:
                return feature
        return None


def _parse_mechanic(data: dict | None) -> FeatureMechanic | None:
    """Parse mechanic data from YAML."""
    if data is None:
        return None

    recover_on = None
    if "recover_on" in data:
        recover_on = RestType.SHORT if data["recover_on"] == "short" else RestType.LONG

    return FeatureMechanic(
        mechanic_type=FeatureMechanicType(data["type"]),
        resource_name=data.get("resource_name"),
        uses_per_rest=data.get("uses_per_rest"),
        uses_per_rest_formula=data.get("uses_per_rest_formula"),
        recover_on=recover_on,
        dice=data.get("dice"),
        dice_per_level=data.get("dice_per_level"),
        bonus=data.get("bonus"),
        extra_data=data.get("extra_data", {}),
    )


def _parse_feature(data: dict) -> ClassFeature:
    """Parse a class feature from YAML."""
    return ClassFeature(
        name=data["name"],
        level=data["level"],
        description=data["description"],
        mechanic=_parse_mechanic(data.get("mechanic")),
    )


def _parse_subclass(subclass_id: str, data: dict) -> Subclass:
    """Parse a subclass from YAML data."""
    features = [_parse_feature(f) for f in data.get("features", [])]

    return Subclass(
        id=subclass_id,
        name=data["name"],
        parent_class=ClassName(data["parent_class"]),
        description=data["description"],
        features=features,
    )


@lru_cache(maxsize=1)
def _get_subclass_registry() -> dict[str, Subclass]:
    """Build the subclass registry from YAML data."""
    subclasses = {}
    raw_data = load_subclasses()
    for subclass_id, subclass_data in raw_data.items():
        subclasses[subclass_id] = _parse_subclass(subclass_id, subclass_data)
    return subclasses


def get_subclass(subclass_id: str) -> Subclass:
    """Get a subclass by ID.

    Parameters
    ----------
    subclass_id : str
        The subclass identifier (e.g., "champion", "thief").

    Returns
    -------
    Subclass
        A copy of the Subclass.

    Raises
    ------
    KeyError
        If the subclass ID is not found.
    """
    registry = _get_subclass_registry()
    if subclass_id not in registry:
        raise KeyError(f"Unknown subclass: {subclass_id}")
    return registry[subclass_id].model_copy(deep=True)


def list_subclasses(parent_class: ClassName | None = None) -> list[str]:
    """List all available subclass IDs.

    Parameters
    ----------
    parent_class : ClassName, optional
        Filter by parent class.

    Returns
    -------
    list[str]
        List of subclass identifiers.
    """
    registry = _get_subclass_registry()
    if parent_class is None:
        return list(registry.keys())
    return [sid for sid, s in registry.items() if s.parent_class == parent_class]


def get_all_subclasses(parent_class: ClassName | None = None) -> list[Subclass]:
    """Get all available subclasses as objects.

    Parameters
    ----------
    parent_class : ClassName, optional
        Filter by parent class.

    Returns
    -------
    list[Subclass]
        List of Subclass objects (copies).
    """
    registry = _get_subclass_registry()
    subclasses = [s.model_copy(deep=True) for s in registry.values()]
    if parent_class is not None:
        subclasses = [s for s in subclasses if s.parent_class == parent_class]
    return subclasses


def get_subclasses_for_class(class_name: ClassName) -> list[Subclass]:
    """Get all subclasses available for a specific class.

    Parameters
    ----------
    class_name : ClassName
        The class to get subclasses for.

    Returns
    -------
    list[Subclass]
        List of Subclass objects (copies).
    """
    return get_all_subclasses(class_name)
