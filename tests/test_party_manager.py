from unittest.mock import MagicMock, patch

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from dnd_bot.agents.party_manager import (
    PartyManagerDecision,
    _build_initiative_section,
    _build_roster,
    make_party_manager_node,
)
from tests.helpers import make_game_state as make_state
from tests.helpers import make_mock_character as make_mock_char


def test_build_roster_lists_all_party_members():
    party = [make_mock_char("Vorn"), make_mock_char("Yue", hp=15, max_hp=20)]
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


def test_party_manager_hard_yields_at_max_turns():
    """When consecutive_agent_turns >= max_turns, yield without calling LLM."""
    party = [make_mock_char("Vorn")]
    state = make_state(party, consecutive=5)

    mock_llm = MagicMock()
    mock_llm.with_structured_output.return_value = mock_llm

    with patch("dnd_bot.agents.party_manager.get_llm", return_value=mock_llm):
        node = make_party_manager_node(max_turns=5)
        result = node(state)

    assert result["next_speaker"] is None
    assert result["consecutive_agent_turns"] == 0
    # LLM should NOT have been called
    mock_llm.invoke.assert_not_called()


def test_party_manager_yields_on_pending_check():
    """When pending_check is True, yield without calling LLM."""
    party = [make_mock_char("Vorn")]
    state = make_state(party, consecutive=1, pending_check=True)

    mock_llm = MagicMock()
    mock_llm.with_structured_output.return_value = mock_llm

    with patch("dnd_bot.agents.party_manager.get_llm", return_value=mock_llm):
        node = make_party_manager_node()
        result = node(state)

    assert result["next_speaker"] is None
    assert result["consecutive_agent_turns"] == 0
    assert result["pending_check"] is False
    mock_llm.invoke.assert_not_called()


def test_party_manager_includes_ai_message_before_tool_messages():
    """When recent messages are ToolMessages, the window extends to include their AIMessage."""
    party = [make_mock_char("Vorn")]
    ai_msg = AIMessage(
        content="I attack!",
        tool_calls=[
            {"id": "tc1", "name": "change_mode", "args": {"new_mode": "combat"}},
            {"id": "tc2", "name": "attack", "args": {}},
            {"id": "tc3", "name": "skill_check", "args": {}},
        ],
    )
    messages = [
        HumanMessage(content="Bandits ambush you!"),
        ai_msg,
        ToolMessage(content="Mode changed to combat", tool_call_id="tc1"),
        ToolMessage(content="Attack result: 15", tool_call_id="tc2"),
        ToolMessage(content="Check result: 12", tool_call_id="tc3"),
    ]
    state = make_state(party, messages=messages)

    mock_decision = PartyManagerDecision(next_speaker="Vorn")
    mock_llm = MagicMock()
    mock_llm.with_structured_output.return_value = mock_llm
    mock_llm.invoke.return_value = mock_decision

    with patch("dnd_bot.agents.party_manager.get_llm", return_value=mock_llm):
        node = make_party_manager_node()
        node(state)

    call_args = mock_llm.invoke.call_args[0][0]
    conversation_msgs = [m for m in call_args if not isinstance(m, SystemMessage)]
    # Must include the AIMessage plus its ToolMessages, not just ToolMessages
    assert any(isinstance(m, AIMessage) for m in conversation_msgs)


def test_party_manager_yields_when_all_messages_are_orphaned():
    """If all recent messages are orphaned ToolMessages, yield to DM."""
    party = [make_mock_char("Vorn")]
    # ToolMessages without a matching AIMessage in the history
    messages = [
        ToolMessage(content="result1", tool_call_id="orphan1"),
        ToolMessage(content="result2", tool_call_id="orphan2"),
    ]
    state = make_state(party, messages=messages)

    mock_llm = MagicMock()
    mock_llm.with_structured_output.return_value = mock_llm

    with patch("dnd_bot.agents.party_manager.get_llm", return_value=mock_llm):
        node = make_party_manager_node()
        result = node(state)

    assert result["next_speaker"] is None
    mock_llm.invoke.assert_not_called()
