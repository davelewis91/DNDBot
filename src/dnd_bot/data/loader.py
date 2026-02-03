"""YAML data loading utilities with caching.

Provides functions to load game data from YAML files and convert them
to Pydantic models. Data is cached on first load to avoid repeated I/O.
"""

from functools import lru_cache
from pathlib import Path
from typing import TypeVar

import yaml

# Type variable for generic loading
T = TypeVar("T")

# Base path for data files
DATA_DIR = Path(__file__).parent


def _load_yaml(filename: str) -> dict:
    """Load a YAML file from the data directory.

    Parameters
    ----------
    filename : str
        Path relative to the data directory (e.g., 'items/weapons.yaml').

    Returns
    -------
    dict
        Parsed YAML content.

    Raises
    ------
    FileNotFoundError
        If the YAML file doesn't exist.
    """
    filepath = DATA_DIR / filename
    with filepath.open() as f:
        return yaml.safe_load(f) or {}


@lru_cache(maxsize=1)
def load_weapons() -> dict:
    """Load all weapon definitions from YAML.

    Returns
    -------
    dict
        Dictionary mapping weapon IDs to their raw YAML data.
    """
    return _load_yaml("items/weapons.yaml")


@lru_cache(maxsize=1)
def load_armor() -> dict:
    """Load all armor definitions from YAML.

    Returns
    -------
    dict
        Dictionary mapping armor IDs to their raw YAML data.
    """
    return _load_yaml("items/armor.yaml")


@lru_cache(maxsize=1)
def load_shields() -> dict:
    """Load all shield definitions from YAML.

    Returns
    -------
    dict
        Dictionary mapping shield IDs to their raw YAML data.
    """
    return _load_yaml("items/shields.yaml")


@lru_cache(maxsize=1)
def load_consumables() -> dict:
    """Load all consumable definitions from YAML.

    Returns
    -------
    dict
        Dictionary mapping consumable IDs to their raw YAML data.
    """
    return _load_yaml("items/consumables.yaml")


@lru_cache(maxsize=1)
def load_ammunition() -> dict:
    """Load all ammunition definitions from YAML.

    Returns
    -------
    dict
        Dictionary mapping ammunition IDs to their raw YAML data.
    """
    return _load_yaml("items/ammunition.yaml")


@lru_cache(maxsize=1)
def load_species() -> dict:
    """Load all species definitions from YAML.

    Returns
    -------
    dict
        Dictionary mapping species IDs to their raw YAML data.
    """
    return _load_yaml("species.yaml")


def _load_class_file(class_name: str) -> dict:
    """Load a single class definition from YAML.

    Parameters
    ----------
    class_name : str
        Name of the class (e.g., 'fighter', 'rogue').

    Returns
    -------
    dict
        Raw YAML data for the class.
    """
    return _load_yaml(f"classes/{class_name}.yaml")


@lru_cache(maxsize=1)
def load_classes() -> dict:
    """Load all class definitions from YAML.

    Returns
    -------
    dict
        Dictionary mapping class names to their raw YAML data.
    """
    classes = {}
    class_names = ["fighter", "rogue", "barbarian", "monk"]
    for name in class_names:
        try:
            classes[name] = _load_class_file(name)
        except FileNotFoundError:
            pass
    return classes


def _load_subclass_file(parent_class: str) -> dict:
    """Load subclass definitions for a parent class from YAML.

    Parameters
    ----------
    parent_class : str
        Name of the parent class (e.g., 'fighter', 'rogue').

    Returns
    -------
    dict
        Dictionary mapping subclass IDs to their raw YAML data.
    """
    return _load_yaml(f"subclasses/{parent_class}.yaml")


@lru_cache(maxsize=1)
def load_subclasses() -> dict:
    """Load all subclass definitions from YAML.

    Returns
    -------
    dict
        Dictionary mapping subclass IDs to their raw YAML data.
    """
    subclasses = {}
    parent_classes = ["fighter", "rogue", "barbarian", "monk"]
    for parent in parent_classes:
        try:
            data = _load_subclass_file(parent)
            subclasses.update(data)
        except FileNotFoundError:
            pass
    return subclasses


def clear_cache() -> None:
    """Clear all cached data.

    Useful for testing or when data files are modified at runtime.
    """
    load_weapons.cache_clear()
    load_armor.cache_clear()
    load_shields.cache_clear()
    load_consumables.cache_clear()
    load_ammunition.cache_clear()
    load_species.cache_clear()
    load_classes.cache_clear()
    load_subclasses.cache_clear()
