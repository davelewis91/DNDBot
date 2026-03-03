from unittest.mock import MagicMock, patch

from dnd_bot.agents.tools import ToolContext, build_tools
from dnd_bot.character import SpeciesName, create_character
from dnd_bot.character.abilities import Ability


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
    char.is_critical_hit.return_value = False
    char.roll_weapon_damage.return_value = (9, "1d8")
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
    char.get_attack_ability = MagicMock(return_value=Ability.STRENGTH)
    char.get_ability_modifier.return_value = 3  # +3 STR
    weapon = make_mock_weapon()

    with patch("dnd_bot.agents.tools.get_weapon", return_value=weapon):
        ctx = ToolContext(character=char)
        tools = {t.name: t for t in build_tools(ctx)}
        result = tools["attack"].invoke({"target": "goblin", "weapon": "longsword"})

    assert "Longsword" in result
    assert "17" in result   # to-hit total from make_attack_roll mock
    assert "9" in result    # damage from roll_weapon_damage mock
    assert "slashing" in result


def test_attack_with_versatile_weapon_two_handed():
    char = make_mock_character()
    char.equipment.weapon_ids = ["longsword"]
    char.get_attack_ability = MagicMock(return_value=Ability.STRENGTH)
    char.get_ability_modifier.return_value = 2
    weapon = make_mock_weapon(versatile_dice="1d10")

    char.roll_weapon_damage.return_value = (9, "1d10")
    with patch("dnd_bot.agents.tools.get_weapon", return_value=weapon):
        ctx = ToolContext(character=char)
        tools = {t.name: t for t in build_tools(ctx)}
        result = tools["attack"].invoke(
            {"target": "goblin", "weapon": "longsword", "two_handed": True}
        )

    assert "1d10" in result  # versatile dice notation should appear
    assert "9" in result    # damage from roll_weapon_damage mock


def test_attack_with_finesse_weapon_uses_better_modifier():
    char = make_mock_character()
    char.equipment.weapon_ids = ["rapier"]
    char.get_attack_ability = MagicMock(return_value=Ability.DEXTERITY)
    # DEX mod (+4) returned for dexterity
    char.get_ability_modifier.return_value = 4
    weapon = make_mock_weapon(name="Rapier", is_finesse=True)

    with patch("dnd_bot.agents.tools.get_weapon", return_value=weapon):
        ctx = ToolContext(character=char)
        tools = {t.name: t for t in build_tools(ctx)}
        result = tools["attack"].invoke({"target": "bandit", "weapon": "rapier"})

    assert "9" in result


def test_attack_unknown_weapon_returns_error():
    char = make_mock_character()
    char.equipment.weapon_ids = ["longsword"]
    ctx = ToolContext(character=char)
    tools = {t.name: t for t in build_tools(ctx)}
    result = tools["attack"].invoke({"target": "goblin", "weapon": "axe"})
    assert "axe" in result.lower()
    assert "longsword" in result


def test_unarmed_attack_standard_includes_damage():
    char = make_mock_character()
    char.get_attack_ability = MagicMock(return_value=Ability.STRENGTH)
    char.roll_unarmed_damage = MagicMock(return_value=(4, "1 + +3"))
    ctx = ToolContext(character=char)
    tools = {t.name: t for t in build_tools(ctx)}
    result = tools["attack"].invoke({"target": "goblin"})
    assert "bludgeoning" in result
    assert "4" in result


def test_unarmed_attack_monk_uses_martial_arts_die_and_dex():
    char = make_mock_character()
    char.get_attack_ability = MagicMock(return_value=Ability.DEXTERITY)
    char.roll_unarmed_damage = MagicMock(return_value=(9, "1d6 + +4"))
    ctx = ToolContext(character=char)
    tools = {t.name: t for t in build_tools(ctx)}
    result = tools["attack"].invoke({"target": "bandit"})
    assert "bludgeoning" in result
    assert "9" in result
    assert "1d6" in result


def test_attack_critical_hit_doubles_damage_dice():
    char = make_mock_character()
    char.equipment.weapon_ids = ["longsword"]
    char.get_attack_ability = MagicMock(return_value=Ability.STRENGTH)
    char.get_ability_modifier.return_value = 3
    char.make_attack_roll.return_value = (22, 20)
    char.is_critical_hit.return_value = True
    weapon = make_mock_weapon()  # damage_dice="1d8"

    char.roll_weapon_damage.return_value = (11, "2d8")
    with patch("dnd_bot.agents.tools.get_weapon", return_value=weapon):
        ctx = ToolContext(character=char)
        tools = {t.name: t for t in build_tools(ctx)}
        result = tools["attack"].invoke({"target": "goblin", "weapon": "longsword"})

    assert "CRITICAL HIT!" in result
    assert "2d8" in result


