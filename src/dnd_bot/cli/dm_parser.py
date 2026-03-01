import json

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel

from dnd_bot.agents.llm import get_llm


class DMCommand(BaseModel):
    """A structured game command extracted from DM input."""

    type: str  # "damage", "heal", "mode", "condition", "remove_condition", "rest"
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
"mode" (value="combat"|"exploration"),
"condition" (value=str), "remove_condition" (value=str), \
"rest" (value="short"|"long")

Use "remove_condition" when the DM indicates a condition is ending \
(e.g. "you are no longer poisoned", "the stun wears off").

Emit damage=N when the player takes damage: "you take N damage", "takes N damage", \
"deals N damage", "hit for N", "suffers N damage", "N piercing/slashing/bludgeoning \
/fire/cold/poison damage". Extract the integer N as the value.

Emit heal=N when the player regains hit points: "heal N", "regain N hit points", \
"restore N hit points", "recover N hit points", "gain N HP", "heals you for N". \
Extract the integer N as the value.

Emit mode="combat" when combat begins: "roll initiative", "initiative", \
"roll for initiative", "combat begins", "battle begins", "they attack", \
"attacks you", "prepare for battle".

Emit mode="exploration" when combat or conversation ends: "combat is over", \
"enemy is dead", "enemy flees", "the fight is over", "the creature falls", \
"you defeat", "they retreat", "the conversation ends", "the NPC leaves", \
"they walk away", "the area is clear".

If no commands, use an empty list. Include ONLY commands you are certain about.
"""


def _extract_json(text: str) -> str:
    """Strip markdown code fences from LLM JSON responses."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines)
    return text


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
        data = json.loads(_extract_json(response.content))
        return DMIntent(
            narrative=data.get("narrative", text),
            commands=[DMCommand(**c) for c in data.get("commands", [])],
        )
    except (json.JSONDecodeError, KeyError, TypeError):
        return DMIntent(narrative=text, commands=[])
