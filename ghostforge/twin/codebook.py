"""Soft codebook for discrete regime learning.

Each prototype represents a network regime, like benign, recon, lateral.
Implements soft quantization to avoid collapse.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F


class SoftCodebook(nn.Module):
    """Differentiable codebook with soft assignment."""

    def __init__(self, num_codes: int = 64, latent_dim: int = 128, tau: float = 1.0) -> None:
        super().__init__()
        self.num_codes = num_codes
        self.latent_dim = latent_dim
        self.tau = tau
        self.prototypes = nn.Parameter(torch.randn(num_codes, latent_dim) * 0.1)

    def forward(self, z: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        """Soft quantize z.

        Args:
            z: Latent vector [latent_dim] or [B, latent_dim]

        Returns:
            z_q: Quantized vector same shape as z
            p: Assignment probabilities [num_codes]
        """
        if z.dim() == 1:
            z = z.unsqueeze(0)

        # Distance to prototypes
        dist = torch.cdist(z, self.prototypes)  # [B, K]
        logits = -dist / self.tau
        p = F.softmax(logits, dim=-1)  # [B, K]

        # Soft quantized
        z_q = p @ self.prototypes  # [B, latent]

        if z_q.shape[0] == 1:
            return z_q.squeeze(0), p.squeeze(0)
        return z_q, p

    def entropy(self, p: torch.Tensor) -> torch.Tensor:
        """Batch entropy for collapse prevention."""
        p_mean = p.mean(dim=0) if p.dim() > 1 else p
        # Avoid log 0
        p_mean = p_mean.clamp(min=1e-8)
        return -(p_mean * p_mean.log()).sum()

    def usage(self, p: torch.Tensor) -> float:
        """Fraction of codes used."""
        if p.dim() == 1:
            p = p.unsqueeze(0)
        # Count codes with mean prob > 0.01
        mean_p = p.mean(dim=0)
        used = (mean_p > 0.01).sum().item()
        return used / self.num_codes
