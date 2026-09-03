"""Feature attribution for explainability.

Simple, fast, and offline. No heavy SHAP dependency required for baseline.
Provides per feature contribution to risk.
"""

from typing import Dict, List

import numpy as np


def feature_attribution(
    features: Dict[str, float],
    baseline: Dict[str, float] | None = None,
    weights: Dict[str, float] | None = None,
) -> List[Dict[str, float]]:
    """Compute attribution as weighted delta from baseline.

    This is a lightweight proxy for SHAP. Real SHAP will replace this
    when explain deps are installed, but this keeps API stable and
    offline.

    Args:
        features: Current window features
        baseline: Benign baseline means, if None uses zeros
        weights: Per feature importance from model, if None uses uniform

    Returns:
        Sorted list of {feature, value, baseline, contrib}
    """
    baseline = baseline or {k: 0.0 for k in features}
    weights = weights or {k: 1.0 for k in features}

    out: List[Dict[str, float]] = []
    for k, v in features.items():
        b = baseline.get(k, 0.0)
        w = weights.get(k, 1.0)
        # Simple delta times weight
        contrib = (v - b) * w
        out.append({"feature": k, "value": float(v), "baseline": float(b), "contrib": float(contrib)})

    # Sort by absolute contribution
    out.sort(key=lambda x: abs(x["contrib"]), reverse=True)
    return out


def top_features(attributions: List[Dict[str, float]], k: int = 5) -> List[Dict[str, float]]:
    """Get top k attributions."""
    return attributions[:k]


def normalize_contrib(attributions: List[Dict[str, float]]) -> List[Dict[str, float]]:
    """Normalize contributions to sum to 1 for display."""
    total = sum(abs(a["contrib"]) for a in attributions)
    if total == 0:
        return attributions
    for a in attributions:
        a["contrib_norm"] = a["contrib"] / total
    return attributions
