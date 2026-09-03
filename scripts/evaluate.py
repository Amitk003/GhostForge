"""Evaluation script for honest benchmarks.

Compares against logistic regression baseline and reports lead time at 1 percent FPR.
"""

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer()
console = Console()


@app.command()
def main(
    pred: Path = typer.Option(Path("benchmarks/output.json"), "--pred"),
    gt: Path = typer.Option(Path("data/processed/labels.csv"), "--gt"),
) -> None:
    """Evaluate predictions vs ground truth."""
    console.print(f"Evaluating {pred} vs {gt}")
    table = Table(title="Benchmark Results")
    table.add_column("Model")
    table.add_column("F1")
    table.add_column("Precision")
    table.add_column("Recall")
    table.add_column("FPR")
    table.add_column("Lead Time")
    table.add_row("LogReg baseline", "-", "-", "-", "-", "-")
    table.add_row("GhostForge Twin", "-", "-", "-", "-", "-")
    console.print(table)
    console.print("Scaffold: real metrics will be computed here")


if __name__ == "__main__":
    app()
