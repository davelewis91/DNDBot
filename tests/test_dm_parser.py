from unittest.mock import MagicMock, patch

from dnd_bot.cli.dm_parser import DMCommand, DMIntent, parse_dm_input


def mock_llm_response(json_str: str):
    mock = MagicMock()
    mock.content = json_str
    return mock


def test_parse_dm_input_narrative_passthrough():
    with patch("dnd_bot.cli.dm_parser.get_llm") as mock_get_llm:
        llm = MagicMock()
        llm.invoke.return_value = mock_llm_response(
            '{"narrative": "You see a goblin.", "commands": []}'
        )
        mock_get_llm.return_value = llm
        result = parse_dm_input("You see a goblin.", provider="ollama")
    assert result.narrative == "You see a goblin."
    assert result.commands == []


def test_parse_dm_input_extracts_damage():
    with patch("dnd_bot.cli.dm_parser.get_llm") as mock_get_llm:
        llm = MagicMock()
        llm.invoke.return_value = mock_llm_response(
            '{"narrative": "The goblin hits you.", '
            '"commands": [{"type": "damage", "value": 5}]}'
        )
        mock_get_llm.return_value = llm
        result = parse_dm_input("The goblin hits for 5 damage.", provider="ollama")
    assert any(c.type == "damage" and c.value == 5 for c in result.commands)


def test_dm_intent_has_narrative_and_commands():
    intent = DMIntent(narrative="test", commands=[])
    assert intent.narrative == "test"
    assert intent.commands == []


def test_dm_command_types():
    cmd = DMCommand(type="damage", value=3)
    assert cmd.type == "damage"
    assert cmd.value == 3
