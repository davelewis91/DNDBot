import argparse

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from dnd_bot.agents.llm import get_llm
from dnd_bot.agents.party_graph import build_party_graph
from dnd_bot.agents.party_manager import _drop_orphaned_tool_messages
from dnd_bot.agents.prompts import SUMMARISATION_PROMPT
from dnd_bot.agents.state import GameState
from dnd_bot.character.conditions import Condition
from dnd_bot.character.storage import load_character
from dnd_bot.character.types import AnyCharacter
from dnd_bot.cli.display import (
    console,
    print_agent_turn,
    print_character_card,
    print_mode_change,
    print_scene,
)
from dnd_bot.cli.dm_parser import DMCommand, parse_dm_input
from dnd_bot.dice import roll

SUMMARISE_AFTER_N_MESSAGES = 40
SUMMARISE_KEEP_RECENT = 6


def _summarise_messages(
    messages: list,
    model: str,
    provider: str,
) -> list:
    """
    Compact old messages into a summary when history exceeds the threshold.

    Keeps the most recent SUMMARISE_KEEP_RECENT messages verbatim. Summarises
    everything older using SUMMARISATION_PROMPT and inserts a SystemMessage
    summary in their place.

    Parameters
    ----------
    messages : list
        Full message list to compact
    model : str
        LLM model name for the summarisation call
    provider : str
        LLM provider for the summarisation call

    Returns
    -------
    list
        Compacted message list: [SystemMessage(summary)] + recent messages
    """
    if len(messages) <= SUMMARISE_KEEP_RECENT:
        return messages
    to_summarise = _drop_orphaned_tool_messages(messages[:-SUMMARISE_KEEP_RECENT])
    recent = _drop_orphaned_tool_messages(messages[-SUMMARISE_KEEP_RECENT:])
    llm = get_llm(model=model, temperature=0.0, provider=provider)
    response = llm.invoke(
        [SystemMessage(content=SUMMARISATION_PROMPT)] + list(to_summarise)
    )
    content = response.content
    summary_text = (
        content if isinstance(content, str)
        else "\n".join(b["text"] for b in content if b.get("type") == "text")
    )
    return [SystemMessage(content=f"Session so far: {summary_text}")] + recent


