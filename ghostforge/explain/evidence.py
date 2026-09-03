"""Evidence chain builder.

Creates human readable explanation for each prediction.
Top flows, codebook path, MITRE link.
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class EvidenceFlow:
    """One flow that contributed to prediction."""

    src: str
    dst: str
    port: int
    flags: str
    contrib: float
    reason: str


@dataclass
class EvidenceChain:
    """Full evidence for one prediction window."""

    window_id: int
    risk: float
    stage: str
    confidence: float
    codebook_path: List[int] = field(default_factory=list)
    top_flows: List[EvidenceFlow] = field(default_factory=list)
    mitre_technique: str = ""
    mitre_url: str = ""
    causal_path: str = ""
    plausibility: float = 1.0

    def to_dict(self) -> dict:
        return {
            "window_id": self.window_id,
            "risk": self.risk,
            "stage": self.stage,
            "confidence": self.confidence,
            "codebook_path": self.codebook_path,
            "top_flows": [f.__dict__ for f in self.top_flows],
            "mitre_technique": self.mitre_technique,
            "mitre_url": self.mitre_url,
            "causal_path": self.causal_path,
            "plausibility": self.plausibility,
        }


def build_evidence(
    window_id: int,
    risk: float,
    stage: str,
    top_flows_raw: List[dict],
) -> EvidenceChain:
    """Build evidence chain from raw top flows."""
    flows = []
    for f in top_flows_raw[:5]:
        flows.append(
            EvidenceFlow(
                src=f.get("src", "unknown"),
                dst=f.get("dst", "unknown"),
                port=f.get("port", 0),
                flags=f.get("flags", ""),
                contrib=f.get("contrib", 0.0),
                reason=f.get("reason", ""),
            )
        )

    mitre_map = {
        "Reconnaissance": ("T1595 Active Scanning", "https://attack.mitre.org/techniques/T1595/"),
        "LateralMovement": ("T1021 Remote Services", "https://attack.mitre.org/techniques/T1021/"),
        "CommandAndControl": ("T1071 Application Layer Protocol", "https://attack.mitre.org/techniques/T1071/"),
        "Exfiltration": ("T1041 Exfiltration Over C2", "https://attack.mitre.org/techniques/T1041/"),
    }

    technique, url = mitre_map.get(stage, ("", ""))

    return EvidenceChain(
        window_id=window_id,
        risk=risk,
        stage=stage,
        confidence=0.0,
        top_flows=flows,
        mitre_technique=technique,
        mitre_url=url,
        causal_path=f"{stage} predicted from flows",
    )
