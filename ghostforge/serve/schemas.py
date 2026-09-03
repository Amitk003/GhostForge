"""Pydantic schemas for API.

Clear and typed models for request and response.
"""

from typing import List, Optional

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(description="Service status")
    version: str = Field(description="App version")
    uptime: float | None = Field(default=None, description="Uptime seconds")


class FlowItem(BaseModel):
    src: str
    dst: str
    port: int = 0
    flags: str = ""
    contrib: float = 0.0
    reason: str = ""


class ForecastRequest(BaseModel):
    window_id: int = 0
    features: dict | None = None


class ForecastResponse(BaseModel):
    window_id: int
    risk: float = Field(ge=0, le=1)
    stage: str
    confidence: float = Field(ge=0, le=1)
    plausibility: float = Field(ge=0, le=1)
    top_flows: List[FlowItem] = []
    mitre_technique: str = ""
    mitre_url: str = ""
    causal_path: str = ""
    low: float = 0.0
    high: float = 1.0


class MitreResponse(BaseModel):
    name: str
    tactic: str
    url: str = ""


class FeedbackRequest(BaseModel):
    window_id: int
    label: str = Field(description="correct, wrong, missing")
    note: str = ""


class FeedbackResponse(BaseModel):
    window_id: int
    label: str
    status: str
