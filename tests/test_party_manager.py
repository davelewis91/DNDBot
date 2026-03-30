from unittest.mock import MagicMock, patch

from langchain_core.messages import HumanMessage, SystemMessage

from dnd_bot.agents.party_manager import (
    PartyManagerDecision,
    _build_initiative_section,
    _build_roster,
    make_party_manager_node,
)


def make_mock_char(name, hp=20, max_hp=20, conditions=None):
    char = MagicMock()
    char.name = name
    char.current_hp = hp
    char.max_hp = max_hp
    char.conditions = conditions or []
    return char


def make_state(party, mode="exploration", initiative_order=None, consecutive=0):
    return {
        "messages": [HumanMessage(content="You enter a tavern.")],
        "mode": mode,
        "party": party,
        "initiative_order": initiative_order or [],
        "initiative_index": 0,
        "next_speaker": None,
        "consecutive_agent_turns": consecutive,
    }


def test_build_roster_lists_all_party_members():
    party = [make_mock_char("Vorn"), make_mock_char("Yue", hp=15)]
    state = make_state(party)
    roster = _build_roster(state)
    assert "Vorn" in roster
    assert "Yue" in roster
    assert "15/20" in roster


def test_build_initiative_section_empty_outside_combat():
    party = [make_mock_char("Vorn")]
    state = make_state(party, mode="exploration")
    section = _build_initiative_section(state)
    assert section == ""


def test_build_initiative_section_shows_current_turn():
    party = [make_mock_char("Vorn"), make_mock_char("Goblin")]
    state = make_state(
        party, mode="combat",
        initiative_order=["Vorn", "Goblin"],
    )
    state["initiative_index"] = 1
    section = _build_initiative_section(state)
    assert "Goblin" in section
    assert "Current turn" in section


def test_party_manager_routes_to_next_speaker():
    party = [make_mock_char("Vorn"), make_mock_char("Yue")]
    state = make_state(party)

    mock_decision = PartyManagerDecision(next_speaker="Vorn", yield_to_dm=False)
    mock_llm = MagicMock()
    mock_llm.with_structured_output.return_value = mock_llm
    mock_llm.invoke.return_value = mock_decision

    with patch("dnd_bot.agents.party_manager.get_llm", return_value=mock_llm):
        node = make_party_manager_node()
        result = node(state)

    assert result["next_speaker"] == "Vorn"


def test_party_manager_yields_to_dm():
    party = [make_mock_char("Vorn")]
    state = make_state(party)

    mock_decision = PartyManagerDecision(yield_to_dm=True)
    mock_llm = MagicMock()
    mock_llm.with_structured_output.return_value = mock_llm
    mock_llm.invoke.return_value = mock_decision

    with patch("dnd_bot.agents.party_manager.get_llm", return_value=mock_llm):
        node = make_party_manager_node()
        result = node(state)

    assert result["next_speaker"] is None
    assert result["consecutive_agent_turns"] == 0


def test_party_manager_resets_consecutive_turns_on_yield():
    party = [make_mock_char("Vorn")]
    state = make_state(party, consecutive=4)

    mock_decision = PartyManagerDecision(yield_to_dm=True)
    mock_llm = MagicMock()
    mock_llm.with_structured_output.return_value = mock_llm
    mock_llm.invoke.return_value = mock_decision

    with patch("dnd_bot.agents.party_manager.get_llm", return_value=mock_llm):
        node = make_party_manager_node()
        result = node(state)

    assert result["consecutive_agent_turns"] == 0


def test_party_manager_receives_only_recent_messages():
    """Party manager should only see the last 3 messages, not full history."""
    party = [make_mock_char("Vorn")]
    state = make_state(party)
    # Add many messages to history
    state["messages"] = [
        HumanMessage(content=f"Message {i}") for i in range(20)
    ]

    mock_decision = PartyManagerDecision(next_speaker="Vorn")
    mock_llm = MagicMock()
    mock_llm.with_structured_output.return_value = mock_llm
    mock_llm.invoke.return_value = mock_decision

    with patch("dnd_bot.agents.party_manager.get_llm", return_value=mock_llm):
        node = make_party_manager_node()
        node(state)

    # Check the messages passed to invoke: [SystemMessage] + last 3
    call_args = mock_llm.invoke.call_args[0][0]
    # First message is SystemMessage (the prompt), rest are conversation messages
    conversation_msgs = [m for m in call_args if not isinstance(m, SystemMessage)]
    assert len(conversation_msgs) == 3
    assert conversation_msgs[-1].content == "Message 19"