class GameSession:
    """
    Manages a multi-agent D&D game session between a human DM and a party of
    AI player agents, driven by a LangGraph session graph.

    Parameters
    ----------
    party : list[AnyCharacter]
        List of Character instances in the party
    provider : str
        LLM provider for all agents and DM parsing
    model : str
        LLM model name for all agents and DM parsing
    max_consecutive_turns : int
        Maximum agent turns before forced yield to DM
    """

    def __init__(
        self,
        party: list[AnyCharacter],
        provider: str = "ollama",
        model: str = "llama3:8b",
        max_consecutive_turns: int = 5,
    ):
        self.party = party
        self.provider = provider
        self.model = model
        self.graph = build_party_graph(
            model=model,
            provider=provider,
            max_consecutive_turns=max_consecutive_turns,
        )
        self.state: GameState = {
            "messages": [],
            "mode": "exploration",
            "party": party,
            "initiative_order": [],
            "initiative_rolls": {},
            "initiative_index": 0,
            "next_speaker": None,
            "consecutive_agent_turns": 0,
            "pending_check": False,
            "combat_role": {},
        }

    def _get_character(self, name: str):
        """Return the character matching name (case-insensitive).

        Tries exact match first, then prefix match (e.g. "vorn" matches
        "Vorn Ashgrip" if unambiguous). Returns None if no match or if
        multiple characters match a partial name.
        """
        name_lower = name.lower()
        exact = next(
            (c for c in self.party if c.name.lower() == name_lower), None
        )
        if exact is not None:
            return exact
        matches = [c for c in self.party if c.name.lower().startswith(name_lower)]
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            names = ", ".join(c.name for c in matches)
            console.print(f"  [yellow]Ambiguous name '{name}': matches {names}[/yellow]")
        return None

    @staticmethod
    def _parse_name_and_value(parts: list[str]) -> tuple[str, str] | None:
        """Split slash-command parts into (name, value).

        The value is always the last token. Everything between the command
        (parts[0]) and the last token is joined as the character name.
        Returns None if there aren't enough parts.
        """
        rest = parts[1:]
        if len(rest) < 2:
            return None
        return " ".join(rest[:-1]), rest[-1]

    def _resolve_targets(self, cmd: DMCommand) -> list:
        """Resolve command targets to character instances.

        Returns all party members if no target specified, otherwise resolves
        comma-separated names to matching characters.
        """
        if cmd.target is None:
            return list(self.party)
        names = [n.strip() for n in cmd.target.split(",")]
        targets = []
        for name in names:
            char = self._get_character(name)
            if char:
                targets.append(char)
            else:
                console.print(f"  [yellow]Unknown character: {name}[/yellow]")
        return targets

    def _roll_party_initiative(self) -> None:
        """Roll initiative for all party members and populate state."""
        rolls: dict[str, int] = {}
        for char in self.party:
            total, die_roll = char.roll_initiative()
            rolls[char.name] = total
            bonus = total - die_roll
            console.print(
                f"  [cyan]{char.name} initiative: {total}"
                f" (rolled {die_roll} + {bonus:+d})[/cyan]"
            )
        order = sorted(rolls, key=rolls.get, reverse=True)
        self.state["initiative_order"] = order
        self.state["initiative_rolls"] = rolls
        self.state["initiative_index"] = 0

    def _clear_initiative(self) -> None:
        """Reset initiative state when leaving combat."""
        self.state["initiative_order"] = []
        self.state["initiative_rolls"] = {}
        self.state["initiative_index"] = 0

    def _handle_mode_change(self, new_mode: str) -> None:
        """Apply a mode transition and its side effects."""
        self.state["mode"] = new_mode
        print_mode_change(new_mode)
        if new_mode == "combat":
            self._roll_party_initiative()
        else:
            self._clear_initiative()
            self.state["combat_role"] = {}

    def _build_combat_roles(self, commands: list[DMCommand]) -> None:
        """
        Build combat_role dict for this DM turn from initiative and parser commands.

        Sets the initiative-current character as "active", then applies any "target"
        commands from the parser. If a targeted character is already active, skip
        (active is a superset of targeted).
        """
        roles: dict[str, str] = {}
        order = self.state["initiative_order"]
        if order:
            idx = self.state["initiative_index"] % len(order)
            roles[order[idx]] = "active"
        for cmd in commands:
            if cmd.type == "target" and cmd.target:
                for name in (n.strip() for n in cmd.target.split(",")):
                    char = self._get_character(name)
                    if char and char.name not in roles:
                        roles[char.name] = "targeted"
        self.state["combat_role"] = roles

    def _advance_initiative(self) -> None:
        """Advance initiative_index to the next character in the order."""
        order = self.state["initiative_order"]
        if order:
            self.state["initiative_index"] = (
                self.state["initiative_index"] + 1
            ) % len(order)

    def _apply_commands(self, commands: list[DMCommand]) -> None:
        """Apply parsed DM commands to party state."""
        for cmd in commands:
            targets = self._resolve_targets(cmd)
            if cmd.type == "damage" and isinstance(cmd.value, int):
                for char in targets:
                    char.take_damage(cmd.value)
                    console.print(
                        f"  [red]{char.name} took {cmd.value} damage. "
                        f"HP: {char.current_hp}/{char.max_hp}[/red]"
                    )
            elif cmd.type == "heal" and isinstance(cmd.value, int):
                for char in targets:
                    char.heal(cmd.value)
                    console.print(
                        f"  [green]{char.name} healed {cmd.value}. "
                        f"HP: {char.current_hp}/{char.max_hp}[/green]"
                    )
            elif cmd.type == "mode" and self.state["mode"] != str(cmd.value):
                self._handle_mode_change(str(cmd.value))
            elif cmd.type == "condition":
                try:
                    condition = Condition(str(cmd.value).lower())
                    for char in targets:
                        char.add_condition(condition)
                        console.print(
                            f"  [yellow]{char.name}: condition {condition.value}"
                            f" applied[/yellow]"
                        )
                except ValueError:
                    console.print(f"  [yellow]Unknown condition: {cmd.value}[/yellow]")
            elif cmd.type == "remove_condition":
                try:
                    condition = Condition(str(cmd.value).lower())
                    for char in targets:
                        char.remove_condition(condition)
                        console.print(
                            f"  [yellow]{char.name}: condition {condition.value}"
                            f" removed[/yellow]"
                        )
                except ValueError:
                    console.print(f"  [yellow]Unknown condition: {cmd.value}[/yellow]")

    def _display_new_messages(self, messages_before: int, mode: str) -> None:
        """Display agent messages added since messages_before index."""
        new_msgs = self.state["messages"][messages_before:]
        i = 0
        while i < len(new_msgs):
            msg = new_msgs[i]
            if isinstance(msg, AIMessage) and msg.content:
                # Collect following ToolMessages for this AIMessage
                tool_results = []
                j = i + 1
                while j < len(new_msgs) and isinstance(new_msgs[j], ToolMessage):
                    tool_results.append(new_msgs[j].content)
                    j += 1
                # Find character name from tool calls or content context
                char_name = self._infer_speaker(msg) or "Agent"
                content = msg.content
                narrative = (
                    content if isinstance(content, str)
                    else "\n".join(
                        b["text"] for b in content if b.get("type") == "text"
                    )
                )
                print_agent_turn(char_name, narrative, tool_results, mode)
                i = j
            else:
                i += 1

    def _infer_speaker(self, msg) -> str | None:
        """Attempt to infer which character spoke from message metadata."""
        # The player_node doesn't tag messages with character_name.
        # Best effort: check additional_kwargs or return None.
        return msg.additional_kwargs.get("character_name")

    def _handle_slash_command(self, text: str) -> bool:
        """Handle slash commands. Returns True if command was handled."""
        parts = text.strip().split()
        cmd = parts[0].lower()

        if cmd == "/status":
            for char in self.party:
                print_character_card(char)
            return True
        elif cmd == "/damage" and len(parts) > 2:
            parsed = self._parse_name_and_value(parts)
            if parsed is None:
                return True
            name, amount_str = parsed
            try:
                amount = int(amount_str)
            except ValueError:
                console.print(f"  [yellow]Amount must be a number, got: {amount_str}[/yellow]")
                return True
            char = self._get_character(name)
            if char:
                char.take_damage(amount)
                console.print(
                    f"  [red]{char.name} took {amount} damage. "
                    f"HP: {char.current_hp}/{char.max_hp}[/red]"
                )
            else:
                console.print(f"  [yellow]Unknown character: {name}[/yellow]")
            return True
        elif cmd == "/heal" and len(parts) > 2:
            parsed = self._parse_name_and_value(parts)
            if parsed is None:
                return True
            name, amount_str = parsed
            try:
                amount = int(amount_str)
            except ValueError:
                console.print(f"  [yellow]Amount must be a number, got: {amount_str}[/yellow]")
                return True
            char = self._get_character(name)
            if char:
                char.heal(amount)
                console.print(
                    f"  [green]{char.name} healed {amount}. "
                    f"HP: {char.current_hp}/{char.max_hp}[/green]"
                )
            else:
                console.print(f"  [yellow]Unknown character: {name}[/yellow]")
            return True
        elif cmd == "/condition" and len(parts) > 2:
            parsed = self._parse_name_and_value(parts)
            if parsed is None:
                return True
            name, cond_str = parsed
            char = self._get_character(name)
            if char:
                try:
                    condition = Condition(cond_str.lower())
                    char.add_condition(condition)
                    console.print(
                        f"  [yellow]{char.name}: condition {condition.value} applied[/yellow]"
                    )
                except ValueError:
                    console.print(f"  [yellow]Unknown condition: {cond_str}[/yellow]")
            else:
                console.print(f"  [yellow]Unknown character: {name}[/yellow]")
            return True
        elif cmd == "/uncondition" and len(parts) > 2:
            parsed = self._parse_name_and_value(parts)
            if parsed is None:
                return True
            name, cond_str = parsed
            char = self._get_character(name)
            if char:
                try:
                    condition = Condition(cond_str.lower())
                    char.remove_condition(condition)
                    console.print(
                        f"  [yellow]{char.name}: condition {condition.value} removed[/yellow]"
                    )
                except ValueError:
                    console.print(f"  [yellow]Unknown condition: {cond_str}[/yellow]")
            else:
                console.print(f"  [yellow]Unknown character: {name}[/yellow]")
            return True
        elif cmd == "/rest" and len(parts) > 1:
            rest_type = parts[1].lower()
            for char in self.party:
                if rest_type == "short":
                    result = char.short_rest()
                    if result.success:
                        console.print(
                            f"  [cyan]{char.name} short rest. "
                            f"HP: {char.current_hp}/{char.max_hp}[/cyan]"
                        )
                    else:
                        console.print(
                            f"  [yellow]{char.name} short rest failed: {result.error}[/yellow]"
                        )
                elif rest_type == "long":
                    char.long_rest()
                    console.print(
                        f"  [cyan]{char.name} long rest. "
                        f"HP: {char.current_hp}/{char.max_hp}[/cyan]"
                    )
                else:
                    console.print(
                        f"  [yellow]Unknown rest type '{rest_type}'. Use: short, long[/yellow]"
                    )
                    break
            return True
        elif cmd == "/mode" and len(parts) > 1:
            new_mode = parts[1].lower()
            if self.state["mode"] != new_mode:
                self._handle_mode_change(new_mode)
            return True
        elif cmd == "/roll" and len(parts) > 1:
            notation = parts[1]
            try:
                result = roll(notation)
                console.print(
                    f"  [magenta]Roll {notation}: [bold]{result.total}[/bold][/magenta]"
                )
            except Exception:
                console.print(f"  [yellow]Invalid dice notation '{notation}'[/yellow]")
            return True
        elif cmd == "/initiative":
            return self._handle_initiative_command(parts[1:])
        elif cmd == "/quit":
            console.print("[bold red]Session ended.[/bold red]")
            raise SystemExit(0)
        return False

    def _handle_initiative_command(self, args: list[str]) -> bool:
        """Handle /initiative subcommands: add, remove, next, show."""
        if not args:
            console.print(
                "  [yellow]Usage: /initiative add <name> <roll> | remove <name> "
                "| next | show[/yellow]"
            )
            return True
        sub = args[0].lower()
        order = self.state["initiative_order"]

        if sub == "add" and len(args) >= 3:
            name = args[1]
            try:
                roll_value = int(args[2])
            except ValueError:
                console.print(f"  [yellow]Roll must be a number, got: {args[2]}[/yellow]")
                return True
            # Insert in descending order by roll value
            # Store as (roll, name) for sorting, then rebuild order list
            self.state["initiative_rolls"][name] = roll_value
            pairs = [(self._get_initiative_roll(n), n) for n in order]
            pairs.append((roll_value, name))
            pairs.sort(key=lambda x: x[0], reverse=True)
            self.state["initiative_order"] = [n for _, n in pairs]
            console.print(
                f"  [cyan]{name} added to initiative at roll {roll_value}.[/cyan]"
            )
        elif sub == "remove" and len(args) >= 2:
            name = args[1]
            if name in order:
                idx = order.index(name)
                order.remove(name)
                # Adjust index if needed
                if self.state["initiative_index"] >= len(order) and order:
                    self.state["initiative_index"] = 0
                elif idx < self.state["initiative_index"]:
                    self.state["initiative_index"] = max(
                        0, self.state["initiative_index"] - 1
                    )
                console.print(f"  [cyan]{name} removed from initiative.[/cyan]")
            else:
                console.print(f"  [yellow]{name} not in initiative order.[/yellow]")
        elif sub == "next":
            if order:
                self.state["initiative_index"] = (
                    self.state["initiative_index"] + 1
                ) % len(order)
                current = order[self.state["initiative_index"]]
                console.print(f"  [cyan]Initiative: {current}'s turn.[/cyan]")
            else:
                console.print("  [yellow]Initiative order is empty.[/yellow]")
        elif sub == "show":
            if not order:
                console.print("  [cyan]No initiative order set.[/cyan]")
            else:
                idx = self.state["initiative_index"]
                lines = [
                    f"  {'→ ' if i == idx else '  '}{name}"
                    for i, name in enumerate(order)
                ]
                console.print("[cyan]Initiative Order:[/cyan]")
                for line in lines:
                    console.print(line)
        else:
            console.print(
                "  [yellow]Usage: /initiative add <name> <roll> | remove <name> "
                "| next | show[/yellow]"
            )
        return True

    def _get_initiative_roll(self, name: str) -> int:
        """Return the stored initiative roll for name, or 0 if unknown."""
        return self.state["initiative_rolls"].get(name, 0)

    def run(self) -> None:
        """Run the interactive game session loop."""
        names = ", ".join(c.name for c in self.party)
        console.print(f"\n[bold blue]=== D&D Session: {names} ===[/bold blue]\n")
        for char in self.party:
            print_character_card(char)
        console.print(
            "\nType your scene descriptions. "
            "Commands: /status, /damage <name> <n>, /heal <name> <n>, "
            "/condition <name> <cond>, /uncondition <name> <cond>, "
            "/rest short|long, /mode combat|exploration, /roll <dice>, "
            "/initiative add|remove|next|show, /quit\n"
        )

        while True:
            try:
                raw = console.input("[bold yellow]DM>[/bold yellow] ").strip()
            except (EOFError, KeyboardInterrupt):
                break

            if not raw:
                continue

            if raw.startswith("/"):
                try:
                    self._handle_slash_command(raw)
                except SystemExit:
                    break
                continue

            intent = parse_dm_input(raw, provider=self.provider, model=self.model)
            print_scene(intent.narrative)
            self._apply_commands(intent.commands)

            # Build combat roles for this turn (deterministic routing in combat)
            if self.state["mode"] == "combat":
                self._build_combat_roles(intent.commands)

            # Prepare state for this turn
            count_before = len(self.state["messages"])
            self.state["messages"] = (
                list(self.state["messages"])
                + [HumanMessage(content=intent.narrative)]
            )
            mode_before = self.state["mode"]

            result = self.graph.invoke(self.state)
            self.state = result

            if self.state["mode"] != mode_before:
                self._handle_mode_change(self.state["mode"])

            # Auto-advance initiative after the combat round completes
            if self.state["mode"] == "combat":
                self._advance_initiative()

            self._display_new_messages(count_before + 1, self.state["mode"])

            # Summarise if history is long
            if len(self.state["messages"]) >= SUMMARISE_AFTER_N_MESSAGES:
                self.state["messages"] = _summarise_messages(
                    self.state["messages"], model=self.model, provider=self.provider
                )


def main() -> None:
    """CLI entry point: dndbot <character_yaml> [character_yaml ...]"""
    parser = argparse.ArgumentParser(description="D&D Multi-Agent Session")
    parser.add_argument(
        "characters",
        nargs="+",
        help="Paths to character YAML files (one per player)",
    )
    parser.add_argument("--provider", default="ollama", choices=["ollama", "anthropic"])
    parser.add_argument("--model", default="llama3:8b")
    args = parser.parse_args()

    party = [load_character(path) for path in args.characters]
    session = GameSession(party=party, model=args.model, provider=args.provider)
    session.run()
