"""Tests for validator hunt and conformal."""

import tempfile
from pathlib import Path

from ghostforge.twin.feedback import Feedback, load_feedback, needs_retrain, save_feedback
from ghostforge.validator.conformal import calibrate, interval
from ghostforge.validator.counterfactual import hunt_plan, rank_hunts
from ghostforge.validator.mitre_map import MitreDAG
from ghostforge.validator.plausibility import dampen_probability, plausibility_score


def test_mitre_plausible() -> None:
    dag = MitreDAG()
    assert dag.is_plausible("Reconnaissance", []) is True
    assert dag.is_plausible("Exfiltration", ["Reconnaissance"]) is False
    assert plausibility_score("Exfiltration", []) < 1.0
    assert dampen_probability(0.8, 0.5) == 0.4


def test_hunt_rank() -> None:
    hunts = rank_hunts("LateralMovement", [])
    assert len(hunts) > 0
    assert hunts[0].reduces_stage in ["LateralMovement", "Discovery"]


def test_hunt_plan() -> None:
    plan = hunt_plan(0.7, "LateralMovement", [])
    assert len(plan) == 3
    assert plan[0]["after"] < plan[0]["before"]


def test_conformal() -> None:
    w = calibrate([0.1, 0.2, 0.15], alpha=0.1)
    assert w > 0
    low, high = interval(0.5, w)
    assert 0 <= low <= 0.5 <= high <= 1


def test_feedback() -> None:
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "feedback.parquet"
        save_feedback(Feedback(window_id=1, label="wrong", risk=0.7, stage="LateralMovement"), p)
        save_feedback(Feedback(window_id=2, label="correct"), p)
        loaded = load_feedback(p)
        assert len(loaded) == 2
        assert not needs_retrain(p, threshold=10)
        assert needs_retrain(p, threshold=2)
