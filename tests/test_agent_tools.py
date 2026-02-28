from unittest.mock import MagicMock
from dnd_bot.agents.tools import build_tools, ToolContext


def make_mock_character():
    char = MagicMock()
    char.name = "Thorin"
    char.current_hp = 28
    char.max_hp = 32
    char.conditions = []
    char.equipment = []
    char.make_skill_check.return_value = (18, 14)   # (total, die_roll)
    char.make_ability_check.return_value = (15, 13)
    char.make_saving_throw.return_value = (12, 10)
    char.make_attack_roll.return_value = (17, 14)
    return char


def test_build_tools_returns_list():
    char = make_mock_character()
    ctx = ToolContext(character=char)
    tools = build_tools(ctx)
    assert len(tools) > 0


def test_check_status_tool():
    char = make_mock_character()
    ctx = ToolContext(character=char)
    tools = {t.name: t for t in build_tools(ctx)}
    result = tools["check_status"].invoke({})
    assert "Thorin" in result
    assert "28/32" in result


def test_skill_check_tool():
    char = make_mock_character()
    ctx = ToolContext(character=char)
    tools = {t.name: t for t in build_tools(ctx)}
    result = tools["skill_check"].invoke({"skill": "perception"})
    assert "Perception" in result
    assert "18" in result


def test_ability_check_tool():
    char = make_mock_character()
    ctx = ToolContext(character=char)
    tools = {t.name: t for t in build_tools(ctx)}
    result = tools["ability_check"].invoke({"ability": "strength"})
    assert "Strength" in result
    assert "15" in result


def test_speak_tool():
    char = make_mock_character()
    ctx = ToolContext(character=char)
    tools = {t.name: t for t in build_tools(ctx)}
    result = tools["speak"].invoke({"message": "Hello there!"})
    assert "Hello there!" in result


def test_describe_action_tool():
    char = make_mock_character()
    ctx = ToolContext(character=char)
    tools = {t.name: t for t in build_tools(ctx)}
    result = tools["describe_action"].invoke({"action": "looks around carefully"})
    assert "looks around carefully" in result
