import json

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel

from dnd_bot.agents.llm import get_llm


class DMCommand(BaseModel):
    """A structured game command extracted from DM input."""

    type: str  # "damage", "heal", "mode", "condition", "rest"
    value: int | str | None = None


class DMIntent(BaseModel):
    """Structured interpretation of DM natural language input."""

    narrative: str
    commands: list[DMCommand]


_PARSER_SYSTEM = """\
You are a D&D game state parser. Given DM narration, extract:
1. The narrative text to show the player (preserve dramatic language)
2. Any mechanical game commands embedded in the text

Respond ONLY with valid JSON matching this schema:
{"narrative": "...", "commands": [{"type": "...", "value": ...}]}

Command types: "damage" (value=int), "heal" (value=int), \
"mode" (value="combat"|"exploration"|"roleplay"),
"condition" (value=str), "rest" (value="short"|"long"), "initiative" (value=null)

If no commands, use an empty list. Include ONLY commands you are certain about.
"""


def parse_dm_input(
    text: str,
    provider: str = "ollama",
    model: str = "llama3:8b",
) -> DMIntent:
    """
    Parse natural language DM input into structured intent.

    Parameters
    ----------
    text : str
        Raw DM input text
    provider : str
        LLM provider for parsing ("ollama" or "anthropic")
    model : str
        Model to use for parsing

    Returns
    -------
    DMIntent
        Structured narrative and commands
    """
    llm = get_llm(model=model, temperature=0.0, provider=provider)
    messages = [
        SystemMessage(content=_PARSER_SYSTEM),
        HumanMessage(content=text),
    ]
    response = llm.invoke(messages)
    try:
        data = json.loads(response.content)
        return DMIntent(
            narrative=data.get("narrative", text),
            commands=[DMCommand(**c) for c in data.get("commands", [])],
        )
    except (json.JSONDecodeError, KeyError, TypeError):
        return DMIntent(narrative=text, commands=[])