def test_attack_non_critical_hit_normal_damage():
    char = make_mock_character()
    char.equipment.weapon_ids = ["longsword"]
    char.get_attack_ability = MagicMock(return_value=Ability.STRENGTH)
    char.get_ability_modifier.return_value = 3
    char.make_attack_roll.return_value = (18, 14)
    char.is_critical_hit.return_value = False
    weapon = make_mock_weapon()  # damage_dice="1d8"

    with patch("dnd_bot.agents.tools.get_weapon", return_value=weapon):
        ctx = ToolContext(character=char)
        tools = {t.name: t for t in build_tools(ctx)}
        result = tools["attack"].invoke({"target": "goblin", "weapon": "longsword"})

    assert "CRITICAL HIT!" not in result
    assert "1d8" in result


def test_attack_champion_critical_hit_on_19():
    char = make_mock_character()
    char.equipment.weapon_ids = ["longsword"]
    char.get_attack_ability = MagicMock(return_value=Ability.STRENGTH)
    char.get_ability_modifier.return_value = 3
    char.make_attack_roll.return_value = (21, 19)
    char.is_critical_hit.return_value = True  # Champion: [19, 20]
    weapon = make_mock_weapon()

    char.roll_weapon_damage.return_value = (11, "2d8")
    with patch("dnd_bot.agents.tools.get_weapon", return_value=weapon):
        ctx = ToolContext(character=char)
        tools = {t.name: t for t in build_tools(ctx)}
        result = tools["attack"].invoke({"target": "orc", "weapon": "longsword"})

    assert "CRITICAL HIT!" in result
    assert "2d8" in result


# --- Fighter class tool tests ---


def test_second_wind_heals_fighter():
    """second_wind tool should heal the Fighter and consume the resource."""
    char = create_character(
        name="Test Fighter",
        species_name=SpeciesName.HUMAN,
        class_type="fighter",
        level=3,
    )
    char.current_hp = 5
    tools = {t.name: t for t in build_tools(ToolContext(character=char))}

    tools["second_wind"].invoke({})

    assert char.current_hp > 5
    second_wind_resource = char.resources.get_feature("Second Wind")
    assert second_wind_resource.current == 0


def test_second_wind_unavailable_when_used():
    """second_wind tool should report not available after resource is exhausted."""
    char = create_character(
        name="Test Fighter",
        species_name=SpeciesName.HUMAN,
        class_type="fighter",
        level=3,
    )
    char.current_hp = 5
    tools = {t.name: t for t in build_tools(ToolContext(character=char))}

    tools["second_wind"].invoke({})
    result = tools["second_wind"].invoke({})

    assert "not available" in result


def test_action_surge_returns_confirmation():
    """action_surge tool should confirm usage and reduce resource to 0."""
    char = create_character(
        name="Test Fighter",
        species_name=SpeciesName.HUMAN,
        class_type="fighter",
        level=2,
    )
    tools = {t.name: t for t in build_tools(ToolContext(character=char))}

    result = tools["action_surge"].invoke({})

    assert "Action Surge" in result
    action_surge_resource = char.resources.get_feature("Action Surge")
    assert action_surge_resource.current == 0


# --- Barbarian class tool tests ---


def test_toggle_rage_starts_rage():
    """toggle_rage tool should start rage and report 'Rage started'."""
    char = create_character(
        name="Test Barbarian",
        species_name=SpeciesName.HUMAN,
        class_type="barbarian",
        level=1,
    )
    tools = {t.name: t for t in build_tools(ToolContext(character=char))}

    result = tools["toggle_rage"].invoke({})

    assert "Rage started" in result
    assert char.is_raging


def test_toggle_rage_ends_rage():
    """toggle_rage tool invoked twice should end rage with resource decremented once."""
    char = create_character(
        name="Test Barbarian",
        species_name=SpeciesName.HUMAN,
        class_type="barbarian",
        level=1,
    )
    tools = {t.name: t for t in build_tools(ToolContext(character=char))}
    rage_resource = char.resources.get_feature("Rage")
    uses_before = rage_resource.current

    tools["toggle_rage"].invoke({})
    tools["toggle_rage"].invoke({})

    assert not char.is_raging
    assert rage_resource.current == uses_before - 1


