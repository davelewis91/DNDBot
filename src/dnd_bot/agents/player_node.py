import re

from langchain_core.messages import AIMessage, AnyMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool

from dnd_bot.agents.llm import get_llm
from dnd_bot.agents.prompts import (
    PLAYER_SYSTEM_PROMPT,
    SKILLS_GUIDANCE,
    build_character_context,
)
from dnd_bot.agents.state import GameState
from dnd_bot.agents.tools import COMBAT_TOOLS, EXPLORATION_TOOLS, ToolContext, build_tools

_IMPORTANCE_INSTRUCTION = (
    "\n\nAfter your action, include a line: [Importance: X] where X is a number 0-10 "
    "reflecting how personally important this action is to your character "
    "(10 = core to your backstory or motivation, 0 = purely tactical or optional)."
)


def _extract_text(content) -> str:
    """Extract plain text from message content (str or Anthropic block list)."""
    if isinstance(content, str):
        return content
    return "\n".join(b["text"] for b in content if b.get("type") == "text")


def _build_character_messages(
    messages: list[AnyMessage],
    character_name: str,
) -> list[AnyMessage]:
    """
    Rewrite message history so only this character's AIMessages keep the assistant role.

    Other characters' AIMessages become HumanMessages with a ``[Name]: ...`` prefix,
    preventing the LLM from interpreting another character's narration as its own.
    ToolMessages that follow a converted AIMessage are folded into the preceding
    HumanMessage (their tool_call_id would otherwise be orphaned).
    """
    result: list[AnyMessage] = []
    converted_tool_ids: set[str] = set()

    for msg in messages:
        if isinstance(msg, AIMessage):
            owner = msg.additional_kwargs.get("character_name")
            if owner is not None and owner != character_name:
                text = _extract_text(msg.content)
                for tc in msg.tool_calls:
                    converted_tool_ids.add(tc["id"])
                result.append(HumanMessage(content=f"[{owner}]: {text}"))
            else:
                result.append(msg)
        elif isinstance(msg, ToolMessage):
            if msg.tool_call_id in converted_tool_ids:
                if result and isinstance(result[-1], HumanMessage):
                    result[-1] = HumanMessage(
                        content=result[-1].content
                        + f"\n[Tool result: {msg.content}]"
                    )
            else:
                result.append(msg)
        else:
            result.append(msg)

    return result


def _filter_tools_for_mode(all_tools: list, mode: str) -> list:
    """
    Filter a tool list to those relevant for the given game mode.

    Parameters
    ----------
    all_tools : list
        Full list of LangChain tool objects (base tools + class ability tools).
    mode : str
        Game mode: "combat" keeps COMBAT_TOOLS plus class ability tools;
        any other mode keeps only EXPLORATION_TOOLS.

    Returns
    -------
    list
        Filtered list of LangChain tool objects.
    """
    if mode == "combat":
        allowed = COMBAT_TOOLS
        return [
            t for t in all_tools
            if t.name in allowed or t.name not in (EXPLORATION_TOOLS | COMBAT_TOOLS)
        ]
    allowed = EXPLORATION_TOOLS
    return [t for t in all_tools if t.name in allowed]


def make_player_node(model: str = "llama3:8b", provider: str = "ollama"):
    """
    Create a player node function bound to the given LLM configuration.

    Parameters
    ----------
    model : str
        LLM model name passed to get_llm()
    provider : str
        LLM provider ("ollama" or "anthropic")

    Returns
    -------
    Callable[[GameState], dict]
        A LangGraph-compatible node function.
    """

    base_llm = get_llm(model=model, temperature=0.7, provider=provider)

    def player_node(state: GameState) -> dict:
        """
        Execute one turn for the character named in state['next_speaker'].

        Looks up the character by name, builds mode-appropriate tools (including
        a change_mode closure), runs the LLM + tool loop, and returns a state
        update with new messages, any mode change, and an incremented
        consecutive_agent_turns counter.
        """
        character = next(
            (c for c in state["party"] if c.name == state["next_speaker"]), None
        )
        if character is None:
            return {
                "messages": [],
                "consecutive_agent_turns": state["consecutive_agent_turns"] + 1,
            }

        mode = state["mode"]
        mode_updates: list[str] = []

        @tool
        def change_mode(new_mode: str) -> str:
            """
            Switch the current game mode when a significant narrative event occurs.
            Call this when combat begins, an NPC addresses you directly, or combat ends.

            Parameters
            ----------
            new_mode : str
                New mode: "combat" or "exploration"
            """
            valid = ("combat", "exploration")
            if new_mode not in valid:
                return f"Invalid mode '{new_mode}'. Valid modes: {', '.join(valid)}"
            mode_updates.append(new_mode)
            if new_mode == "combat":
                total, die_roll = character.roll_initiative()
                bonus = total - die_roll
                return (
                    f"Mode changed to combat. "
                    f"Initiative roll: {total} (rolled {die_roll} + {bonus:+d})"
                )
            return f"Mode changed to {new_mode}"

        all_tools = build_tools(ToolContext(character=character)) + [change_mode]
        filtered = _filter_tools_for_mode(all_tools, mode)
        tool_map = {t.name: t for t in filtered}

        llm = base_llm.bind_tools(filtered)

        char_context = build_character_context(character, mode)
        system = PLAYER_SYSTEM_PROMPT.format(character_context=char_context)
        if mode != "combat":
            system += "\n\n" + SKILLS_GUIDANCE
        system += _IMPORTANCE_INSTRUCTION

        player_messages = _build_character_messages(
            state["messages"], character.name
        )
        response: AIMessage = llm.invoke(
            [SystemMessage(content=system)] + player_messages
        )

        # Extract importance score from response content (self-reported by player LLM)
        content = response.content
        narrative = (
            content if isinstance(content, str)
            else "\n".join(b["text"] for b in content if b.get("type") == "text")
        )
        importance_match = re.search(r"\[Importance:\s*(\d+(?:\.\d+)?)\]", narrative)
        importance = float(importance_match.group(1)) if importance_match else 5.0
        response.additional_kwargs["importance"] = importance
        response.additional_kwargs["character_name"] = character.name

        # Strip the importance tag from the content so it doesn't leak into
        # display or accumulate in message history
        if importance_match:
            cleaned = narrative[:importance_match.start()] + narrative[importance_match.end():]
            response.content = cleaned.strip()

        new_messages: list = [response]
        for tc in response.tool_calls:
            fn = tool_map.get(tc["name"])
            if fn:
                result = fn.invoke(tc["args"])
                new_messages.append(
                    ToolMessage(content=str(result), tool_call_id=tc["id"])
                )

        new_mode = mode_updates[-1] if mode_updates else mode
        return {
            "messages": new_messages,
            "mode": new_mode,
            "consecutive_agent_turns": state["consecutive_agent_turns"] + 1,
        }

    return player_node
