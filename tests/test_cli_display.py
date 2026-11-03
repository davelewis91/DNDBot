from io import StringIO
from unittest.mock import MagicMock, patch

from rich.console import Console

from dnd_bot.character import SpeciesName, get_species
from dnd_bot.cli.display import (
    print_character_card,
    print_scene,
)


def make_mock_character():
    char = MagicMock()
    char.name = "Thorin"
    char.character_class = "Fighter"
    char.level = 3
    char.species = get_species(SpeciesName.DWARF)
    char.current_hp = 28
    char.max_hp = 32
    char.armor_class = 16
    char.proficiency_bonus = 2
    char.initiative = 2
    char.conditions = []
    return char


def test_print_character_card_outputs_name():
    char = make_mock_character()
    buf = StringIO()
    with patch("dnd_bot.cli.display.console", Console(file=buf, no_color=True)):
        print_character_card(char)
    assert "Thorin" in buf.getvalue()


def test_print_scene_outputs_description():
    buf = StringIO()
    with patch("dnd_bot.cli.display.console", Console(file=buf, no_color=True)):
        print_scene("You enter a dark cave.")
    assert "dark cave" in buf.getvalue()
