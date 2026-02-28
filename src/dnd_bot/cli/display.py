from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def print_character_card(character) -> None:
    """Print a formatted character summary panel."""
    table = Table(box=box.SIMPLE, show_header=False, pad_edge=False)
    table.add_column("Key", style="bold cyan")
    table.add_column("Value")
    table.add_row("Class", f"{character.species} {character.character_class}")
    table.add_row("Level", str(character.level))
    table.add_row("HP", f"{character.current_hp}/{character.max_hp}")
    console.print(Panel(table, title=f"[bold]{character.name}[/bold]", border_style="blue"))


def print_scene(description: str) -> None:
    """Print a scene description from the DM."""
    console.print(Panel(description, title="[bold yellow]DM[/bold yellow]", border_style="yellow"))


def print_agent_action(character_name: str, action: str) -> None:
    """Print the agent's chosen action."""
    console.print(
        Panel(action, title=f"[bold green]{character_name}[/bold green]", border_style="green")
    )


def print_dice_roll(roll_type: str, total: int, breakdown: str) -> None:
    """Print a formatted dice roll result."""
    console.print(f"  [dim]{roll_type}:[/dim] [bold]{total}[/bold] [dim]({breakdown})[/dim]")
