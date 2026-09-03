"""Tests for twin modules."""

import torch

from ghostforge.twin.codebook import SoftCodebook
from ghostforge.twin.encoder import GraphEncoder
from ghostforge.twin.jepa import JEPAPredictor
from ghostforge.twin.stage_head import StageHead
from ghostforge.validator.mitre_map import MitreDAG
from ghostforge.validator.plausibility import plausibility_score


def test_encoder_empty() -> None:
    enc = GraphEncoder()
    z = enc(torch.tensor([]))
    assert z.shape[0] == 128


def test_encoder_forward() -> None:
    enc = GraphEncoder(in_dim=4)
    x = torch.randn(5, 4)
    z = enc(x)
    assert z.shape[0] == 128


def test_codebook() -> None:
    cb = SoftCodebook(num_codes=8, latent_dim=16)
    z = torch.randn(16)
    z_q, p = cb(z)
    assert z_q.shape[0] == 16
    assert p.shape[0] == 8
    assert abs(p.sum().item() - 1.0) < 1e-5


def test_jepa() -> None:
    pred = JEPAPredictor(latent_dim=16, hidden_dim=32)
    z = torch.randn(16)
    out = pred(z, "60s")
    assert out.shape[0] == 16


def test_stage_head() -> None:
    head = StageHead(latent_dim=16)
    z = torch.randn(16)
    stage, conf = head.predict(z)
    assert stage in [
        "Benign",
        "Reconnaissance",
        "InitialAccess",
        "Discovery",
        "LateralMovement",
        "CommandAndControl",
        "Exfiltration",
    ]
    assert 0 <= conf <= 1


def test_mitre_plausibility() -> None:
    dag = MitreDAG()
    assert dag.is_plausible("Reconnaissance", []) is True
    assert dag.is_plausible("Exfiltration", []) is False
    assert plausibility_score("Exfiltration", []) < 1.0
    assert plausibility_score("Reconnaissance", []) == 1.0
