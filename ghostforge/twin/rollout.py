"""Rollout for K step forecasting.

Autoregresses predictor to get risk timeline with confidence cone.
Uses ensemble and simple conformal calibration.
"""

from dataclasses import dataclass

import torch

from ghostforge.twin.codebook import SoftCodebook
from ghostforge.twin.jepa import JEPAPredictor


@dataclass
class RolloutConfig:
    """Config for rollout."""

    steps: int = 10
    resolution: str = "60s"
    ensemble: int = 3


@dataclass
class RolloutStep:
    """One step of rollout."""

    step: int
    risk: float
    confidence: float
    low: float
    high: float
    stage: str = "Benign"


class RolloutEngine:
    """K step rollout with ensemble."""

    def __init__(self, predictor: JEPAPredictor, codebook: SoftCodebook | None = None) -> None:
        self.predictor = predictor
        self.codebook = codebook

    @torch.no_grad()
    def rollout(
        self, z_start: torch.Tensor, config: RolloutConfig | None = None
    ) -> list[RolloutStep]:
        """Roll out from z_start for K steps.

        Uses simple drift as risk: distance from start grows means higher risk.
        Real version will use learned risk head and conformal intervals.
        """
        config = config or RolloutConfig()
        self.predictor.eval()

        steps: list[RolloutStep] = []
        z = z_start

        for k in range(1, config.steps + 1):
            # Ensemble: run predictor multiple times with small noise
            preds = []
            for _ in range(config.ensemble):
                z_next = self.predictor(z, config.resolution)
                # Add tiny noise for ensemble diversity in scaffold
                z_next = z_next + torch.randn_like(z_next) * 0.01
                preds.append(z_next)

            mean_pred = torch.stack(preds).mean(dim=0)
            std = torch.stack(preds).std(dim=0).mean().item()

            # Risk as normalized distance from start
            drift = torch.norm(mean_pred - z_start).item()
            # Map drift to 0-1 via tanh
            risk = float(torch.tanh(torch.tensor(drift * 0.5)).item())
            low = max(0.0, risk - std * 0.5)
            high = min(1.0, risk + std * 0.5)
            conf = 1.0 - min(std, 0.5) * 2

            steps.append(RolloutStep(step=k, risk=risk, low=low, high=high, confidence=conf))

            z = mean_pred

        return steps

    def risk_timeline(self, z_start: torch.Tensor, steps: int = 10) -> dict:
        """Return dict for API and UI."""
        cfg = RolloutConfig(steps=steps)
        rolled = self.rollout(z_start, cfg)
        return {
            "steps": [r.step for r in rolled],
            "risk": [r.risk for r in rolled],
            "low": [r.low for r in rolled],
            "high": [r.high for r in rolled],
            "confidence": [r.confidence for r in rolled],
        }


def conformal_calibrate(risks: list[float], alpha: float = 0.1) -> float:
    """Simple conformal interval width from calibration risks.

    Returns width to add to risk for coverage 1-alpha.
    For scaffold we use quantile.
    """
    if not risks:
        return 0.1
    risks_sorted = sorted(risks)
    q = 1 - alpha
    idx = min(int(len(risks_sorted) * q), len(risks_sorted) - 1)
    return float(risks_sorted[idx] * 0.1)
