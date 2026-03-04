from io import StringIO
from unittest.mock import MagicMock, patch

from rich.console import Console

from dnd_bot.agents.player import TurnResult
from dnd_bot.character import SpeciesName, get_species
from dnd_bot.cli.dm_parser import DMCommand
from dnd_bot.cli.game import GameSession, apply_commands


class SimpleCharacter:
    """Minimal character stub for testing apply_commands state changes."""

    name = "Thorin"
    character_class = "Fighter"
    level = 3
    species = get_species(SpeciesName.DWARF)

    def __init__(self):
        self.current_hp = 28
        self.max_hp = 32
        self.conditions = []

    def take_damage(self, amount: int) -> int:
        self.current_hp -= amount
        return amount

    def heal(self, amount: int) -> int:
        healed = min(self.max_hp - self.current_hp, amount)
        self.current_hp += healed
        return healed

    def add_condition(self, condition) -> None:
        self.conditions.append(condition)

    def remove_condition(self, condition) -> int:
        if condition in self.conditions:
            self.conditions.remove(condition)
            return 1
        return 0


class SimpleAgent:
    """Minimal agent stub for testing mode changes."""

    def __init__(self):
        self.mode = "exploration"
        self.character = SimpleCharacter()

    def set_mode(self, mode: str) -> None:
        self.mode = mode


def make_mock_agent():
    agent = MagicMock()
    agent.process_turn.return_value = "I attack the goblin!"
    agent.character = SimpleCharacter()
    return agent


def test_apply_commands_damage():
    char = SimpleCharacter()
    with patch("dnd_bot.cli.game.console"):
        apply_commands([DMCommand(type="damage", value=5)], char)
    assert char.current_hp == 23  # 28 - 5 via take_damage


def test_apply_commands_heal():
    char = SimpleCharacter()
    char.current_hp = 20
    with patch("dnd_bot.cli.game.console"):
        apply_commands([DMCommand(type="heal", value=5)], char)
    assert char.current_hp == 25  # 20 + 5 via heal


def test_apply_commands_mode_change():
    agent = SimpleAgent()
    with patch("dnd_bot.cli.game.console"):
        apply_commands([DMCommand(type="mode", value="combat")], agent.character, agent=agent)
    assert agent.mode == "combat"


def test_apply_commands_mode_silent_when_already_set():
    """Mode command prints nothing when agent is already in that mode."""
    agent = SimpleAgent()
    agent.set_mode("combat")  # already in combat
    buf = StringIO()
    with patch("dnd_bot.cli.game.console"), \
         patch("dnd_bot.cli.display.console", Console(file=buf, no_color=True)):
        apply_commands([DMCommand(type="mode", value="combat")], agent.character, agent=agent)
    assert "Mode" not in buf.getvalue()


def test_game_session_init():
    agent = make_mock_agent()
    session = GameSession(agent=agent, provider="ollama", model="llama3:8b")
    assert session.agent is agent


def test_apply_commands_condition_apply():
    char = SimpleCharacter()
    with patch("dnd_bot.cli.game.console"):
        apply_commands([DMCommand(type="condition", value="poisoned")], char)
    from dnd_bot.character.conditions import Condition
    assert Condition.POISONED in char.conditions


def test_apply_commands_condition_remove():
    char = SimpleCharacter()
    from dnd_bot.character.conditions import Condition
    char.conditions.append(Condition.POISONED)
    with patch("dnd_bot.cli.game.console"):
        apply_commands([DMCommand(type="remove_condition", value="poisoned")], char)
    assert Condition.POISONED not in char.conditions


def test_handle_slash_command_uncondition():
    agent = make_mock_agent()
    from dnd_bot.character.conditions import Condition
    agent.character.conditions.append(Condition.POISONED)
    session = GameSession(agent=agent, provider="ollama", model="llama3:8b")
    with patch("dnd_bot.cli.game.console"):
        result = session._handle_slash_command("/uncondition poisoned")
    assert result is True
    assert Condition.POISONED not in agent.character.conditions


def test_handle_slash_command_status():
    agent = make_mock_agent()
    session = GameSession(agent=agent, provider="ollama", model="llama3:8b")
    buf = StringIO()
    with patch("dnd_bot.cli.display.console", Console(file=buf, no_color=True)):
        result = session._handle_slash_command("/status")
    assert result is True
    assert "Thorin" in buf.getvalue()


def test_game_session_prints_mode_change_when_agent_switches():
    agent = SimpleAgent()

    def fake_process_turn(dm_input):
        agent.set_mode("combat")
        return TurnResult(narrative="I draw my sword.", mode="combat")

    agent.process_turn = fake_process_turn
    session = GameSession(agent=agent, provider="ollama", model="llama3:8b")

    with patch("dnd_bot.cli.game.parse_dm_input") as mock_parse, \
         patch("dnd_bot.cli.game.print_scene"), \
         patch("dnd_bot.cli.game.print_turn_result"), \
         patch("dnd_bot.cli.game.print_character_card"), \
         patch("dnd_bot.cli.game.print_mode_change") as mock_mode, \
         patch("dnd_bot.cli.game.console") as mock_console:
        mock_parse.return_value = MagicMock(narrative="Enemies appear!", commands=[])
        mock_console.input.side_effect = ["Enemies appear!", KeyboardInterrupt]
        session.run()

    mock_mode.assert_called_once_with("combat")
