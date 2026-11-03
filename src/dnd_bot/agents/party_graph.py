from langgraph.constants import END
from langgraph.graph import StateGraph

from dnd_bot.agents.party_manager import make_party_manager_node
from dnd_bot.agents.player_node import make_player_node
from dnd_bot.agents.state import GameState


def _route_from_manager(state: GameState) -> str:
    """Route to player_node if a speaker is set, otherwise end the subgraph."""
    return "player_node" if state["next_speaker"] is not None else END


def build_party_graph(
    model: str = "llama3:8b",
    provider: str = "ollama",
    max_consecutive_turns: int = 5,
):
    """
    Build and compile the party subgraph.

    The subgraph loops party_manager → player_node → party_manager until
    party_manager sets next_speaker=None (yield to DM). The circuit breaker
    (max_consecutive_turns) is passed into the party manager's system prompt.

    Parameters
    ----------
    model : str
        LLM model name for all nodes
    provider : str
        LLM provider for all nodes
    max_consecutive_turns : int
        Maximum consecutive agent turns before the party manager is forced to yield

    Returns
    -------
    CompiledStateGraph
        Compiled party subgraph ready for use as a node in the session graph.
    """
    graph = StateGraph(GameState)
    graph.add_node(
        "party_manager",
        make_party_manager_node(
            model=model, provider=provider, max_turns=max_consecutive_turns
        ),
    )
    graph.add_node("player_node", make_player_node(model=model, provider=provider))
    graph.set_entry_point("party_manager")
    graph.add_conditional_edges("party_manager", _route_from_manager)
    graph.add_edge("player_node", "party_manager")
    return graph.compile()
