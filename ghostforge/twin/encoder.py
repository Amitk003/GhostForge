"""Graph encoder for temporal host graphs.

Encodes G_t into latent z_t.
Designed to be light for CPU and strong for temporal drift.
"""

import torch
import torch.nn as nn


class GraphEncoder(nn.Module):
    """Simple graph encoder scaffold.

    Real version will use Temporal Graph Network with memory.
    This scaffold uses mean pooling for now to keep code runnable
    without heavy deps.
    """

    def __init__(self, in_dim: int = 16, hidden_dim: int = 64, latent_dim: int = 128) -> None:
        super().__init__()
        self.in_dim = in_dim
        self.hidden_dim = hidden_dim
        self.latent_dim = latent_dim
        self.mlp = nn.Sequential(
            nn.Linear(in_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, latent_dim),
        )
        self.graph_pool = nn.AdaptiveAvgPool1d(1)

    def forward(self, edge_attrs: torch.Tensor) -> torch.Tensor:
        """Encode edge attributes into latent.

        Args:
            edge_attrs: Tensor of shape [num_edges, in_dim]

        Returns:
            Latent tensor [latent_dim]
        """
        if edge_attrs.numel() == 0:
            return torch.zeros(self.latent_dim)

        x = self.mlp(edge_attrs)  # [E, latent]
        # Mean pool over edges to get graph level
        z = x.mean(dim=0)  # [latent]
        return z

    def encode_snapshot(self, edge_list: list[list[int]], edge_attrs: list[float]) -> torch.Tensor:
        """Helper to encode from raw lists."""
        if not edge_attrs:
            return torch.zeros(self.latent_dim)
        t = torch.tensor(edge_attrs, dtype=torch.float32).unsqueeze(1)
        # Pad to in_dim
        if t.shape[1] < self.in_dim:
            pad = torch.zeros(t.shape[0], self.in_dim - t.shape[1])
            t = torch.cat([t, pad], dim=1)
        else:
            t = t[:, : self.in_dim]
        return self.forward(t)
