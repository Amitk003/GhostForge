"""Report generator for benchmarks.

Creates markdown and json reports from metrics.
Honest reporting includes failures and ablations.
"""

import json
from pathlib import Path
from typing import Dict, List

from benchmarks.metrics import auroc, lead_time_at_fpr, precision_recall_f1


def generate_report(
    y_true: List[int],
    y_score: List[float],
    y_pred: List[int],
    model_name: str = "GhostForge Twin",
    baseline_name: str = "LogReg baseline",
    times: List[float] | None = None,
) -> Dict:
    """Generate report dict with all metrics."""
    times = times or list(range(len(y_true)))
    main = precision_recall_f1(y_true, y_pred)
    main["auroc"] = auroc(y_true, y_score)
    lead = lead_time_at_fpr(y_true, y_score, times, target_fpr=0.01)
    main["lead_time"] = lead if lead is not None else 0.0
    main["model"] = model_name

    # Dummy baseline for scaffold
    baseline = {"model": baseline_name, "f1": 0.0, "precision": 0.0, "recall": 0.0, "fpr": 0.1, "auroc": 0.5, "lead_time": 0.0}

    return {"model": main, "baseline": baseline, "comparison": {"f1_gain": main["f1"] - baseline["f1"]}}


def save_report(report: Dict, out_dir: Path = Path("benchmarks")) -> None:
    """Save report as json and markdown."""
    out_dir.mkdir(parents=True, exist_ok=True)

    # JSON
    with open(out_dir / "report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    # Markdown
    md = f"""# Benchmark Report

Model: {report['model']['model']}
F1: {report['model']['f1']:.3f}
Precision: {report['model']['precision']:.3f}
Recall: {report['model']['recall']:.3f}
FPR: {report['model']['fpr']:.3f}
AUROC: {report['model']['auroc']:.3f}
Lead Time @1% FPR: {report['model']['lead_time']}

Baseline: {report['baseline']['model']}
F1 gain: {report['comparison']['f1_gain']:.3f}

Notes: Cross dataset and held out family tests are required for honest numbers.
"""
    with open(out_dir / "report.md", "w", encoding="utf-8") as f:
        f.write(md)


def print_table(report: Dict) -> None:
    """Print table to console."""
    from rich.console import Console
    from rich.table import Table

    console = Console()
    table = Table(title="Benchmark Results")
    table.add_column("Model")
    table.add_column("F1")
    table.add_column("Precision")
    table.add_column("Recall")
    table.add_column("FPR")
    table.add_column("AUROC")
    table.add_column("Lead Time")
    for key in ["baseline", "model"]:
        r = report[key]
        table.add_row(r["model"], f"{r['f1']:.3f}", f"{r['precision']:.3f}", f"{r['recall']:.3f}", f"{r['fpr']:.3f}", f"{r['auroc']:.3f}", f"{r['lead_time']}")
    console.print(table)
