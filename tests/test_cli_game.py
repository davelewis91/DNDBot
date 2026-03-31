from unittest.mock import MagicMock, patch

from dnd_bot.character import SpeciesName, get_species
from dnd_bot.cli.game import GameSession


class SimpleCharacter:
    """Minimal character stub."""

    character_class = "Fighter"
    level = 3
    species = get_species(SpeciesName.DWARF)
    armor_class = 16
    proficiency_bonus = 2
    initiative = 2

    def __init__(self, name="Thorin"):
        self.name = name
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

    def short_rest(self):
        result = MagicMock()
        result.success = True
        return result

    def long_rest(self):
        pass


def make_session(party=None):
    if party is None:
        party = [SimpleCharacter()]
    session = GameSession.__new__(GameSession)
    session.party = party
    session.provider = "ollama"
    session.model = "llama3:8b"
    session.graph = MagicMock()
    session.state = {
        "messages": [],
        "mode": "exploration",
        "party": party,
        "initiative_order": [],
        "initiative_rolls": {},
        "initiative_index": 0,
        "next_speaker": None,
        "consecutive_agent_turns": 0,
    }
    return session


def test_game_session_init():
    char = SimpleCharacter()
    with patch("dnd_bot.cli.game.build_session_graph", return_value=MagicMock()):
        session = GameSession(party=[char], provider="ollama", model="llama3:8b")
    assert session.party == [char]
    assert session.state["mode"] == "exploration"


def test_handle_slash_command_status():
    session = make_session()
    with patch("dnd_bot.cli.game.print_character_card"), \
         patch("dnd_bot.cli.game.console"):
        result = session._handle_slash_command("/status")
    assert result is True


def test_handle_slash_command_damage():
    session = make_session()
    with patch("dnd_bot.cli.game.console"):
        result = session._handle_slash_command("/damage Thorin 5")
    assert result is True
    assert session.party[0].current_hp == 23


def test_handle_slash_command_heal():
    session = make_session()
    session.party[0].current_hp = 20
    with patch("dnd_bot.cli.game.console"):
        result = session._handle_slash_command("/heal Thorin 5")
    assert result is True
    assert session.party[0].current_hp == 25


def test_handle_slash_command_mode():
    session = make_session()
    with patch("dnd_bot.cli.game.print_mode_change"), \
         patch("dnd_bot.cli.game.console"):
        result = session._handle_slash_command("/mode combat")
    assert result is True
    assert session.state["mode"] == "combat"


def test_handle_slash_command_mode_no_change_when_already_set():
    session = make_session()
    session.state["mode"] = "combat"
    with patch("dnd_bot.cli.game.print_mode_change"), \
         patch("dnd_bot.cli.game.console"):
        session._handle_slash_command("/mode combat")
    assert session.state["mode"] == "combat"


def test_initiative_add_inserts_in_order():
    session = make_session()
    with patch("dnd_bot.cli.game.console"):
        session._handle_initiative_command(["add", "Goblin", "18"])
        session._handle_initiative_command(["add", "Thorin", "12"])
    assert session.state["initiative_order"][0] == "Goblin"
    assert session.state["initiative_order"][1] == "Thorin"


def test_initiative_remove_updates_order():
    session = make_session()
    session.state["initiative_order"] = ["Vorn", "Goblin", "Yue"]
    with patch("dnd_bot.cli.game.console"):
        session._handle_initiative_command(["remove", "Goblin"])
    assert "Goblin" not in session.state["initiative_order"]
    assert len(session.state["initiative_order"]) == 2


def test_initiative_next_advances_index():
    session = make_session()
    session.state["initiative_order"] = ["Vorn", "Goblin"]
    session.state["initiative_index"] = 0
    with patch("dnd_bot.cli.game.console"):
        session._handle_initiative_command(["next"])
    assert session.state["initiative_index"] == 1


def test_initiative_next_wraps_around():
    session = make_session()
    session.state["initiative_order"] = ["Vorn", "Goblin"]
    session.state["initiative_index"] = 1
    with patch("dnd_bot.cli.game.console"):
        session._handle_initiative_command(["next"])
    assert session.state["initiative_index"] == 0


def test_get_character_case_insensitive():
    session = make_session()
    assert session._get_character("thorin") is session.party[0]
    assert session._get_character("THORIN") is session.party[0]
    assert session._get_character("nobody") is None


def test_apply_commands_targets_single_character():
    """Damage with a target should only affect that character."""
    char1 = SimpleCharacter("Vorn")
    char2 = SimpleCharacter("Yue")
    session = make_session(party=[char1, char2])

    from dnd_bot.cli.dm_parser import DMCommand
    with patch("dnd_bot.cli.game.console"):
        session._apply_commands([DMCommand(type="damage", value=5, target="Vorn")])

    assert char1.current_hp == 23
    assert char2.current_hp == 28  # Unaffected


def test_apply_commands_targets_multiple_characters():
    """Damage with comma-separated targets should affect only those characters."""
    char1 = SimpleCharacter("Vorn")
    char2 = SimpleCharacter("Yue")
    char3 = SimpleCharacter("Durgin")
    session = make_session(party=[char1, char2, char3])

    from dnd_bot.cli.dm_parser import DMCommand
    with patch("dnd_bot.cli.game.console"):
        session._apply_commands([DMCommand(type="damage", value=3, target="Vorn, Yue")])

    assert char1.current_hp == 25
    assert char2.current_hp == 25
    assert char3.current_hp == 28  # Unaffected


def test_apply_commands_no_target_affects_all():
    """Damage without a target should affect all party members (backwards compat)."""
    char1 = SimpleCharacter("Vorn")
    char2 = SimpleCharacter("Yue")
    session = make_session(party=[char1, char2])

    from dnd_bot.cli.dm_parser import DMCommand
    with patch("dnd_bot.cli.game.console"):
        session._apply_commands([DMCommand(type="damage", value=5)])

    assert char1.current_hp == 23
    assert char2.current_hp == 23
