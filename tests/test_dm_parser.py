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


def test_parse_dm_input_detects_combat_mode():
    with patch("dnd_bot.cli.dm_parser.get_llm") as mock_get_llm:
        llm = MagicMock()
        llm.invoke.return_value = mock_llm_response(
            '{"narrative": "Roll for initiative!", '
            '"commands": [{"type": "mode", "value": "combat"}]}'
        )
        mock_get_llm.return_value = llm
        result = parse_dm_input("Roll for initiative!", provider="ollama")
    assert any(c.type == "mode" and c.value == "combat" for c in result.commands)


def test_parse_dm_input_detects_exploration_mode_after_combat():
    with patch("dnd_bot.cli.dm_parser.get_llm") as mock_get_llm:
        llm = MagicMock()
        llm.invoke.return_value = mock_llm_response(
            '{"narrative": "The goblin falls dead.", '
            '"commands": [{"type": "mode", "value": "exploration"}]}'
        )
        mock_get_llm.return_value = llm
        result = parse_dm_input("The goblin falls dead.", provider="ollama")
    assert any(c.type == "mode" and c.value == "exploration" for c in result.commands)


def test_parse_dm_input_does_not_emit_roleplay_mode():
    with patch("dnd_bot.cli.dm_parser.get_llm") as mock_get_llm:
        llm = MagicMock()
        llm.invoke.return_value = mock_llm_response(
            '{"narrative": "The innkeeper addresses you.", "commands": []}'
        )
        mock_get_llm.return_value = llm
        result = parse_dm_input("The innkeeper addresses you.", provider="ollama")
    assert not any(c.type == "mode" and c.value == "roleplay" for c in result.commands)


def test_parse_dm_input_detects_damage():
    with patch("dnd_bot.cli.dm_parser.get_llm") as mock_get_llm:
        llm = MagicMock()
        llm.invoke.return_value = mock_llm_response(
            '{"narrative": "You take 3 piercing damage.", '
            '"commands": [{"type": "damage", "value": 3}]}'
        )
        mock_get_llm.return_value = llm
        result = parse_dm_input("You take 3 piercing damage.", provider="ollama")
    assert any(c.type == "damage" and c.value == 3 for c in result.commands)


def test_parse_dm_input_detects_healing():
    with patch("dnd_bot.cli.dm_parser.get_llm") as mock_get_llm:
        llm = MagicMock()
        llm.invoke.return_value = mock_llm_response(
            '{"narrative": "The potion restores 8 hit points.", '
            '"commands": [{"type": "heal", "value": 8}]}'
        )
        mock_get_llm.return_value = llm
        result = parse_dm_input("The potion restores 8 hit points.", provider="ollama")
    assert any(c.type == "heal" and c.value == 8 for c in result.commands)


def test_parse_dm_input_handles_markdown_wrapped_json():
    with patch("dnd_bot.cli.dm_parser.get_llm") as mock_get_llm:
        llm = MagicMock()
        llm.invoke.return_value = mock_llm_response(
            '```json\n{"narrative": "You take 5 damage.", '
            '"commands": [{"type": "damage", "value": 5}]}\n```'
        )
        mock_get_llm.return_value = llm
        result = parse_dm_input("You take 5 damage.", provider="ollama")
    assert any(c.type == "damage" and c.value == 5 for c in result.commands)
