from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from dnd_bot.agents.llm import get_llm
from dnd_bot.agents.prompts import PLAYER_SYSTEM_PROMPT, build_character_context
from dnd_bot.agents.tools import ToolContext, build_tools


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
        self.tools = build_tools(ToolContext(character=character))
        self._tool_map = {t.name: t for t in self.tools}
        llm = get_llm(model=model, temperature=0.7, provider=provider)
        self._llm = llm.bind_tools(self.tools)
        self._history: list = []

    def process_turn(self, dm_input: str) -> str:
        """
        Process a DM message and return the agent's action.

        Parameters
        ----------
        dm_input : str
            The DM's scene description or prompt

        Returns
        -------
        str
            The agent's response including any tool results
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

        parts = []
        if response.content:
            parts.append(str(response.content))

        for tool_call in response.tool_calls:
            tool = self._tool_map.get(tool_call["name"])
            if tool:
                result = tool.invoke(tool_call["args"])
                parts.append(f"ACTION: {tool_call['name']}({tool_call['args']})\nResult: {result}")

        return "\n".join(parts) if parts else "(no response)"

    def set_mode(self, mode: str) -> None:
        """Update the game mode (exploration/combat/roleplay)."""
        self.mode = mode
