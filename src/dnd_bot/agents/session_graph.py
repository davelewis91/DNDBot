from dnd_bot.agents.party_graph import build_party_graph


def build_session_graph(
    model: str = "llama3:8b",
    provider: str = "ollama",
    max_consecutive_turns: int = 5,
):
    """
    Build and compile the session graph.

    Currently a thin wrapper around build_party_graph. Exists as the intended
    location for future session-level concerns (e.g., multi-party events,
    session-level hooks).

    Parameters
    ----------
    model : str
        LLM model name for all nodes
    provider : str
        LLM provider for all nodes
    max_consecutive_turns : int
        Maximum consecutive agent turns before forced yield to DM

    Returns
    -------
    CompiledStateGraph
        Compiled session graph for use by GameSession.
    """
    return build_party_graph(
        model=model,
        provider=provider,
        max_consecutive_turns=max_consecutive_turns,
    )
