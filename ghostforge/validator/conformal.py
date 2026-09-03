"""Conformal calibration for forecast confidence.

Provides calibrated intervals for risk timeline, offline and simple.
"""

import numpy as np


def calibrate(scores: list[float], alpha: float = 0.1) -> float:
    """Calibrate interval width from benign calibration scores.

    Uses quantile of absolute residuals. Returns width to add.
    """
    if not scores:
        return 0.1
    arr = np.array(scores)
    q = np.quantile(np.abs(arr), 1 - alpha)
    return float(q * 0.5 + 0.05)


def interval(risk: float, width: float) -> tuple[float, float]:
    """Return low high interval around risk."""
    low = max(0.0, risk - width)
    high = min(1.0, risk + width)
    return low, high


def coverage(risks: list[float], lows: list[float], highs: list[float]) -> float:
    """Check empirical coverage, for testing."""
    if not risks:
        return 0.0
    hits = sum(1 for r, lo, hi in zip(risks, lows, highs) if lo <= r <= hi)
    return hits / len(risks)
