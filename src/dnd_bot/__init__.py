"""DND Bot - A Discord bot for D&D gaming."""

__version__ = "0.1.0"

# Make submodules importable
from dnd_bot import character, items

__all__ = ["character", "items", "__version__"]
