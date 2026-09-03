"""Tests for bench metrics and report."""

from benchmarks.metrics import auroc, confusion, lead_time_at_fpr, precision_recall_f1
from benchmarks.report import generate_report


def test_confusion() -> None:
    tp, tn, fp, fn = confusion([1, 0, 1, 0], [1, 0, 0, 0])
    assert tp == 1
    assert tn == 2
    assert fp == 0
    assert fn == 1


def test_precision_recall() -> None:
    m = precision_recall_f1([1, 0, 1, 0], [1, 0, 1, 0])
    assert m["precision"] == 1.0
    assert m["recall"] == 1.0
    assert m["f1"] == 1.0
    assert m["fpr"] == 0.0


def test_auroc() -> None:
    y_true = [0, 0, 1, 1]
    y_score = [0.1, 0.2, 0.8, 0.9]
    a = auroc(y_true, y_score)
    assert 0.8 <= a <= 1.0


def test_report() -> None:
    y_true = [0, 0, 0, 1, 1]
    y_score = [0.1, 0.2, 0.15, 0.8, 0.9]
    y_pred = [1 if s > 0.5 else 0 for s in y_score]
    r = generate_report(y_true, y_score, y_pred)
    assert "model" in r
    assert "baseline" in r
    assert r["model"]["f1"] > 0
