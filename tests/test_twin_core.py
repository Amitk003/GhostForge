"""Tests for twin core training and rollout."""

import torch

from ghostforge.twin.anomaly import AnomalyScorer
from ghostforge.twin.codebook import SoftCodebook
from ghostforge.twin.dataset import SnapshotSequenceDataset
from ghostforge.twin.encoder import GraphEncoder
from ghostforge.twin.jepa import JEPAPredictor
from ghostforge.twin.losses import total_jepa_loss
from ghostforge.twin.rollout import RolloutEngine, conformal_calibrate
from ghostforge.twin.trainer import TrainConfig, TwinTrainer


def test_losses() -> None:
    z_pred = torch.randn(4, 16)
    z_target = torch.randn(4, 16)
    probs = torch.softmax(torch.randn(4, 8), dim=1)
    z_q = torch.randn(4, 16)
    loss, parts = total_jepa_loss(z_pred, z_target, probs, z_q)
    assert loss.item() > -10
    assert "total" in parts


def test_dataset() -> None:
    latents = [torch.randn(16) for _ in range(5)]
    ds = SnapshotSequenceDataset(latents)
    assert len(ds) == 4
    item = ds[0]
    assert item.z_current.shape[0] == 16


def test_trainer_one_epoch() -> None:
    enc = GraphEncoder(in_dim=4, hidden_dim=8, latent_dim=16)
    pred = JEPAPredictor(latent_dim=16, hidden_dim=32)
    cb = SoftCodebook(num_codes=8, latent_dim=16)
    trainer = TwinTrainer(enc, pred, cb, TrainConfig(epochs=1, device="cpu"))
    latents = [torch.randn(16) for _ in range(5)]
    ds = SnapshotSequenceDataset(latents)
    history = trainer.train(ds)
    assert "total" in history


def test_rollout() -> None:
    pred = JEPAPredictor(latent_dim=16, hidden_dim=32)
    engine = RolloutEngine(pred)
    z = torch.randn(16)
    steps = engine.rollout(z)
    assert len(steps) == 10
    assert 0 <= steps[0].risk <= 1


def test_anomaly() -> None:
    scorer = AnomalyScorer(latent_dim=16)
    z_pred = torch.randn(16)
    z_actual = torch.randn(16)
    risk = scorer.score(z_pred, z_actual)
    assert 0 <= risk <= 1


def test_conformal() -> None:
    w = conformal_calibrate([0.1, 0.2, 0.3], alpha=0.1)
    assert w >= 0
