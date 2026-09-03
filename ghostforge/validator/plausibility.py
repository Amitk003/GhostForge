"""Plausibility scoring for forecasts.

Dampens risk when predicted path violates MITRE prerequisites.
"""

from ghostforge.validator.mitre_map import MitreDAG


def plausibility_score(
    predicted_stage: str,
    seen_stages: list[str],
    dag: MitreDAG | None = None,
) -> float:
    """Compute plausibility 0 to 1.

    Returns 1.0 if plausible, lower if missing prereqs.
    """
    dag = dag or MitreDAG()
    if dag.is_plausible(predicted_stage, seen_stages):
        return 1.0

    missing = dag.missing_prereqs(predicted_stage, seen_stages)
    # Each missing prereq reduces score
    # 1 missing -> 0.5, 2 missing -> 0.3 etc
    if len(missing) == 1:
        return 0.5
    if len(missing) >= 2:
        return 0.3
    return 0.0


def dampen_probability(prob: float, plausibility: float) -> float:
    """Apply plausibility to raw model probability."""
    return prob * plausibility
