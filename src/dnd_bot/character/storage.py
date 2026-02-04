"""YAML-based character storage for persistence.

Uses pydantic's discriminated union for automatic class selection on load.
"""

from pathlib import Path

import yaml

from .types import AnyCharacter, validate_character

DEFAULT_CHARACTERS_DIR = Path("./characters")


def _character_to_dict(character: AnyCharacter) -> dict:
    """Convert a Character to a YAML-friendly dictionary.

    Uses pydantic's model_dump with json mode for clean serialization.
    """
    return character.model_dump(mode="json")


def _dict_to_character(data: dict) -> AnyCharacter:
    """Convert a YAML dictionary back to a Character.

    Uses the discriminated union to automatically select the correct class
    based on the class_type field.
    """
    return validate_character(data)


def save_character(character: AnyCharacter, directory: Path | None = None) -> Path:
    """Save a character to a YAML file.

    The filename is derived from the character's name.

    Parameters
    ----------
    character : AnyCharacter
        The character to save.
    directory : Path, optional
        Directory to save to. Defaults to ./characters/

    Returns
    -------
    Path
        Path to the saved file.
    """
    if directory is None:
        directory = DEFAULT_CHARACTERS_DIR

    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)

    # Create a safe filename from the character name
    safe_name = "".join(c if c.isalnum() or c in "._- " else "_" for c in character.name)
    safe_name = safe_name.strip().replace(" ", "_").lower()
    filename = directory / f"{safe_name}.yaml"

    data = _character_to_dict(character)

    with open(filename, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    return filename


def load_character(filepath: Path | str) -> AnyCharacter:
    """Load a character from a YAML file.

    Automatically selects the correct character class based on the
    class_type field using pydantic's discriminated union.

    Parameters
    ----------
    filepath : Path | str
        Path to the YAML file.

    Returns
    -------
    AnyCharacter
        The loaded Character (Fighter, Rogue, Barbarian, Monk, or subclass).

    Raises
    ------
    FileNotFoundError
        If the file doesn't exist.
    yaml.YAMLError
        If the file is not valid YAML.
    ValueError
        If the YAML doesn't represent a valid character.
    """
    filepath = Path(filepath)

    with open(filepath, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    return _dict_to_character(data)


def list_characters(directory: Path | None = None) -> list[Path]:
    """List all character files in a directory.

    Parameters
    ----------
    directory : Path, optional
        Directory to search. Defaults to ./characters/

    Returns
    -------
    list[Path]
        List of paths to character YAML files.
    """
    if directory is None:
        directory = DEFAULT_CHARACTERS_DIR

    directory = Path(directory)

    if not directory.exists():
        return []

    return sorted(directory.glob("*.yaml"))


def delete_character(filepath: Path | str) -> bool:
    """Delete a character file.

    Parameters
    ----------
    filepath : Path | str
        Path to the YAML file.

    Returns
    -------
    bool
        True if deleted, False if file didn't exist.
    """
    filepath = Path(filepath)

    if filepath.exists():
        filepath.unlink()
        return True
    return False
