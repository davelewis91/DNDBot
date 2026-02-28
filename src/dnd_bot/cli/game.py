import argparse

from dnd_bot.agents.player import PlayerAgent
from dnd_bot.character.storage import load_character
from dnd_bot.cli.display import console, print_agent_action, print_character_card, print_scene
from dnd_bot.cli.dm_parser import DMCommand, parse_dm_input


def apply_commands(
    commands: list[DMCommand],
    character,
    agent: PlayerAgent | None = None,
) -> None:
    """
    Apply parsed DM commands to game state.

    Parameters
    ----------
    commands : list[DMCommand]
        Commands extracted from DM input
    character : AnyCharacter
        The player character to modify
    agent : PlayerAgent, optional
        Agent to update mode on
    """
    for cmd in commands:
        if cmd.type == "damage" and isinstance(cmd.value, int):
            character.take_damage(cmd.value)
            hp = f"{character.current_hp}/{character.max_hp}"
            console.print(f"  [red]Took {cmd.value} damage. HP: {hp}[/red]")
        elif cmd.type == "heal" and isinstance(cmd.value, int):
            character.heal(cmd.value)
            hp = f"{character.current_hp}/{character.max_hp}"
            console.print(f"  [green]Healed {cmd.value}. HP: {hp}[/green]")
        elif cmd.type == "mode" and agent is not None:
            agent.set_mode(str(cmd.value))
            console.print(f"  [cyan]Mode: {cmd.value}[/cyan]")
        elif cmd.type == "condition":
            character.conditions.append(str(cmd.value))
            console.print(f"  [yellow]Condition applied: {cmd.value}[/yellow]")


class GameSession:
    """
    Manages a D&D game session between a human DM and the player agent.

    Parameters
    ----------
    agent : PlayerAgent
        The player agent
    provider : str
        LLM provider for DM parsing
    model : str
        LLM model for DM parsing
    """

    def __init__(self, agent: PlayerAgent, provider: str = "ollama", model: str = "llama3:8b"):
        self.agent = agent
        self.provider = provider
        self.model = model

    def _handle_slash_command(self, text: str) -> bool:
        """Handle slash commands. Returns True if command was handled."""
        parts = text.strip().split()
        cmd = parts[0].lower()
        char = self.agent.character

        if cmd == "/status":
            print_character_card(char)
            return True
        elif cmd == "/damage" and len(parts) > 1:
            apply_commands([DMCommand(type="damage", value=int(parts[1]))], char)
            return True
        elif cmd == "/heal" and len(parts) > 1:
            apply_commands([DMCommand(type="heal", value=int(parts[1]))], char)
            return True
        elif cmd == "/quit":
            console.print("[bold red]Session ended.[/bold red]")
            raise SystemExit(0)
        return False

    def run(self) -> None:
        """Run the interactive game session loop."""
        char = self.agent.character
        console.print(f"\n[bold blue]=== D&D Session: {char.name} ===[/bold blue]\n")
        print_character_card(char)
        console.print("\nType your scene descriptions. Use /status, /damage N, /heal N, /quit\n")

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
            apply_commands(intent.commands, char, agent=self.agent)

            response = self.agent.process_turn(intent.narrative)
            print_agent_action(char.name, response)


def main() -> None:
    """CLI entry point: dndbot play <character_yaml>"""
    parser = argparse.ArgumentParser(description="D&D Player Agent CLI")
    parser.add_argument("character", help="Path to character YAML file")
    parser.add_argument("--provider", default="ollama", choices=["ollama", "anthropic"])
    parser.add_argument("--model", default="llama3:8b")
    args = parser.parse_args()

    character = load_character(args.character)
    agent = PlayerAgent(character=character, model=args.model, provider=args.provider)
    session = GameSession(agent=agent, provider=args.provider, model=args.model)
    session.run()
