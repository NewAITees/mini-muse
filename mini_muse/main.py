"""Main entry point for mini_muse application."""

import sys
import asyncio
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel

from mini_muse.config import load_config, AppConfig
from mini_muse import __version__

app = typer.Typer(
    name="mini-muse",
    help="AI-powered image generation and feedback application",
    add_completion=False,
)
console = Console()


@app.command()
def run(
    config_file: Optional[Path] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to configuration file",
        exists=True,
        file_okay=True,
        dir_okay=False,
    ),
    debug: bool = typer.Option(
        False,
        "--debug",
        "-d",
        help="Enable debug mode",
    ),
) -> None:
    """Run the mini_muse TUI application."""
    try:
        # Load configuration
        config = load_config(config_file)
        
        if debug:
            config.log_level = "DEBUG"
            console.print("[yellow]Debug mode enabled[/yellow]")
        
        # Display startup information
        console.print(
            Panel(
                f"[bold blue]mini_muse v{__version__}[/bold blue]\n"
                f"AI-powered image generation and feedback application\n\n"
                f"Configuration: {config_file or 'default'}\n"
                f"Log level: {config.log_level}",
                title="Starting mini_muse",
                border_style="blue",
            )
        )
        
        # TODO: Initialize and run TUI application
        console.print("[yellow]TUI application initialization will be implemented in future tasks[/yellow]")
        console.print("[green]Configuration loaded successfully![/green]")
        
    except Exception as e:
        console.print(f"[red]Error starting application: {e}[/red]")
        sys.exit(1)


@app.command()
def config(
    show: bool = typer.Option(
        False,
        "--show",
        "-s",
        help="Show current configuration",
    ),
    reset: bool = typer.Option(
        False,
        "--reset",
        "-r",
        help="Reset configuration to defaults",
    ),
    config_file: Optional[Path] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to configuration file",
    ),
) -> None:
    """Manage application configuration."""
    try:
        if reset:
            from mini_muse.config import Config
            config_manager = Config(config_file)
            config_manager.reset_to_defaults()
            console.print("[green]Configuration reset to defaults[/green]")
            return
        
        if show:
            config = load_config(config_file)
            console.print(
                Panel(
                    config.json(indent=2),
                    title="Current Configuration",
                    border_style="green",
                )
            )
        else:
            console.print("Use --show to display configuration or --reset to reset to defaults")
            
    except Exception as e:
        console.print(f"[red]Error managing configuration: {e}[/red]")
        sys.exit(1)


@app.command()
def version() -> None:
    """Show version information."""
    console.print(f"mini_muse version {__version__}")


def main() -> None:
    """Main entry point."""
    app()


if __name__ == "__main__":
    main()