from dataclasses import dataclass, field


@dataclass
class ActionResult:
    """A tool action taken by the player agent during a turn."""

    name: str
    result: str


@dataclass
class TurnResult:
    """
    The result of a single agent turn.

    Parameters
    ----------
    narrative : str
        The agent's in-character narrative response
    mode : str
        The game mode at the end of this turn
    actions : list[ActionResult]
        Tool actions taken during this turn
    """

    narrative: str
    mode: str
    actions: list[ActionResult] = field(default_factory=list)
