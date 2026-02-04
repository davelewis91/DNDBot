from typing import Literal

from langgraph.graph import MessagesState
from pydantic import Field

from ..character import AnyCharacter


class GameContext(MessagesState):
    """
    Current game state/situation provided by the DM.

    This is information external to the player characters, i.e.
    what they can observe about the world around them.
    """
    scene_description: str = ""
    npcs_present: list[str] = Field(default_factory=list)
    allies_present: list[str] = Field(default_factory=list)
    enemies_present: list[str] = Field(default_factory=list)

    is_combat: bool = False
    turn_order: list[str] = Field(default_factory=list)
    current_turn_number: int = 0

    recent_events: list[str] = Field(default_factory=list)


class PlayerState(MessagesState):
    """
    Current player state.

    The Character class contains all available mechanics, so we don't
    need to duplicate that here. This state is just for tracking.
    """
    character: AnyCharacter

    game_context: GameContext = Field(default_factory=GameContext)

    mode: Literal["exploration", "combat", "roleplay"] = "roleplay"

    chosen_action: str | None = None
    action_result: str | None = None
