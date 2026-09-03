"""FastAPI service for GhostForge.

Offline, no cloud calls. Provides ingest and inference.
"""

import time
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from ghostforge.__version__ import __version__
from ghostforge.serve.schemas import (
    FeedbackRequest,
    FeedbackResponse,
    ForecastResponse,
    HealthResponse,
    MitreResponse,
)
from ghostforge.twin.feedback import Feedback, save_feedback

app = FastAPI(
    title="GhostForge API",
    version=__version__,
    description="Network attack forecasting from traffic telemetry",
)

# Allow local UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

start_time = time.time()


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Health check, works offline."""
    uptime = time.time() - start_time
    return HealthResponse(status="ok", version=__version__, uptime=uptime)


@app.get("/mitre/{technique}", response_model=MitreResponse)
def mitre_info(technique: str) -> MitreResponse:
    """Return MITRE technique info from bundled offline data."""
    known = {
        "T1595": {
            "name": "Active Scanning",
            "tactic": "Reconnaissance",
            "url": "https://attack.mitre.org/techniques/T1595/",
        },
        "T1021": {
            "name": "Remote Services",
            "tactic": "Lateral Movement",
            "url": "https://attack.mitre.org/techniques/T1021/",
        },
        "T1071": {
            "name": "Application Layer Protocol",
            "tactic": "Command and Control",
            "url": "https://attack.mitre.org/techniques/T1071/",
        },
        "T1041": {
            "name": "Exfiltration Over C2",
            "tactic": "Exfiltration",
            "url": "https://attack.mitre.org/techniques/T1041/",
        },
        "T1190": {
            "name": "Exploit Public Facing Application",
            "tactic": "Initial Access",
            "url": "https://attack.mitre.org/techniques/T1190/",
        },
        "T1083": {
            "name": "File and Directory Discovery",
            "tactic": "Discovery",
            "url": "https://attack.mitre.org/techniques/T1083/",
        },
    }
    data = known.get(technique, {"name": "Unknown", "tactic": "Unknown", "url": ""})
    return MitreResponse(**data)


@app.post("/infer", response_model=ForecastResponse)
async def infer(file: UploadFile = File(...)) -> JSONResponse:
    """Infer from uploaded PCAP or CSV.

    Validates file type and size, then runs lightweight forecast.
    Real twin will be used when model is loaded, for now returns dummy
    but with proper validation and error handling.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    allowed = {".pcap", ".pcapng", ".csv", ".log", ".txt", ".gz"}
    suffix = Path(file.filename).suffix.lower()
    if suffix not in allowed:
        raise HTTPException(status_code=400, detail=f"File type {suffix} not allowed")

    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Empty file")
    if len(content) > 100 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large, max 100 MB")

    # Simple heuristic for scaffold: if filename contains attack, return higher risk
    is_suspicious = any(x in file.filename.lower() for x in ["attack", "bot", "scan", "infil"])
    risk = 0.72 if is_suspicious else 0.12
    stage = "LateralMovement" if is_suspicious else "Benign"
    confidence = 0.81 if is_suspicious else 0.92

    dummy = ForecastResponse(
        window_id=0,
        risk=risk,
        stage=stage,
        confidence=confidence,
        plausibility=1.0,
        top_flows=[],
        mitre_technique="T1021 Remote Services" if is_suspicious else "",
        mitre_url="https://attack.mitre.org/techniques/T1021/" if is_suspicious else "",
        causal_path=f"{stage} from {file.filename}",
        low=max(0, risk - 0.05),
        high=min(1, risk + 0.05),
    )
    return JSONResponse(content=dummy.model_dump())


@app.post("/feedback", response_model=FeedbackResponse)
def feedback(req: FeedbackRequest) -> FeedbackResponse:
    """Accept analyst feedback for active learning, saves locally."""
    if req.label not in {"correct", "wrong", "missing"}:
        raise HTTPException(status_code=400, detail="label must be correct, wrong, or missing")
    try:
        save_feedback(Feedback(window_id=req.window_id, label=req.label, note=req.note))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return FeedbackResponse(window_id=req.window_id, label=req.label, status="recorded")


@app.get("/export/sigma/{technique}")
def export_sigma(technique: str) -> dict:
    """Export Sigma rule for a technique, offline template."""
    mitre = mitre_info(technique)
    rule = f"""
title: GhostForge {mitre.name}
logsource:
  category: network
detection:
  selection:
    technique: {technique}
  condition: selection
level: high
"""
    return {"technique": technique, "sigma": rule.strip()}
