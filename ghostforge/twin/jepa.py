"""JEPA predictor for multi resolution forecasting.

Predicts next latent z_{t+1} from current z_t at 3 time scales.
Trained only on benign traffic to learn normal physics.
"""

import torch
import torch.nn as nn


class JEPAPredictor(nn.Module):
    """Multi scale JEPA predictor."""

    def __init__(self, latent_dim: int = 128, hidden_dim: int = 256) -> None:
        super().__init__()
        self.latent_dim = latent_dim

        # One predictor per resolution
        self.predictors = nn.ModuleDict(
            {
                "10s": nn.Sequential(
                    nn.Linear(latent_dim, hidden_dim), nn.ReLU(), nn.Linear(hidden_dim, latent_dim)
                ),
                "60s": nn.Sequential(
                    nn.Linear(latent_dim, hidden_dim), nn.ReLU(), nn.Linear(hidden_dim, latent_dim)
                ),
                "300s": nn.Sequential(
                    nn.Linear(latent_dim, hidden_dim), nn.ReLU(), nn.Linear(hidden_dim, latent_dim)
                ),
            }
        )

        # Target encoder with EMA will be handled in training loop

    def forward(self, z: torch.Tensor, resolution: str = "60s") -> torch.Tensor:
        """Predict next latent at given resolution."""
        if resolution not in self.predictors:
            resolution = "60s"
        return self.predictors[resolution](z)

    def predict_all(self, z: torch.Tensor) -> dict[str, torch.Tensor]:
        """Predict at all resolutions."""
        return {k: v(z) for k, v in self.predictors.items()}

    def loss(self, z_pred: torch.Tensor, z_target: torch.Tensor) -> torch.Tensor:
        """Latent prediction loss, MSE in latent space."""
        return nn.functional.mse_loss(z_pred, z_target)
