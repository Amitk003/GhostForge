"""Evidence chain builder.

Creates human readable explanation for each prediction.
Top flows, codebook path, MITRE link.
"""

from dataclasses import dataclass, field


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
    codebook_path: list[int] = field(default_factory=list)
    top_flows: list[EvidenceFlow] = field(default_factory=list)
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


MITRE_MAP = {
    "Benign": ("", ""),
    "Reconnaissance": ("T1595 Active Scanning", "https://attack.mitre.org/techniques/T1595/"),
    "InitialAccess": (
        "T1190 Exploit Public Facing Application",
        "https://attack.mitre.org/techniques/T1190/",
    ),
    "Discovery": (
        "T1083 File and Directory Discovery",
        "https://attack.mitre.org/techniques/T1083/",
    ),
    "LateralMovement": ("T1021 Remote Services", "https://attack.mitre.org/techniques/T1021/"),
    "CommandAndControl": (
        "T1071 Application Layer Protocol",
        "https://attack.mitre.org/techniques/T1071/",
    ),
    "Exfiltration": ("T1041 Exfiltration Over C2", "https://attack.mitre.org/techniques/T1041/"),
}


def build_evidence(
    window_id: int,
    risk: float,
    stage: str,
    top_flows_raw: list[dict],
    codebook_path: list[int] | None = None,
    confidence: float = 0.0,
    plausibility: float = 1.0,
    causal_path: str | None = None,
) -> EvidenceChain:
    """Build evidence chain from raw top flows with full context."""
    flows = []
    for f in top_flows_raw[:5]:
        flows.append(
            EvidenceFlow(
                src=str(f.get("src", f.get("src_ip", "unknown"))),
                dst=str(f.get("dst", f.get("dst_ip", "unknown"))),
                port=int(f.get("port", f.get("dst_port", 0)) or 0),
                flags=str(f.get("flags", "")),
                contrib=float(f.get("contrib", f.get("attention", 0.0)) or 0.0),
                reason=str(f.get("reason", "high drift")),
            )
        )

    technique, url = MITRE_MAP.get(stage, ("", ""))

    if not causal_path:
        if codebook_path:
            causal_path = f"Regime path {' -> '.join(map(str, codebook_path))} led to {stage}"
        else:
            causal_path = f"{stage} predicted from {len(flows)} flows"

    return EvidenceChain(
        window_id=window_id,
        risk=risk,
        stage=stage,
        confidence=confidence,
        codebook_path=codebook_path or [],
        top_flows=flows,
        mitre_technique=technique,
        mitre_url=url,
        causal_path=causal_path,
        plausibility=plausibility,
    )


def evidence_to_markdown(evidence: EvidenceChain) -> str:
    """Render evidence as simple markdown for docs or UI."""
    lines = [
        f"Window {evidence.window_id} - Risk {evidence.risk:.2f} - Stage {evidence.stage}",
        f"Confidence {evidence.confidence:.2f} - Plausibility {evidence.plausibility:.2f}",
        f"MITRE {evidence.mitre_technique} {evidence.mitre_url}",
        f"Causal {evidence.causal_path}",
        "Top flows:",
    ]
    for f in evidence.top_flows:
        lines.append(
            f"- {f.src} -> {f.dst}:{f.port} flags={f.flags} contrib={f.contrib:.2f} reason={f.reason}"
        )
    return "\n".join(lines)
