from unittest.mock import MagicMock, patch

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from dnd_bot.agents.party_manager import (
    PartyManagerDecision,
    _build_initiative_section,
    _build_roster,
    _characters_acted_since_last_dm,
    _next_combat_speaker,
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


# --- Deterministic combat routing tests ---


def test_combat_routing_returns_active_character():
    """In combat, the party manager should route to the active character."""
    party = [make_mock_char("Vorn"), make_mock_char("Yue")]
    state = make_state(
        party, mode="combat",
        combat_role={"Vorn": "active"},
    )

    mock_llm = MagicMock()
    mock_llm.with_structured_output.return_value = mock_llm

    with patch("dnd_bot.agents.party_manager.get_llm", return_value=mock_llm):
        node = make_party_manager_node()
        result = node(state)

    assert result["next_speaker"] == "Vorn"
    mock_llm.invoke.assert_not_called()


def test_combat_routing_skips_llm():
    """In combat mode, the LLM should never be called for routing."""
    party = [make_mock_char("Vorn")]
    state = make_state(
        party, mode="combat",
        combat_role={"Vorn": "active"},
    )

    mock_llm = MagicMock()
    mock_llm.with_structured_output.return_value = mock_llm

    with patch("dnd_bot.agents.party_manager.get_llm", return_value=mock_llm):
        node = make_party_manager_node()
        node(state)

    mock_llm.invoke.assert_not_called()


def test_combat_routing_yields_when_all_served():
    """After all combat roles are served, yield to DM."""
    party = [make_mock_char("Vorn")]
    messages = [
        HumanMessage(content="Your turn Vorn"),
        AIMessage(content="I attack!", additional_kwargs={"character_name": "Vorn"}),
    ]
    state = make_state(
        party, mode="combat", messages=messages,
        combat_role={"Vorn": "active"}, consecutive=1,
    )

    mock_llm = MagicMock()
    mock_llm.with_structured_output.return_value = mock_llm

    with patch("dnd_bot.agents.party_manager.get_llm", return_value=mock_llm):
        node = make_party_manager_node()
        result = node(state)

    assert result["next_speaker"] is None


def test_combat_routing_active_before_targeted():
    """Active character should be routed before targeted characters."""
    party = [make_mock_char("Vorn"), make_mock_char("Yue")]
    state = make_state(
        party, mode="combat",
        combat_role={"Vorn": "active", "Yue": "targeted"},
    )

    mock_llm = MagicMock()
    mock_llm.with_structured_output.return_value = mock_llm

    with patch("dnd_bot.agents.party_manager.get_llm", return_value=mock_llm):
        node = make_party_manager_node()
        result = node(state)

    assert result["next_speaker"] == "Vorn"


def test_combat_routing_routes_targeted_after_active_served():
    """Once active character has acted, route to targeted character."""
    party = [make_mock_char("Vorn"), make_mock_char("Yue")]
    messages = [
        HumanMessage(content="Your turn Vorn"),
        AIMessage(content="I attack!", additional_kwargs={"character_name": "Vorn"}),
    ]
    state = make_state(
        party, mode="combat", messages=messages,
        combat_role={"Vorn": "active", "Yue": "targeted"}, consecutive=1,
    )

    mock_llm = MagicMock()
    mock_llm.with_structured_output.return_value = mock_llm

    with patch("dnd_bot.agents.party_manager.get_llm", return_value=mock_llm):
        node = make_party_manager_node()
        result = node(state)

    assert result["next_speaker"] == "Yue"


def test_combat_routing_yields_on_pending_check():
    """pending_check should force yield even in combat mode."""
    party = [make_mock_char("Vorn")]
    state = make_state(
        party, mode="combat", pending_check=True,
        combat_role={"Vorn": "active"},
    )

    mock_llm = MagicMock()
    mock_llm.with_structured_output.return_value = mock_llm

    with patch("dnd_bot.agents.party_manager.get_llm", return_value=mock_llm):
        node = make_party_manager_node()
        result = node(state)

    assert result["next_speaker"] is None
    assert result["pending_check"] is False


def test_combat_routing_empty_role_yields():
    """If combat_role is empty (no initiative), yield to DM."""
    party = [make_mock_char("Vorn")]
    state = make_state(party, mode="combat", combat_role={})

    mock_llm = MagicMock()
    mock_llm.with_structured_output.return_value = mock_llm

    with patch("dnd_bot.agents.party_manager.get_llm", return_value=mock_llm):
        node = make_party_manager_node()
        result = node(state)

    assert result["next_speaker"] is None


def test_characters_acted_since_last_dm_finds_speakers():
    messages = [
        HumanMessage(content="DM says something"),
        AIMessage(content="I act", additional_kwargs={"character_name": "Vorn"}),
        AIMessage(content="Me too", additional_kwargs={"character_name": "Yue"}),
    ]
    acted = _characters_acted_since_last_dm(messages)
    assert acted == {"Vorn", "Yue"}


def test_characters_acted_since_last_dm_resets_on_new_human_message():
    messages = [
        HumanMessage(content="First DM turn"),
        AIMessage(content="I act", additional_kwargs={"character_name": "Vorn"}),
        HumanMessage(content="Second DM turn"),
        AIMessage(content="I act", additional_kwargs={"character_name": "Yue"}),
    ]
    acted = _characters_acted_since_last_dm(messages)
    assert acted == {"Yue"}


def test_next_combat_speaker_returns_none_when_all_served():
    state = make_state(
        [make_mock_char("Vorn")], mode="combat",
        combat_role={"Vorn": "active"},
        messages=[
            HumanMessage(content="Go"),
            AIMessage(content="I act", additional_kwargs={"character_name": "Vorn"}),
        ],
    )
    assert _next_combat_speaker(state) is None
