"""Tests for serve API."""

from fastapi.testclient import TestClient

from ghostforge.serve.api import app

client = TestClient(app)


def test_health() -> None:
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_mitre() -> None:
    r = client.get("/mitre/T1021")
    assert r.status_code == 200
    assert r.json()["tactic"] == "Lateral Movement"


def test_mitre_unknown() -> None:
    r = client.get("/mitre/T9999")
    assert r.status_code == 200
    assert r.json()["name"] == "Unknown"


def test_infer_missing_file() -> None:
    r = client.post("/infer", files={})
    assert r.status_code == 422


def test_infer_empty() -> None:
    r = client.post("/infer", files={"file": ("empty.csv", b"", "text/csv")})
    assert r.status_code == 400


def test_infer_ok() -> None:
    r = client.post("/infer", files={"file": ("sample.csv", b"a,b\n1,2", "text/csv")})
    assert r.status_code == 200
    assert "risk" in r.json()


def test_feedback() -> None:
    r = client.post("/feedback", json={"window_id": 1, "label": "wrong"})
    assert r.status_code == 200
    assert r.json()["status"] == "recorded"


def test_feedback_bad_label() -> None:
    r = client.post("/feedback", json={"window_id": 1, "label": "bad"})
    assert r.status_code == 400


def test_sigma_export() -> None:
    r = client.get("/export/sigma/T1021")
    assert r.status_code == 200
    assert "sigma" in r.json()