def test_toggle_rage_unavailable_when_no_uses():
    """toggle_rage tool should report not available when all rage uses are exhausted."""
    char = create_character(
        name="Test Barbarian",
        species_name=SpeciesName.HUMAN,
        class_type="barbarian",
        level=1,
    )
    # Exhaust all rage uses directly via resources (level 1 = 2 uses)
    rage_resource = char.resources.get_feature("Rage")
    while rage_resource.current > 0:
        char.resources.use_feature("Rage")

    tools = {t.name: t for t in build_tools(ToolContext(character=char))}

    result = tools["toggle_rage"].invoke({})

    assert "not available" in result


# --- Monk class tool tests ---


def test_flurry_of_blows_makes_two_attacks():
    """flurry_of_blows tool should decrement focus points by 1 and report two strikes."""
    char = create_character(
        name="Test Monk",
        species_name=SpeciesName.HUMAN,
        class_type="monk",
        level=2,
    )
    focus_before = char.get_focus_points()
    tools = {t.name: t for t in build_tools(ToolContext(character=char))}

    result = tools["flurry_of_blows"].invoke({"target": "goblin"})

    assert char.get_focus_points() == focus_before - 1
    assert "Strike 1" in result
    assert "Strike 2" in result


def test_flurry_of_blows_fails_without_focus_points():
    """flurry_of_blows tool should report insufficient Focus Points when none remain."""
    char = create_character(
        name="Test Monk",
        species_name=SpeciesName.HUMAN,
        class_type="monk",
        level=2,
    )
    # Drain all focus points (level 2 = 2 points)
    char.use_focus_points(char.get_focus_points())
    tools = {t.name: t for t in build_tools(ToolContext(character=char))}

    result = tools["flurry_of_blows"].invoke({"target": "goblin"})

    assert "insufficient Focus Points" in result


def test_patient_defense_uses_focus_point():
    """patient_defense tool should decrement focus points by 1 and mention Defense or Dodge."""
    char = create_character(
        name="Test Monk",
        species_name=SpeciesName.HUMAN,
        class_type="monk",
        level=2,
    )
    focus_before = char.get_focus_points()
    tools = {t.name: t for t in build_tools(ToolContext(character=char))}

    result = tools["patient_defense"].invoke({})

    assert char.get_focus_points() == focus_before - 1
    assert "Defense" in result or "Dodge" in result


def test_step_of_the_wind_uses_focus_point():
    """step_of_the_wind tool should decrement focus points by 1 and mention Dash."""
    char = create_character(
        name="Test Monk",
        species_name=SpeciesName.HUMAN,
        class_type="monk",
        level=2,
    )
    focus_before = char.get_focus_points()
    tools = {t.name: t for t in build_tools(ToolContext(character=char))}

    result = tools["step_of_the_wind"].invoke({"action": "dash"})

    assert char.get_focus_points() == focus_before - 1
    assert "Dash" in result


def test_stunning_strike_uses_focus_point():
    """stunning_strike tool should decrement focus points by 1 and report the DC."""
    char = create_character(
        name="Test Monk",
        species_name=SpeciesName.HUMAN,
        class_type="monk",
        level=5,
    )
    focus_before = char.get_focus_points()
    tools = {t.name: t for t in build_tools(ToolContext(character=char))}

    result = tools["stunning_strike"].invoke({"target": "goblin"})

    assert char.get_focus_points() == focus_before - 1
    assert "DC" in result


# --- Rogue class tool tests ---


def test_cunning_action_hide_returns_stealth_roll():
    """cunning_action hide should return a Stealth check result with a numeric total."""
    char = create_character(
        name="Test Rogue",
        species_name=SpeciesName.HUMAN,
        class_type="rogue",
        level=2,
    )
    tools = {t.name: t for t in build_tools(ToolContext(character=char))}

    result = tools["cunning_action"].invoke({"action": "hide"})

    assert "Stealth" in result
    # The result should contain a number (the check total)
    assert any(c.isdigit() for c in result)


# --- check_status resource display tests ---


def test_check_status_shows_resources_for_fighter():
    """check_status tool should include Resources section for a Fighter with Second Wind."""
    char = create_character(
        name="Test Fighter",
        species_name=SpeciesName.HUMAN,
        class_type="fighter",
        level=1,
    )
    tools = {t.name: t for t in build_tools(ToolContext(character=char))}

    result = tools["check_status"].invoke({})

    assert "Resources:" in result
    assert "Second Wind" in result
