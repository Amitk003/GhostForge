"""Central configuration using pydantic.

Simple and strict config for training and inference.
All values have defaults and can be overridden by yaml or env.
"""

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class IngestConfig(BaseModel):
    """Ingestion and windowing settings."""

    window_seconds: int = Field(default=60, description="Snapshot window size")
    stride_seconds: int = Field(default=30, description="Window stride")
    max_hosts: int = Field(default=5000, description="Max hosts per window")
    drop_ip_ports: bool = Field(default=True, description="Remove raw IPs and ports to avoid leakage")
    hash_role: bool = Field(default=True, description="Use role embedding instead of raw IP")


class TwinConfig(BaseModel):
    """World model twin settings."""

    latent_dim: int = Field(default=128, description="Latent size z_t")
    codebook_size: int = Field(default=64, description="Number of discrete regimes")
    resolutions: list[int] = Field(default=[10, 60, 300], description="Time scales in seconds")
    learning_rate: float = Field(default=1e-4, description="Adam learning rate")
    batch_size: int = Field(default=32, description="Training batch size")
    epochs: int = Field(default=50, description="Training epochs")


class ValidatorConfig(BaseModel):
    """Validator and MITRE settings."""

    plausibility_threshold: float = Field(default=0.5, description="Min plausibility to keep forecast")
    conformal_alpha: float = Field(default=0.1, description="Conformal coverage 1-alpha")


class ServeConfig(BaseModel):
    """Service settings."""

    host: str = Field(default="0.0.0.0")
    port_api: int = Field(default=8000)
    port_ui: int = Field(default=8501)


class GhostForgeConfig(BaseSettings):
    """Root config loaded from yaml or env."""

    project_name: str = Field(default="ghostforge")
    data_root: Path = Field(default=Path("data"))
    models_root: Path = Field(default=Path("models"))
    ingest: IngestConfig = Field(default_factory=IngestConfig)
    twin: TwinConfig = Field(default_factory=TwinConfig)
    validator: ValidatorConfig = Field(default_factory=ValidatorConfig)
    serve: ServeConfig = Field(default_factory=ServeConfig)

    model_config = {
        "env_prefix": "GHOSTFORGE_",
        "env_nested_delimiter": "__",
    }


def load_config(path: Path | None = None) -> GhostForgeConfig:
    """Load config from yaml file if provided, else defaults."""
    if path and path.exists():
        import yaml

        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        return GhostForgeConfig(**data)
    return GhostForgeConfig()
