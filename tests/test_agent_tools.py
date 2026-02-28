from unittest.mock import MagicMock, patch

from dnd_bot.agents.tools import ToolContext, build_tools


def make_mock_character():
    char = MagicMock()
    char.name = "Thorin"
    char.current_hp = 28
    char.max_hp = 32
    char.conditions = []
    char.equipment.weapon_ids = []
    char.make_skill_check.return_value = (18, 14)   # (total, die_roll)
    char.make_ability_check.return_value = (15, 13)
    char.make_saving_throw.return_value = (12, 10)
    char.make_attack_roll.return_value = (17, 14)
    return char


def make_mock_weapon(name="Longsword", damage_dice="1d8", damage_type="slashing",
                     is_finesse=False, is_ranged=False, versatile_dice=None):
    weapon = MagicMock()
    weapon.name = name
    weapon.damage_dice = damage_dice
    weapon.damage_type.value = damage_type
    weapon.is_finesse = is_finesse
    weapon.is_ranged = is_ranged
    weapon.versatile_dice = versatile_dice
    return weapon


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


def test_attack_with_weapon_includes_damage():
    char = make_mock_character()
    char.equipment.weapon_ids = ["longsword"]
    char.get_ability_modifier.return_value = 3  # +3 STR
    weapon = make_mock_weapon()

    with patch("dnd_bot.agents.tools.get_weapon", return_value=weapon):
        with patch("dnd_bot.agents.tools.roll") as mock_roll:
            mock_roll.return_value.total = 6
            ctx = ToolContext(character=char)
            tools = {t.name: t for t in build_tools(ctx)}
            result = tools["attack"].invoke({"target": "goblin", "weapon": "longsword"})

    assert "Longsword" in result
    assert "17" in result   # to-hit total from make_attack_roll mock
    assert "9" in result    # damage: 6 (roll) + 3 (str mod)
    assert "slashing" in result


def test_attack_with_versatile_weapon_two_handed():
    char = make_mock_character()
    char.equipment.weapon_ids = ["longsword"]
    char.get_ability_modifier.return_value = 2
    weapon = make_mock_weapon(versatile_dice="1d10")

    with patch("dnd_bot.agents.tools.get_weapon", return_value=weapon):
        with patch("dnd_bot.agents.tools.roll") as mock_roll:
            mock_roll.return_value.total = 7
            ctx = ToolContext(character=char)
            tools = {t.name: t for t in build_tools(ctx)}
            result = tools["attack"].invoke(
                {"target": "goblin", "weapon": "longsword", "two_handed": True}
            )

    # Should have used versatile_dice ("1d10") not damage_dice ("1d8")
    mock_roll.assert_called_once_with("1d10")
    assert "9" in result    # damage: 7 + 2


def test_attack_with_finesse_weapon_uses_better_modifier():
    char = make_mock_character()
    char.equipment.weapon_ids = ["rapier"]
    # DEX mod (+4) > STR mod (+1), so should pick DEX
    char.get_ability_modifier.side_effect = lambda ability: (
        1 if ability.value == "strength" else 4
    )
    weapon = make_mock_weapon(name="Rapier", is_finesse=True)

    with patch("dnd_bot.agents.tools.get_weapon", return_value=weapon):
        with patch("dnd_bot.agents.tools.roll") as mock_roll:
            mock_roll.return_value.total = 5
            ctx = ToolContext(character=char)
            tools = {t.name: t for t in build_tools(ctx)}
            result = tools["attack"].invoke({"target": "bandit", "weapon": "rapier"})

    # DEX (+4) chosen over STR (+1) — damage = 5 + 4 = 9
    assert "9" in result


def test_attack_unknown_weapon_returns_error():
    char = make_mock_character()
    char.equipment.weapon_ids = ["longsword"]
    ctx = ToolContext(character=char)
    tools = {t.name: t for t in build_tools(ctx)}
    result = tools["attack"].invoke({"target": "goblin", "weapon": "axe"})
    assert "axe" in result.lower()
    assert "longsword" in result
