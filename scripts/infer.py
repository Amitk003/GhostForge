"""Inference script for single file or snapshot."""

from pathlib import Path

import typer
from rich.console import Console

from ghostforge.config import load_config

app = typer.Typer()
console = Console()


@app.command()
def main(
    input_path: Path = typer.Option(..., "--input", "-i"),
    out: Path = typer.Option(Path("benchmarks/output.json"), "--out", "-o"),
    config: Path = typer.Option(Path("configs/inference.yaml"), "--config", "-c"),
) -> None:
    """Run inference on a snapshot or pcap."""
    cfg = load_config(config)
    console.print(f"Infer {input_path} with window {cfg.ingest.window_seconds}s")
    console.print(f"Output to {out}")
    console.print("Scaffold: real inference will load model and produce risk timeline here")


if __name__ == "__main__":
    app()
