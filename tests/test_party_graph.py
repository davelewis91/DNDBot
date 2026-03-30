from unittest.mock import MagicMock, patch

from langchain_core.messages import AIMessage, HumanMessage

from dnd_bot.agents.party_graph import build_party_graph
from dnd_bot.agents.party_manager import PartyManagerDecision


def make_mock_char(name="Vorn"):
    char = MagicMock()
    char.name = name
    char.current_hp = 20
    char.max_hp = 20
    char.level = 1
    char.conditions = []
    char.class_features = []
    char.resources.feature_uses = {}
    char.get_ability_modifier.return_value = 0
    char.get_skill_bonus.return_value = 0
    char.skills.get_proficient_skills.return_value = []
    char.equipment.item_names.return_value = []
    char.species.name.value = "human"
    char.background.to_prompt_context.return_value = "A simple background."
    return char


def make_initial_state(party):
    return {
        "messages": [HumanMessage(content="The DM speaks.")],
        "mode": "exploration",
        "party": party,
        "initiative_order": [],
        "initiative_index": 0,
        "next_speaker": None,
        "consecutive_agent_turns": 0,
    }


def test_party_graph_yields_to_dm_immediately():
    """When party_manager immediately yields, graph exits without calling player_node."""
    char = make_mock_char()
    state = make_initial_state([char])

    yield_decision = PartyManagerDecision(yield_to_dm=True)
    mock_manager_llm = MagicMock()
    mock_manager_llm.with_structured_output.return_value = mock_manager_llm
    mock_manager_llm.invoke.return_value = yield_decision

    with patch("dnd_bot.agents.party_manager.get_llm", return_value=mock_manager_llm):
        graph = build_party_graph()
        result = graph.invoke(state)

    assert result["next_speaker"] is None
    assert result["consecutive_agent_turns"] == 0


def test_party_graph_routes_to_player_then_yields():
    """party_manager → player_node → party_manager (yields) — 2 manager calls, 1 player call."""
    char = make_mock_char("Vorn")
    state = make_initial_state([char])

    speak_decision = PartyManagerDecision(next_speaker="Vorn")
    yield_decision = PartyManagerDecision(yield_to_dm=True)

    mock_manager_llm = MagicMock()
    mock_manager_llm.with_structured_output.return_value = mock_manager_llm
    mock_manager_llm.invoke.side_effect = [speak_decision, yield_decision]

    mock_player_response = MagicMock(spec=AIMessage)
    mock_player_response.content = "Vorn speaks."
    mock_player_response.tool_calls = []
    mock_player_response.additional_kwargs = {}
    mock_player_response.id = "msg-1"
    mock_player_response.type = "ai"
    mock_player_llm = MagicMock()
    mock_player_llm.bind_tools.return_value = mock_player_llm
    mock_player_llm.invoke.return_value = mock_player_response

    with (
        patch("dnd_bot.agents.party_manager.get_llm", return_value=mock_manager_llm),
        patch("dnd_bot.agents.player_node.get_llm", return_value=mock_player_llm),
    ):
        graph = build_party_graph()
        result = graph.invoke(state)

    assert result["next_speaker"] is None
    assert result["consecutive_agent_turns"] == 0
    # One agent message was added
    agent_msgs = [m for m in result["messages"] if isinstance(m, AIMessage)]
    assert len(agent_msgs) == 1


def test_party_graph_respects_max_consecutive_turns():
    """When consecutive_agent_turns reaches max, party_manager must yield."""
    char = make_mock_char("Vorn")
    state = make_initial_state([char])

    # Manager always wants to speak but max_turns=1 forces yield after 1 agent turn
    speak_decision = PartyManagerDecision(next_speaker="Vorn")
    yield_decision = PartyManagerDecision(yield_to_dm=True)

    mock_manager_llm = MagicMock()
    mock_manager_llm.with_structured_output.return_value = mock_manager_llm
    # First call: route to player. Second call: player has set consecutive=1=max, yield.
    mock_manager_llm.invoke.side_effect = [speak_decision, yield_decision]

    mock_player_response = MagicMock(spec=AIMessage)
    mock_player_response.content = "Vorn acts."
    mock_player_response.tool_calls = []
    mock_player_response.additional_kwargs = {}
    mock_player_response.id = "msg-1"
    mock_player_response.type = "ai"
    mock_player_llm = MagicMock()
    mock_player_llm.bind_tools.return_value = mock_player_llm
    mock_player_llm.invoke.return_value = mock_player_response

    with (
        patch("dnd_bot.agents.party_manager.get_llm", return_value=mock_manager_llm),
        patch("dnd_bot.agents.player_node.get_llm", return_value=mock_player_llm),
    ):
        graph = build_party_graph(max_consecutive_turns=1)
        result = graph.invoke(state)

    assert result["next_speaker"] is None
