"""Dataset audit for CIC and CTU-13.

Checks leakage, redundant columns, label balance, and cross dataset issues.
Run: python scripts/audit_datasets.py --cic data/raw/cic.csv --ctu data/raw/ctu.csv
"""

from pathlib import Path
from typing import Dict

import polars as pl
import typer
from rich.console import Console
from rich.table import Table

from ghostforge.ingest.flow_parser import LEAKAGE_FIELDS, REDUNDANT_GROUPS

app = typer.Typer()
console = Console()


def audit_leakage(df: pl.DataFrame) -> Dict[str, bool]:
    """Check for leakage columns."""
    found = {}
    for col in df.columns:
        if col.lower() in LEAKAGE_FIELDS:
            found[col] = True
    return found


def audit_redundant(df: pl.DataFrame) -> list[list[str]]:
    """Find present redundant groups."""
    present = []
    for group in REDUNDANT_GROUPS:
        cols = [c for c in group if c in df.columns]
        if len(cols) > 1:
            present.append(cols)
    return present


def audit_labels(df: pl.DataFrame, label_col: str | None = None) -> Dict[str, int]:
    """Count label distribution."""
    if not label_col:
        for c in df.columns:
            if c.lower() in {"label", "class", "attack"}:
                label_col = c
                break
    if not label_col or label_col not in df.columns:
        return {}
    counts = df.group_by(label_col).len().sort("len", descending=True)
    return {str(row[0]): int(row[1]) for row in counts.iter_rows()}


@app.command()
def main(
    cic: Path = typer.Option(None, "--cic", help="Path to CIC CSV"),
    ctu: Path = typer.Option(None, "--ctu", help="Path to CTU biargus CSV"),
) -> None:
    """Run audits on provided datasets. If none given, show help."""
    if not cic and not ctu:
        console.print("[yellow]No dataset given. Use --cic or --ctu.[/yellow]")
        console.print("Example: python scripts/audit_datasets.py --cic data/raw/cic_sample.csv")
        raise typer.Exit()

    for name, path in [("CIC", cic), ("CTU-13", ctu)]:
        if not path:
            continue
        if not path.exists():
            console.print(f"[red]{name} not found: {path}[/red]")
            continue
        console.print(f"[green]Auditing {name}: {path}[/green]")
        try:
            df = pl.read_csv(path, infer_schema_length=1000, ignore_errors=True)
        except Exception as e:
            console.print(f"[red]Failed to read {path}: {e}[/red]")
            continue

        console.print(f"Rows: {len(df)}, Cols: {len(df.columns)}")

        # Leakage
        leak = audit_leakage(df)
        if leak:
            console.print(f"[red]Leakage columns found: {list(leak.keys())}[/red]")
        else:
            console.print("[green]No leakage columns found[/green]")

        # Redundant
        red = audit_redundant(df)
        if red:
            console.print(f"[yellow]Redundant groups: {red}[/yellow]")

        # Labels
        counts = audit_labels(df)
        if counts:
            table = Table(title=f"{name} label balance")
            table.add_column("Label")
            table.add_column("Count", justify="right")
            for k, v in list(counts.items())[:10]:
                table.add_row(str(k), str(v))
            console.print(table)
        console.print("")


if __name__ == "__main__":
    app()
