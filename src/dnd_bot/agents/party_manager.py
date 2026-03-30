from langchain_core.messages import AIMessage, SystemMessage
from pydantic import BaseModel, Field

from dnd_bot.agents.llm import get_llm
from dnd_bot.agents.state import GameState

MAX_CONSECUTIVE_AGENT_TURNS = 5
_MANAGER_CONTEXT_MESSAGES = 3

_PARTY_MANAGER_PROMPT = """\
You are the party coordinator for a D&D group. Decide who acts next, or yield to the DM.

Party members:
{roster}

Current mode: {mode}
{initiative_section}\
Consecutive agent turns this round: {consecutive}/{max_turns}
Last player importance score: {importance}/10

Rules:
- If consecutive turns >= {max_turns}, you MUST yield to the DM (set yield_to_dm=true).
- In combat mode, only the character whose turn it is in the initiative order should act, \
unless a reaction is clearly warranted by context.
- A high importance score (>=7) suggests the player feels strongly about acting; favour \
letting them proceed even if the action is mechanically suboptimal.
- A low importance score (<=3) suggests the action is optional; yield to the DM sooner.
- Yield when the party has said their piece, no further player action adds value, or \
a narrative beat requires DM input.
"""


class PartyManagerDecision(BaseModel):
    """Routing decision from the party manager LLM."""

    next_speaker: str | None = Field(
        default=None,
        description="Name of the party member who should act next. "
                    "Must exactly match a name in the party roster.",
    )
    yield_to_dm: bool = Field(
        default=False,
        description="Set to true to return control to the DM.",
    )
    reasoning: str = Field(
        default="",
        description="One sentence explaining this routing decision.",
    )


def _build_roster(state: GameState) -> str:
    """Build a formatted party roster string for the party manager prompt."""
    lines = []
    for char in state["party"]:
        conditions = (
            ", ".join(str(c) for c in char.conditions) if char.conditions else "None"
        )
        lines.append(
            f"- {char.name} ({type(char).__name__}): "
            f"HP {char.current_hp}/{char.max_hp}, Conditions: {conditions}"
        )
    return "\n".join(lines)


def _get_last_importance(state: GameState) -> float:
    """Return the importance score from the most recent AIMessage, or 1.0 if absent."""
    for msg in reversed(state["messages"]):
        if isinstance(msg, AIMessage):
            return float(msg.additional_kwargs.get("importance", 1.0))
    return 1.0


def _build_initiative_section(state: GameState) -> str:
    """Build initiative order context string; empty string outside combat."""
    if state["mode"] != "combat" or not state["initiative_order"]:
        return ""
    order = state["initiative_order"]
    idx = state["initiative_index"] % len(order)
    current = order[idx]
    formatted = ", ".join(
        f"[{name}]" if i == idx else name for i, name in enumerate(order)
    )
    return f"Initiative order: {formatted}\nCurrent turn: {current}\n"


def make_party_manager_node(
    model: str = "llama3:8b",
    provider: str = "ollama",
    max_turns: int = MAX_CONSECUTIVE_AGENT_TURNS,
):
    """
    Create a party manager node bound to the given LLM configuration.

    Parameters
    ----------
    model : str
        LLM model name passed to get_llm()
    provider : str
        LLM provider ("ollama" or "anthropic")
    max_turns : int
        Maximum consecutive agent turns before forcing yield to DM

    Returns
    -------
    Callable[[GameState], dict]
        A LangGraph-compatible node function.
    """

    llm = get_llm(model=model, temperature=0.3, provider=provider)
    structured_llm = llm.with_structured_output(PartyManagerDecision)

    def party_manager_node(state: GameState) -> dict:
        """Route to the next player agent or yield to the DM."""
        roster = _build_roster(state)
        initiative_section = _build_initiative_section(state)
        last_importance = _get_last_importance(state)
        system = _PARTY_MANAGER_PROMPT.format(
            roster=roster,
            mode=state["mode"],
            initiative_section=initiative_section,
            consecutive=state["consecutive_agent_turns"],
            max_turns=max_turns,
            importance=last_importance,
        )

        recent = state["messages"][-_MANAGER_CONTEXT_MESSAGES:]
        decision: PartyManagerDecision = structured_llm.invoke(
            [SystemMessage(content=system)] + list(recent)
        )

        if decision.yield_to_dm or decision.next_speaker is None:
            return {"next_speaker": None, "consecutive_agent_turns": 0}
        return {"next_speaker": decision.next_speaker}

    return party_manager_node
