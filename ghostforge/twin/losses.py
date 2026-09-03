"""Losses for JEPA training.

Includes latent prediction loss, codebook entropy, and commitment.
Designed for stable training without collapse.
"""

import torch
import torch.nn.functional as F


def latent_pred_loss(z_pred: torch.Tensor, z_target: torch.Tensor) -> torch.Tensor:
    """MSE between predicted and target latent, stop grad on target."""
    return F.mse_loss(z_pred, z_target.detach())


def codebook_entropy_loss(probs: torch.Tensor) -> torch.Tensor:
    """Maximize batch entropy to prevent collapse, so loss is negative entropy."""
    # probs: [B, K] or [K]
    if probs.dim() == 1:
        probs = probs.unsqueeze(0)
    mean_p = probs.mean(dim=0).clamp(min=1e-8)
    entropy = -(mean_p * mean_p.log()).sum()
    # We want to maximize entropy, so minimize negative entropy
    return -entropy


def sample_sharpness_loss(probs: torch.Tensor) -> torch.Tensor:
    """Minimize per sample entropy to make assignments sharp."""
    if probs.dim() == 1:
        probs = probs.unsqueeze(0)
    p = probs.clamp(min=1e-8)
    ent = -(p * p.log()).sum(dim=1).mean()
    return ent


def commitment_loss(z: torch.Tensor, z_q: torch.Tensor) -> torch.Tensor:
    """Keep z close to its quantized version."""
    return F.mse_loss(z, z_q.detach())


def total_jepa_loss(
    z_pred: torch.Tensor,
    z_target: torch.Tensor,
    probs: torch.Tensor,
    z_q: torch.Tensor,
    w_pred: float = 1.0,
    w_ent: float = 0.1,
    w_sharp: float = 0.05,
    w_commit: float = 0.1,
) -> tuple[torch.Tensor, dict[str, float]]:
    """Combine all losses with weights."""
    lp = latent_pred_loss(z_pred, z_target)
    le = codebook_entropy_loss(probs)
    ls = sample_sharpness_loss(probs)
    lc = commitment_loss(z_pred, z_q)

    total = w_pred * lp + w_ent * le + w_sharp * ls + w_commit * lc
    parts = {
        "pred": float(lp.item()),
        "ent": float(le.item()),
        "sharp": float(ls.item()),
        "commit": float(lc.item()),
        "total": float(total.item()),
    }
    return total, parts
