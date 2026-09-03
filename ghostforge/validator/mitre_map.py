"""MITRE ATT&CK DAG and prerequisites.

Simple DAG that encodes causal prerequisites for stages.
Used as post hoc validator, not joint training.
"""

from dataclasses import dataclass, field


@dataclass
class StageNode:
    """Node in MITRE stage DAG."""

    name: str
    requires: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)


# Default DAG, can be overridden by yaml
DEFAULT_DAG: dict[str, StageNode] = {
    "Reconnaissance": StageNode(
        name="Reconnaissance", requires=[], evidence=["port_scan", "syn_flood"]
    ),
    "InitialAccess": StageNode(
        name="InitialAccess", requires=["Reconnaissance"], evidence=["brute_force", "exploit"]
    ),
    "Discovery": StageNode(
        name="Discovery", requires=["InitialAccess"], evidence=["dns_query", "port_scan"]
    ),
    "LateralMovement": StageNode(
        name="LateralMovement", requires=["Discovery"], evidence=["smb_445", "winrm_5985", "rpd"]
    ),
    "CommandAndControl": StageNode(
        name="CommandAndControl",
        requires=["LateralMovement"],
        evidence=["dns_tunnel", "http_beacon"],
    ),
    "Exfiltration": StageNode(
        name="Exfiltration",
        requires=["CommandAndControl"],
        evidence=["large_outbound", "dns_tunnel"],
    ),
}


class MitreDAG:
    """Simple DAG checker."""

    def __init__(self, dag: dict[str, StageNode] | None = None) -> None:
        self.dag = dag or DEFAULT_DAG

    def is_plausible(self, predicted: str, seen_stages: list[str]) -> bool:
        """Check if predicted stage is plausible given seen stages."""
        node = self.dag.get(predicted)
        if not node:
            return False
        # All requires must be in seen
        for req in node.requires:
            if req not in seen_stages:
                return False
        return True

    def missing_prereqs(self, predicted: str, seen_stages: list[str]) -> list[str]:
        """Return missing prerequisites."""
        node = self.dag.get(predicted)
        if not node:
            return []
        return [r for r in node.requires if r not in seen_stages]

    def all_stages(self) -> list[str]:
        return list(self.dag.keys())
