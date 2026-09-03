"""FastAPI service for GhostForge.

Offline, no cloud calls. Provides ingest and inference.
"""

from pathlib import Path
from typing import List

from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from ghostforge.__version__ import __version__

app = FastAPI(
    title="GhostForge API",
    version=__version__,
    description="Network attack forecasting from traffic telemetry",
)


class HealthResponse(BaseModel):
    status: str
    version: str


class ForecastResponse(BaseModel):
    window_id: int
    risk: float
    stage: str
    confidence: float
    plausibility: float
    top_flows: List[dict] = []


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Health check, works offline."""
    return HealthResponse(status="ok", version=__version__)


@app.get("/mitre/{technique}")
def mitre_info(technique: str) -> dict:
    """Return MITRE technique info from bundled data."""
    # Bundled offline data, no fetch
    known = {
        "T1595": {"name": "Active Scanning", "tactic": "Reconnaissance"},
        "T1021": {"name": "Remote Services", "tactic": "Lateral Movement"},
        "T1071": {"name": "Application Layer Protocol", "tactic": "Command and Control"},
        "T1041": {"name": "Exfiltration Over C2", "tactic": "Exfiltration"},
    }
    return known.get(technique, {"name": "Unknown", "tactic": "Unknown"})


@app.post("/infer", response_model=ForecastResponse)
async def infer(file: UploadFile = File(...)) -> JSONResponse:
    """Infer from uploaded PCAP or CSV.

    Scaffold returns dummy forecast, real will run twin.
    """
    # Read file to verify upload works, discard content for scaffold
    _ = await file.read()

    dummy = ForecastResponse(
        window_id=0,
        risk=0.12,
        stage="Benign",
        confidence=0.92,
        plausibility=1.0,
        top_flows=[],
    )
    return JSONResponse(content=dummy.model_dump())


@app.post("/feedback")
def feedback(window_id: int, label: str) -> dict:
    """Accept analyst feedback for active learning."""
    # Scaffold, real will append to feedback.parquet
    return {"window_id": window_id, "label": label, "status": "recorded"}
