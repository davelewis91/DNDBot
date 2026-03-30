from dnd_bot.agents.state import GameState


def test_game_state_has_required_fields():
    state: GameState = {
        "messages": [],
        "mode": "exploration",
        "party": [],
        "initiative_order": [],
        "initiative_index": 0,
        "next_speaker": None,
        "consecutive_agent_turns": 0,
    }
    assert state["mode"] == "exploration"
    assert state["next_speaker"] is None
    assert state["consecutive_agent_turns"] == 0


def test_game_state_combat_mode():
    state: GameState = {
        "messages": [],
        "mode": "combat",
        "party": [],
        "initiative_order": ["Vorn", "Goblin", "Yue"],
        "initiative_index": 1,
        "next_speaker": "Vorn",
        "consecutive_agent_turns": 2,
    }
    assert state["initiative_order"][1] == "Goblin"
    assert state["initiative_index"] == 1
