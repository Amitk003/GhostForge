# API

GhostForge API runs offline at http://localhost:8000. Docs at http://localhost:8000/docs.

## Health

`GET /health`

Check if service is up.

Response:

```json
{"status": "ok", "version": "0.1.0"}
```

curl:

```bash
curl http://localhost:8000/health
```

## MITRE lookup

`GET /mitre/{technique}`

Get info for a technique from bundled data, no internet needed.

Example `GET /mitre/T1021`:

```json
{"name": "Remote Services", "tactic": "Lateral Movement"}
```

curl:

```bash
curl http://localhost:8000/mitre/T1021
```

Known codes: T1595, T1021, T1071, T1041. Unknown returns `{"name":"Unknown"}`.

## Infer

`POST /infer`

Upload a PCAP or CSV and get a forecast.

Request: multipart file field `file`.

Response:

```json
{
  "window_id": 0,
  "risk": 0.12,
  "stage": "Benign",
  "confidence": 0.92,
  "plausibility": 1.0,
  "top_flows": []
}
```

Fields:

* window_id: which window this forecast is for
* risk: 0 to 1, higher means more drift from normal
* stage: MITRE stage like Reconnaissance or Benign
* confidence: model confidence 0 to 1
* plausibility: MITRE DAG check 0 to 1, lower means path is not plausible
* top_flows: list of flows that caused the drift

curl:

```bash
curl -X POST -F "file=@data/raw/sample.pcap" http://localhost:8000/infer
```

Python:

```python
import requests
with open("data/raw/sample.pcap", "rb") as f:
    r = requests.post("http://localhost:8000/infer", files={"file": f})
    print(r.json())
```

## Feedback

`POST /feedback?window_id=5&label=wrong`

Record analyst feedback for active learning. Labels: correct, wrong, missing.

Response:

```json
{"window_id": 5, "label": "wrong", "status": "recorded"}
```

curl:

```bash
curl -X POST "http://localhost:8000/feedback?window_id=5&label=wrong"
```

Feedback is saved locally to `feedback.parquet` and used in next training.

## Errors

* 422: missing file or bad params
* 500: server error, check logs with `docker logs`

All endpoints work without internet.
