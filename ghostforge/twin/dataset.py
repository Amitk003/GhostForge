"""Dataset for snapshot sequences.

Provides paired (z_t, z_{t+1}) for JEPA training from windowed graphs.
Works with polars dataframes or precomputed latents.
"""

from dataclasses import dataclass
from pathlib import Path

import torch
from torch.utils.data import Dataset

from ghostforge.twin.encoder import GraphEncoder


@dataclass
class SequenceItem:
    """One training item: current and next latent."""

    z_current: torch.Tensor
    z_next: torch.Tensor
    window_id: int


class SnapshotSequenceDataset(Dataset):
    """Dataset that yields consecutive snapshot pairs.

    For scaffold, we generate synthetic latents from graph builder
    or load from parquet if available.
    """

    def __init__(self, latents: list[torch.Tensor], window_ids: list[int] | None = None) -> None:
        if len(latents) < 2:
            raise ValueError("Need at least 2 latents for sequence")
        self.latents = latents
        self.window_ids = window_ids or list(range(len(latents)))

    def __len__(self) -> int:
        return len(self.latents) - 1

    def __getitem__(self, idx: int) -> SequenceItem:
        return SequenceItem(
            z_current=self.latents[idx],
            z_next=self.latents[idx + 1],
            window_id=self.window_ids[idx],
        )

    @classmethod
    def from_snapshots(
        cls,
        snapshots: list[dict],
        encoder: GraphEncoder | None = None,
    ) -> "SnapshotSequenceDataset":
        """Build from raw snapshot dicts with edge lists.

        Each snapshot dict needs edge_attrs or graph.
        For now we use dummy latents if encoder not ready.
        """
        encoder = encoder or GraphEncoder()
        latents: list[torch.Tensor] = []
        ids: list[int] = []

        for i, snap in enumerate(snapshots):
            edge_attrs = snap.get("edge_attrs", [])
            # Use encoder helper
            if isinstance(edge_attrs, list) and edge_attrs:
                z = encoder.encode_snapshot(snap.get("edge_index", []), edge_attrs)
            else:
                # Dummy random latent for scaffold
                z = torch.randn(encoder.latent_dim) * 0.1
            latents.append(z)
            ids.append(snap.get("window_id", i))

        return cls(latents, ids)


def load_latents_from_dir(path: Path) -> list[torch.Tensor]:
    """Load precomputed latents from dir, if any. Returns empty if not found."""
    if not path.exists():
        return []
    # Scaffold: no file yet, return empty
    return []
