from io import StringIO
from unittest.mock import MagicMock, patch

from rich.console import Console

from dnd_bot.agents.player import ActionResult, TurnResult
from dnd_bot.character import SpeciesName, get_species
from dnd_bot.cli.display import (
    print_agent_action,
    print_character_card,
    print_dice_roll,
    print_scene,
    print_turn_result,
)


def make_mock_character():
    char = MagicMock()
    char.name = "Thorin"
    char.character_class = "Fighter"
    char.level = 3
    char.species = get_species(SpeciesName.DWARF)
    char.current_hp = 28
    char.max_hp = 32
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


def test_print_agent_action_outputs_character_and_action():
    buf = StringIO()
    with patch("dnd_bot.cli.display.console", Console(file=buf, no_color=True)):
        print_agent_action("Thorin", "I swing my warhammer!")
    assert "Thorin" in buf.getvalue()


def test_print_dice_roll_outputs_total():
    buf = StringIO()
    with patch("dnd_bot.cli.display.console", Console(file=buf, no_color=True)):
        print_dice_roll("Attack", 15, "12 + 3")
    assert "15" in buf.getvalue()


def test_print_turn_result_outputs_narrative():
    turn = TurnResult(narrative="I look around.", mode="exploration")
    buf = StringIO()
    with patch("dnd_bot.cli.display.console", Console(file=buf, no_color=True)):
        print_turn_result("Thorin", turn)
    assert "I look around." in buf.getvalue()


def test_print_turn_result_outputs_action():
    turn = TurnResult(
        narrative="", actions=[ActionResult("check_status", "HP 18/18")], mode="combat"
    )
    buf = StringIO()
    with patch("dnd_bot.cli.display.console", Console(file=buf, no_color=True)):
        print_turn_result("Thorin", turn)
    assert "check_status" in buf.getvalue()
    assert "HP 18/18" in buf.getvalue()


def test_print_turn_result_shows_mode():
    turn = TurnResult(narrative="Ready.", mode="combat")
    buf = StringIO()
    with patch("dnd_bot.cli.display.console", Console(file=buf, no_color=True)):
        print_turn_result("Thorin", turn)
    assert "combat" in buf.getvalue()
