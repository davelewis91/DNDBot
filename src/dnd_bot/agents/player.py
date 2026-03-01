from dataclasses import dataclass, field

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool

from dnd_bot.agents.llm import get_llm
from dnd_bot.agents.prompts import PLAYER_SYSTEM_PROMPT, build_character_context
from dnd_bot.agents.tools import ToolContext, build_tools


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


class PlayerAgent:
    """
    Player agent for D&D, using an LLM with tool-calling to control a character.

    Parameters
    ----------
    character : AnyCharacter
        The D&D character this agent controls
    model : str
        LLM model name
    provider : str
        LLM provider ("ollama" or "anthropic")
    """

    def __init__(self, character, model: str = "llama3:8b", provider: str = "ollama"):
        self.character = character
        self.mode = "exploration"
        agent_self = self

        @tool
        def change_mode(mode: str) -> str:
            """
            Switch the current game mode when a significant narrative event occurs.
            Call this when combat begins, an NPC addresses you directly, or combat ends.

            Parameters
            ----------
            mode : str
                New mode: "combat", "exploration", or "roleplay"
            """
            valid = ("combat", "exploration", "roleplay")
            if mode not in valid:
                return f"Invalid mode '{mode}'. Valid modes: {', '.join(valid)}"
            agent_self.set_mode(mode)
            return f"Mode changed to {mode}"

        self.tools = build_tools(ToolContext(character=character)) + [change_mode]
        self._tool_map = {t.name: t for t in self.tools}
        llm = get_llm(model=model, temperature=0.7, provider=provider)
        self._llm = llm.bind_tools(self.tools)
        self._history: list = []

    def process_turn(self, dm_input: str) -> TurnResult:
        """
        Process a DM message and return the agent's action.

        Parameters
        ----------
        dm_input : str
            The DM's scene description or prompt

        Returns
        -------
        TurnResult
            The agent's structured response including narrative and tool actions
        """
        char_context = build_character_context(self.character, self.mode)
        system = PLAYER_SYSTEM_PROMPT.format(
            character_context=char_context,
            mode_guidance="",  # Already embedded in char_context
        )
        messages = [SystemMessage(content=system)] + self._history + [
            HumanMessage(content=dm_input)
        ]

        response: AIMessage = self._llm.invoke(messages)
        self._history.append(HumanMessage(content=dm_input))
        self._history.append(response)

        content = response.content
        if isinstance(content, list):
            narrative = "\n".join(block["text"] for block in content if block.get("type") == "text")
        elif isinstance(content, str):
            narrative = content
        else:
            narrative = ""
        actions = []
        for tool_call in response.tool_calls:
            tool = self._tool_map.get(tool_call["name"])
            if tool:
                result = tool.invoke(tool_call["args"])
                self._history.append(ToolMessage(content=str(result), tool_call_id=tool_call["id"]))
                actions.append(ActionResult(name=tool_call["name"], result=str(result)))

        return TurnResult(narrative=narrative, mode=self.mode, actions=actions)

    def set_mode(self, mode: str) -> None:
        """Update the game mode (exploration/combat/roleplay)."""
        self.mode = mode
