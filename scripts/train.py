"""Training entry point for GhostForge twin."""

from pathlib import Path

import typer
from rich.console import Console

from ghostforge.config import load_config

app = typer.Typer()
console = Console()


@app.command()
def main(
    config: Path = typer.Option(Path("configs/base.yaml"), "--config", "-c"),
    data: Path = typer.Option(Path("data/processed"), "--data", "-d"),
) -> None:
    """Train world model on benign traffic."""
    cfg = load_config(config)
    console.print(f"[green]Training GhostForge[/green] with config {config}")
    console.print(f"Data: {data}, latent {cfg.twin.latent_dim}, epochs {cfg.twin.epochs}")
    console.print("Scaffold: real training will load snapshots and train TGN+JEPA here")
    console.print("Done. Save to models/")


if __name__ == "__main__":
    app()
