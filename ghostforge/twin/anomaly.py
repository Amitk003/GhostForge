"""Anomaly scoring for drift from normal.

Combines latent drift and SVDD style distance to center.
Benign traffic should score low, attack high.
"""

import torch
import torch.nn as nn


class AnomalyScorer(nn.Module):
    """Scores drift of actual vs predicted."""

    def __init__(self, latent_dim: int = 128) -> None:
        super().__init__()
        self.latent_dim = latent_dim
        # Learnable center for SVDD, init at zero
        self.center = nn.Parameter(torch.zeros(latent_dim))
        # Learnable scale for drift to risk mapping
        self.scale = nn.Parameter(torch.tensor(1.0))

    def score(self, z_pred: torch.Tensor, z_actual: torch.Tensor) -> float:
        """Compute anomaly score for one pair.

        Score = weighted sum of prediction error and distance to center.
        """
        pred_err = torch.norm(z_pred - z_actual).item()
        dist_to_center = torch.norm(z_actual - self.center).item()
        # Combine, 70 percent pred error, 30 percent center dist
        raw = 0.7 * pred_err + 0.3 * dist_to_center
        # Scale to 0-1 via tanh
        risk = float(torch.tanh(torch.tensor(raw * self.scale.item())).item())
        return risk

    def batch_score(self, z_pred: torch.Tensor, z_actual: torch.Tensor) -> torch.Tensor:
        """Batch version returns tensor of scores."""
        # z_pred, z_actual: [B, latent]
        err = torch.norm(z_pred - z_actual, dim=1)
        dist = torch.norm(z_actual - self.center, dim=1)
        raw = 0.7 * err + 0.3 * dist
        risk = torch.tanh(raw * self.scale)
        return risk

    @torch.no_grad()
    def init_center(self, latents: torch.Tensor) -> None:
        """Init center to mean of benign latents, call before training."""
        if latents.numel() == 0:
            return
        mean = latents.mean(dim=0)
        self.center.data.copy_(mean)
