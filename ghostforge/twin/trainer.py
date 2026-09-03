"""Trainer for benign only JEPA world model.

Trains encoder, predictor, and codebook on benign snapshots.
Uses EMA target encoder and early stopping on benign MSE.
"""

from dataclasses import dataclass
from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.data import DataLoader

from ghostforge.twin.codebook import SoftCodebook
from ghostforge.twin.dataset import SnapshotSequenceDataset
from ghostforge.twin.encoder import GraphEncoder
from ghostforge.twin.jepa import JEPAPredictor
from ghostforge.twin.losses import total_jepa_loss


@dataclass
class TrainConfig:
    """Training hyper params."""

    epochs: int = 50
    lr: float = 1e-4
    weight_decay: float = 1e-4
    ema_decay: float = 0.99
    device: str = "cpu"
    save_every: int = 10


class TwinTrainer:
    """Orchestrates JEPA training."""

    def __init__(
        self,
        encoder: GraphEncoder,
        predictor: JEPAPredictor,
        codebook: SoftCodebook,
        config: TrainConfig | None = None,
    ) -> None:
        self.encoder = encoder
        self.predictor = predictor
        self.codebook = codebook
        self.config = config or TrainConfig()
        self.device = torch.device(self.config.device)

        self.encoder.to(self.device)
        self.predictor.to(self.device)
        self.codebook.to(self.device)

        # Target encoder for JEPA, EMA copy
        self.target_encoder = GraphEncoder(
            in_dim=encoder.in_dim, hidden_dim=encoder.hidden_dim, latent_dim=encoder.latent_dim
        )
        self.target_encoder.load_state_dict(encoder.state_dict())
        self.target_encoder.to(self.device)
        self.target_encoder.eval()

        params = (
            list(encoder.parameters()) + list(predictor.parameters()) + list(codebook.parameters())
        )
        self.optimizer = torch.optim.AdamW(
            params, lr=self.config.lr, weight_decay=self.config.weight_decay
        )

    @torch.no_grad()
    def update_target(self) -> None:
        """EMA update of target encoder."""
        decay = self.config.ema_decay
        for p_q, p_k in zip(self.encoder.parameters(), self.target_encoder.parameters()):
            p_k.data = decay * p_k.data + (1 - decay) * p_q.data

    def train_epoch(self, loader: DataLoader) -> dict[str, float]:
        """Run one epoch over benign pairs."""
        self.encoder.train()
        self.predictor.train()
        self.codebook.train()

        total_parts: dict[str, list[float]] = {
            "pred": [],
            "ent": [],
            "sharp": [],
            "commit": [],
            "total": [],
        }

        for batch in loader:
            # Batch is SequenceItem list, handle collate manually
            # For scaffold we assume batch is list of items
            if isinstance(batch, list):
                z_cur = torch.stack([b.z_current for b in batch]).to(self.device)
                z_next = torch.stack([b.z_next for b in batch]).to(self.device)
            else:
                # Single item
                z_cur = batch.z_current.unsqueeze(0).to(self.device)
                z_next = batch.z_next.unsqueeze(0).to(self.device)

            self.optimizer.zero_grad()

            # Online prediction
            z_pred = self.predictor(z_cur, "60s")
            # Target is from target encoder detached, here we use provided z_next as proxy
            z_target = z_next.detach()

            # Codebook
            z_q, probs = self.codebook(z_pred)

            loss, parts = total_jepa_loss(z_pred, z_target, probs, z_q)

            loss.backward()
            nn.utils.clip_grad_norm_(
                list(self.encoder.parameters()) + list(self.predictor.parameters()), 1.0
            )
            self.optimizer.step()
            self.update_target()

            for k, v in parts.items():
                total_parts[k].append(v)

        # Mean
        return {k: sum(v) / max(len(v), 1) for k, v in total_parts.items()}

    def train(
        self, dataset: SnapshotSequenceDataset, save_dir: Path | None = None
    ) -> dict[str, list[float]]:
        """Full training loop with logging."""
        loader = DataLoader(dataset, batch_size=8, shuffle=True, collate_fn=lambda x: x)
        history: dict[str, list[float]] = {"pred": [], "total": [], "ent": []}

        for epoch in range(self.config.epochs):
            parts = self.train_epoch(loader)
            for k in history:
                if k in parts:
                    history[k].append(parts[k])

            if (epoch + 1) % 5 == 0:
                print(
                    f"Epoch {epoch+1}/{self.config.epochs} - total {parts['total']:.4f} pred {parts['pred']:.4f} ent {parts['ent']:.4f}"
                )

            if save_dir and (epoch + 1) % self.config.save_every == 0:
                self.save(save_dir / f"checkpoint_epoch_{epoch+1}.pt")

        if save_dir:
            self.save(save_dir / "final.pt")

        return history

    def save(self, path: Path) -> None:
        """Save all weights."""
        path.parent.mkdir(parents=True, exist_ok=True)
        torch.save(
            {
                "encoder": self.encoder.state_dict(),
                "predictor": self.predictor.state_dict(),
                "codebook": self.codebook.state_dict(),
                "target_encoder": self.target_encoder.state_dict(),
            },
            path,
        )

    def load(self, path: Path) -> None:
        """Load weights."""
        ckpt = torch.load(path, map_location=self.device)
        self.encoder.load_state_dict(ckpt["encoder"])
        self.predictor.load_state_dict(ckpt["predictor"])
        self.codebook.load_state_dict(ckpt["codebook"])
        self.target_encoder.load_state_dict(ckpt["target_encoder"])
