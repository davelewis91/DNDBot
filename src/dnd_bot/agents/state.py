from __future__ import annotations

from typing import Annotated, Literal

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

from dnd_bot.character.types import AnyCharacter


class GameState(TypedDict):
    """
    Shared state for the session graph and party subgraph.

    Parameters
    ----------
    messages : list[AnyMessage]
        Full conversation history. Uses add_messages reducer (append-only).
    mode : str
        Current game mode: "exploration" or "combat".
    party : list[AnyCharacter]
        List of Character instances in the party.
    initiative_order : list[str]
        Character names in initiative order (combat). DM-controlled via slash commands.
    initiative_rolls : dict[str, int]
        Maps character name to their initiative roll value. Used for ordered insertion.
    initiative_index : int
        Index into initiative_order for the current turn.
    next_speaker : str | None
        Set by party_manager to name the next acting character.
        None signals yield-to-DM.
    consecutive_agent_turns : int
        Number of agent turns since the last DM turn. Circuit breaker.
    pending_check : bool
        True when a player just used a dice-roll tool (skill_check, ability_check,
        attack, make_saving_throw). Forces the party manager to yield so the DM
        can narrate the outcome before other agents continue.
    combat_role : dict[str, str]
        Transient per-DM-turn mapping of character name to combat role.
        Reset at the start of each DM turn. Roles: "active" (full combat tools),
        "targeted" (saving throws only). Characters not in the dict are skipped.
    """

    messages: Annotated[list[AnyMessage], add_messages]
    mode: Literal["exploration", "combat"]
    party: list[AnyCharacter]
    initiative_order: list[str]
    initiative_rolls: dict[str, int]
    initiative_index: int
    next_speaker: str | None
    consecutive_agent_turns: int
    pending_check: bool
    combat_role: dict[str, str]
