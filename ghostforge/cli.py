"""Command line interface for GhostForge."""

from pathlib import Path

import typer
from rich.console import Console

from ghostforge.__version__ import __version__
from ghostforge.config import load_config

app = typer.Typer(help="GhostForge - network attack forecasting")
console = Console()


@app.command()
def version() -> None:
    """Show version."""
    console.print(f"GhostForge v{__version__}")


@app.command()
def ingest(
    input_path: Path = typer.Option(..., "--input", "-i", help="Input PCAP or CSV"),
    out: Path = typer.Option(Path("data/processed"), "--out", "-o", help="Output dir"),
) -> None:
    """Ingest traffic file into windowed snapshots."""
    cfg = load_config()
    console.print(f"Ingesting {input_path} -> {out} with window {cfg.ingest.window_seconds}s")
    console.print("Use ghostforge.ingest.flow_parser and pcap_parser modules")


@app.command()
def train(
    config: Path = typer.Option(Path("configs/base.yaml"), "--config", "-c", help="Config yaml"),
) -> None:
    """Train the world model twin on benign traffic."""
    cfg = load_config(config)
    console.print(f"Training with latent {cfg.twin.latent_dim} for {cfg.twin.epochs} epochs")


@app.command()
def infer(
    input_path: Path = typer.Option(..., "--input", "-i", help="Input snapshot parquet"),
    out: Path = typer.Option(Path("benchmarks/output.json"), "--out", "-o", help="Output json"),
) -> None:
    """Run forecasting inference on a snapshot."""
    console.print(f"Infer {input_path} -> {out}")


@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", help="Host"),
    port: int = typer.Option(8000, help="Port"),
) -> None:
    """Start the API service."""
    import uvicorn

    uvicorn.run("ghostforge.serve.api:app", host=host, port=port, reload=True)


if __name__ == "__main__":
    app()
