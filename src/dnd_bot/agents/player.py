from dataclasses import dataclass, field

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool

from dnd_bot.agents.llm import get_llm
from dnd_bot.agents.prompts import (
    PLAYER_SYSTEM_PROMPT,
    SUMMARISATION_PROMPT,
    build_character_context,
)
from dnd_bot.agents.tools import COMBAT_TOOLS, EXPLORATION_TOOLS, ToolContext, build_tools


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

        self._all_tools = build_tools(ToolContext(character=character)) + [change_mode]
        self._base_llm = get_llm(model=model, temperature=0.7, provider=provider)
        self._history: list = []
        self._turn_count: int = 0
        self._summary: str | None = None
        self._bind_tools_for_mode("exploration")

    def _bind_tools_for_mode(self, mode: str) -> None:
        """
        Filter all tools to those relevant for the given mode and rebind the LLM.

        Parameters
        ----------
        mode : str
            The game mode to bind tools for. "combat" uses COMBAT_TOOLS plus all class
            ability tools; "exploration" uses EXPLORATION_TOOLS. Any other mode falls
            back to exploration. Note: ``change_mode`` is present in both EXPLORATION_TOOLS
            and COMBAT_TOOLS so the agent remains usable after any mode switch.
        """
        if mode == "combat":
            allowed = COMBAT_TOOLS
            # Class ability tools (not in EXPLORATION_TOOLS or COMBAT_TOOLS base sets)
            # are always included in combat.
            self.tools = [
                t for t in self._all_tools
                if t.name in allowed or t.name not in (EXPLORATION_TOOLS | COMBAT_TOOLS)
            ]
        else:
            allowed = EXPLORATION_TOOLS
            self.tools = [t for t in self._all_tools if t.name in allowed]
        self._tool_map = {t.name: t for t in self.tools}
        self._llm = self._base_llm.bind_tools(self.tools)

    def _summarise_history(self) -> None:
        """
        Summarise all but the last 3 turns of history and compact _history.

        Identifies the last 3 turns by scanning back for 3 HumanMessage boundaries.
        Calls the base LLM with the SUMMARISATION_PROMPT and the older history messages
        to produce a ≤150-word narrative log. Stores the result in ``self._summary`` and
        replaces ``_history`` with a single summary HumanMessage followed by the last 3
        turns' messages.
        """
        # Find index of the 3rd-to-last HumanMessage (i.e. start of "last 3 turns")
        human_indices = [i for i, m in enumerate(self._history) if isinstance(m, HumanMessage)]
        if len(human_indices) <= 3:
            return
        split_index = human_indices[-3]
        older = self._history[:split_index]
        last_three = self._history[split_index:]

        # When _summary exists, older[0] is the injected "Session so far:" message from the
        # last summarisation. Skip it to avoid sending the same content twice.
        older_messages = older[1:] if self._summary and older else older

        # Build context: previous summary (if any) + older messages
        summarise_messages = [SystemMessage(content=SUMMARISATION_PROMPT)]
        if self._summary:
            summarise_messages.append(HumanMessage(content=f"Previous summary:\n{self._summary}"))
        summarise_messages.extend(older_messages)

        response = self._base_llm.invoke(summarise_messages)
        content = response.content
        if isinstance(content, list):
            summary_text = "\n".join(
                block["text"] for block in content if block.get("type") == "text"
            )
        elif isinstance(content, str):
            summary_text = content
        else:
            summary_text = ""

        self._summary = summary_text
        self._history = [HumanMessage(content=f"Session so far: {summary_text}")] + last_three

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
        self._turn_count += 1
        if self._turn_count % 15 == 0:
            self._summarise_history()

        char_context = build_character_context(self.character, self.mode)
        system = PLAYER_SYSTEM_PROMPT.format(
            character_context=char_context
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
        """Update the game mode and rebind the LLM with the appropriate tool set."""
        self.mode = mode
        self._bind_tools_for_mode(mode)
