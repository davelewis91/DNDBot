import json

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel

from dnd_bot.agents.llm import get_llm


class DMCommand(BaseModel):
    """A structured game command extracted from DM input."""

    type: str  # "damage", "heal", "mode", "condition", "remove_condition", "rest", "target"
    value: int | str | None = None
    target: str | None = None


class DMIntent(BaseModel):
    """Structured interpretation of DM natural language input."""

    narrative: str
    commands: list[DMCommand]


_PARSER_SYSTEM = """\
You are a D&D game state parser. Given DM narration, extract:
1. The narrative text to show the player (preserve dramatic language)
2. Any mechanical game commands embedded in the text

Respond ONLY with valid JSON matching this schema:
{"narrative": "...", "commands": [{"type": "...", "value": ..., "target": "..."}]}

Command types: "damage" (value=int), "heal" (value=int), \
"mode" (value="combat"|"exploration"),
"condition" (value=str), "remove_condition" (value=str), \
"rest" (value="short"|"long"), "target" (value=null)

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

For damage, heal, condition, and remove_condition commands: extract the target \
character name(s) if mentioned. Set "target" to the character name exactly as \
spoken. If multiple characters are targeted, use a comma-separated string \
(e.g. "Vorn, Yue"). If no specific target is named, omit "target" or set it \
to null — this means it applies to the whole party.

Emit target when an enemy acts against a specific character during combat — \
an attack, spell, shove, grapple, or request for a saving throw. The "target" \
field must be the character name. Do NOT emit target for damage that is already \
covered by a damage command — only emit target when the enemy acts against \
a character WITHOUT a damage number. Examples:
- "The goblin swings at Vorn" → target with target="Vorn"
- "The wizard casts Hold Person on Yue, make a WIS save" → target with target="Yue"
- "The bandit attacks Vorn for 8 damage" → damage with value=8 and target="Vorn" \
(no separate target command needed, the damage command already names the target)

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
