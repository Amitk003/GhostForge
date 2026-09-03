"""Stage head for MITRE ATT&CK mapping.

Maps latent z_t to attack stages. Decoupled from dynamics,
trained only on labeled windows, keeps dynamics benign only.
"""

import torch
import torch.nn as nn


STAGES = [
    "Benign",
    "Reconnaissance",
    "InitialAccess",
    "Discovery",
    "LateralMovement",
    "CommandAndControl",
    "Exfiltration",
]


class StageHead(nn.Module):
    """Simple MLP classifier for stages."""

    def __init__(self, latent_dim: int = 128, num_stages: int = len(STAGES)) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(latent_dim, 64),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(64, num_stages),
        )

    def forward(self, z: torch.Tensor) -> torch.Tensor:
        """Return logits for stages."""
        return self.net(z)

    def predict(self, z: torch.Tensor) -> tuple[str, float]:
        """Return stage name and confidence."""
        logits = self.forward(z)
        probs = torch.softmax(logits, dim=-1)
        idx = int(torch.argmax(probs).item())
        conf = float(probs[idx].item())
        return STAGES[idx], conf
