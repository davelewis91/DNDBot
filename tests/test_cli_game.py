from io import StringIO
from unittest.mock import MagicMock, patch

from rich.console import Console

from dnd_bot.cli.dm_parser import DMCommand
from dnd_bot.cli.game import GameSession, apply_commands


class SimpleCharacter:
    """Minimal character stub for testing apply_commands state changes."""

    name = "Thorin"
    current_hp = 28
    max_hp = 32
    conditions: list = []
    character_class = "Fighter"
    level = 3
    species = "Dwarf"

    def take_damage(self, amount: int) -> int:
        self.current_hp -= amount
        return amount

    def heal(self, amount: int) -> int:
        healed = min(self.max_hp - self.current_hp, amount)
        self.current_hp += healed
        return healed


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


def test_game_session_init():
    agent = make_mock_agent()
    session = GameSession(agent=agent, provider="ollama", model="llama3:8b")
    assert session.agent is agent


def test_handle_slash_command_status():
    agent = make_mock_agent()
    session = GameSession(agent=agent, provider="ollama", model="llama3:8b")
    buf = StringIO()
    with patch("dnd_bot.cli.display.console", Console(file=buf, no_color=True)):
        result = session._handle_slash_command("/status")
    assert result is True
    assert "Thorin" in buf.getvalue()
