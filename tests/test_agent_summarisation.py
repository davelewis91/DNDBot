from unittest.mock import MagicMock, patch

from langchain_core.messages import AIMessage, HumanMessage

from dnd_bot.agents.player import PlayerAgent
from dnd_bot.character import Equipment, SpeciesName, get_species
from dnd_bot.character.skills import Skill


def make_mock_character():
    char = MagicMock()
    char.name = "Thorin"
    char.character_class = "Fighter"
    char.level = 3
    char.species = get_species(SpeciesName.DWARF)
    char.current_hp = 28
    char.max_hp = 32
    char.conditions = []
    char.equipment = Equipment()
    char.get_ability_modifier.return_value = 2
    char.get_skill_bonus.return_value = 4
    char.skills.get_proficient_skills.return_value = [Skill.ATHLETICS]
    char.background.to_prompt_context.return_value = "A warrior."
    return char


def make_ai_response(text: str) -> AIMessage:
    """Return a minimal AIMessage mock for process_turn."""
    response = MagicMock(spec=AIMessage)
    response.content = text
    response.tool_calls = []
    return response


def make_agent_with_mock_llm(mock_llm):
    """Build a PlayerAgent using a pre-configured mock LLM."""
    char = make_mock_character()
    mock_llm.bind_tools.return_value = mock_llm
    with patch("dnd_bot.agents.player.get_llm", return_value=mock_llm):
        return PlayerAgent(character=char, provider="ollama", model="llama3:8b")


def _run_n_turns(agent, n: int, mock_llm, summary_response: str = "Summary text.") -> None:
    """Run n process_turn calls. On the 15th turn mock_llm.invoke must return the
    summarisation response first, then the normal turn response."""
    for i in range(n):
        if (i + 1) % 15 == 0:
            # The 15th turn triggers summarisation before the normal LLM invoke.
            # Use side_effect: [summarisation result, normal turn result]
            mock_llm.invoke.side_effect = [
                MagicMock(content=summary_response, spec=AIMessage),
                make_ai_response(f"Turn {i + 1} response."),
            ]
        else:
            mock_llm.invoke.side_effect = None
            mock_llm.invoke.return_value = make_ai_response(f"Turn {i + 1} response.")
        agent.process_turn(f"DM input {i + 1}")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_no_summarisation_before_15_turns():
    """After 14 turns, _summary should still be None and _history should have 28 messages."""
    mock_llm = MagicMock()
    agent = make_agent_with_mock_llm(mock_llm)
    mock_llm.invoke.return_value = make_ai_response("response")

    for i in range(14):
        agent.process_turn(f"DM input {i + 1}")

    assert agent._summary is None
    # 14 turns × (1 HumanMessage + 1 AIMessage) = 28 messages
    assert len(agent._history) == 28


def test_summarisation_triggers_at_turn_15():
    """After exactly 15 turns, _summary should be set and _history should be shorter."""
    mock_llm = MagicMock()
    agent = make_agent_with_mock_llm(mock_llm)

    _run_n_turns(agent, 15, mock_llm, summary_response="Session summary here.")

    assert agent._summary == "Session summary here."
    # History should be shorter than 15*2=30 messages
    assert len(agent._history) < 30


def test_summarise_history_replaces_history_correctly():
    """_summarise_history should produce: 1 summary HumanMessage + last-3-turns messages."""
    mock_llm = MagicMock()
    agent = make_agent_with_mock_llm(mock_llm)

    # Manually populate _history with 6 turns (12 messages) — each a HumanMessage + AIMessage
    for i in range(6):
        agent._history.append(HumanMessage(content=f"DM {i + 1}"))
        agent._history.append(MagicMock(spec=AIMessage, content=f"AI {i + 1}", tool_calls=[]))

    mock_llm.invoke.return_value = MagicMock(content="Compact summary.", spec=AIMessage)
    agent._summarise_history()

    # Result: 1 summary message + last 3 turns (6 messages) = 7
    assert len(agent._history) == 7
    assert isinstance(agent._history[0], HumanMessage)
    assert "Compact summary." in agent._history[0].content
    # The last 3 turns start at turn 4 (DM 4 is at original index 6)
    assert agent._history[1].content == "DM 4"


def test_summarise_history_incorporates_previous_summary():
    """When _summary is already set, _summarise_history sends it as context to the LLM."""
    mock_llm = MagicMock()
    agent = make_agent_with_mock_llm(mock_llm)

    # Preload a previous summary
    agent._summary = "Previous session: fought goblins."

    # Populate _history with 6 turns
    for i in range(6):
        agent._history.append(HumanMessage(content=f"DM {i + 1}"))
        agent._history.append(MagicMock(spec=AIMessage, content=f"AI {i + 1}", tool_calls=[]))

    mock_llm.invoke.return_value = MagicMock(content="New summary.", spec=AIMessage)
    agent._summarise_history()

    # Verify the LLM was called and that the previous summary was part of the call
    call_args = mock_llm.invoke.call_args[0][0]  # list of messages passed
    combined = " ".join(
        m.content for m in call_args if isinstance(m, HumanMessage) and m.content
    )
    assert "Previous session: fought goblins." in combined

    # _summary should now be updated
    assert agent._summary == "New summary."


def test_summarise_history_skipped_when_too_few_turns():
    """_summarise_history does nothing when history has ≤3 HumanMessage boundaries."""
    mock_llm = MagicMock()
    agent = make_agent_with_mock_llm(mock_llm)

    # Only 3 turns in history
    for i in range(3):
        agent._history.append(HumanMessage(content=f"DM {i + 1}"))
        agent._history.append(MagicMock(spec=AIMessage, content=f"AI {i + 1}", tool_calls=[]))

    history_before = list(agent._history)
    agent._summarise_history()

    # History unchanged, LLM not called for summarisation
    assert agent._history == history_before
    mock_llm.invoke.assert_not_called()


def test_process_turn_works_normally_after_summarisation():
    """process_turn should return valid TurnResult even after summarisation has run."""
    mock_llm = MagicMock()
    agent = make_agent_with_mock_llm(mock_llm)

    _run_n_turns(agent, 15, mock_llm, summary_response="Summary text.")

    # Turn 16 — no summarisation expected, normal flow
    mock_llm.invoke.side_effect = None
    mock_llm.invoke.return_value = make_ai_response("Still going!")
    result = agent.process_turn("DM input 16")

    assert result.narrative == "Still going!"
    assert result.mode == "exploration"


def test_turn_count_increments_each_process_turn():
    """_turn_count should equal the number of process_turn calls."""
    mock_llm = MagicMock()
    agent = make_agent_with_mock_llm(mock_llm)
    mock_llm.invoke.return_value = make_ai_response("response")

    for i in range(5):
        agent.process_turn(f"DM input {i + 1}")

    assert agent._turn_count == 5
