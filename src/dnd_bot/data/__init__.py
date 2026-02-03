"""Data loading infrastructure for D&D game data.

This module provides utilities for loading game data from YAML files,
with caching to avoid repeated file I/O.
"""

from .loader import (
    clear_cache,
    load_ammunition,
    load_armor,
    load_classes,
    load_consumables,
    load_shields,
    load_species,
    load_subclasses,
    load_weapons,
)

__all__ = [
    "clear_cache",
    "load_ammunition",
    "load_armor",
    "load_classes",
    "load_consumables",
    "load_shields",
    "load_species",
    "load_subclasses",
    "load_weapons",
]
