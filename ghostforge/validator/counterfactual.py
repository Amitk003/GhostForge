"""Counterfactual Hunt actions for safe intervention.

Instead of risky auto block, we suggest what to check next and show
how risk would change if that evidence is collected.
"""

from dataclasses import dataclass
from typing import Dict, List

from ghostforge.validator.mitre_map import MitreDAG
from ghostforge.validator.plausibility import plausibility_score


@dataclass
class HuntAction:
    """One Hunt action the analyst can take."""

    id: str
    title: str
    target: str
    cost: str  # low, medium
    reduces_stage: str
    expected_drop: float  # 0 to 1


# Safe hunt actions, no blocking
HUNT_ACTIONS: List[HuntAction] = [
    HuntAction(id="hunt_auth", title="Pull auth logs", target="host", cost="low", reduces_stage="LateralMovement", expected_drop=0.3),
    HuntAction(id="hunt_dns", title="Check DNS queries", target="host", cost="low", reduces_stage="CommandAndControl", expected_drop=0.25),
    HuntAction(id="hunt_payload", title="Capture payload sample", target="flow", cost="medium", reduces_stage="Exfiltration", expected_drop=0.4),
    HuntAction(id="hunt_deceive", title="Enable honeypot on subnet", target="subnet", cost="low", reduces_stage="Discovery", expected_drop=0.2),
]


def rank_hunts(predicted_stage: str, seen: List[str] | None = None) -> List[HuntAction]:
    """Rank hunt actions by relevance to predicted stage."""
    seen = seen or []
    scored = []
    for h in HUNT_ACTIONS:
        score = 0.5
        if h.reduces_stage == predicted_stage:
            score = 1.0
        # If stage not plausible, prioritize its prereqs
        dag = MitreDAG()
        if not dag.is_plausible(predicted_stage, seen):
            missing = dag.missing_prereqs(predicted_stage, seen)
            if h.reduces_stage in missing:
                score = 0.9
        scored.append((score, h))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [h for _, h in scored]


def simulate_hunt(risk: float, action: HuntAction, plausibility: float = 1.0) -> Dict[str, float]:
    """Simulate risk after hunt action.

    Simple model: risk * (1 - drop * plausibility)
    """
    new_risk = risk * (1 - action.expected_drop * plausibility)
    delta = risk - new_risk
    return {"before": risk, "after": max(0.0, new_risk), "delta": delta, "action": action.id}


def hunt_plan(risk: float, stage: str, seen: List[str] | None = None) -> List[Dict[str, float]]:
    """Full hunt plan for current forecast."""
    seen = seen or []
    dag = MitreDAG()
    plaus = plausibility_score(stage, seen, dag)
    ranked = rank_hunts(stage, seen)
    plan = []
    for h in ranked[:3]:
        sim = simulate_hunt(risk, h, plaus)
        plan.append({"title": h.title, "target": h.target, "before": sim["before"], "after": sim["after"], "delta": sim["delta"]})
    return plan
