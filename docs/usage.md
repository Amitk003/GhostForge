# Usage

How to use GhostForge after you installed it.

## 1. Ingest a file

You can ingest a PCAP or a CSV or a Zeek log.

CLI:

```bash
ghostforge ingest --input data/raw/sample.pcap --out data/processed/
ghostforge ingest --input data/raw/cic_sample.csv --out data/processed/
```

What happens:

* Flow parser cleans the CSV, removes leakage fields, fixes missing values
* PCAP parser extracts TTL, window, flags, payload, scan score
* Windowing makes 60 second snapshots
* Graph builder makes a graph per window with hosts as nodes

Output is `data/processed/snapshots/` with parquet and `graphs/` with pt files.

## 2. Train (only on benign)

```bash
ghostforge train --config configs/base.yaml
# or
python scripts/train.py --config configs/base.yaml --data data/processed
```

Config `configs/base.yaml` sets window 60, latent 128, codebook 64. Training uses only benign windows. It learns normal physics. Attack windows are not used here.

The model saves to `models/jepa.pt` and `models/codebook.pt`.

## 3. Infer on new data

```bash
ghostforge infer --input data/processed/snapshot.parquet --out benchmarks/output.json
# or
python scripts/infer.py --input data/raw/test.pcap --out benchmarks/test.json
```

You get a JSON with:

```json
{
  "window_id": 5,
  "risk": 0.72,
  "stage": "LateralMovement",
  "confidence": 0.81,
  "plausibility": 1.0,
  "top_flows": [
    {"src": "10.0.0.5", "dst": "10.0.0.10", "port": 445, "contrib": 0.42}
  ]
}
```

## 4. Use the API

Start API: `make run-api`

Upload via curl:

```bash
curl -X POST -F "file=@data/raw/sample.pcap" http://localhost:8000/infer
```

Check health:

```bash
curl http://localhost:8000/health
```

Mitre lookup:

```bash
curl http://localhost:8000/mitre/T1021
```

Send feedback:

```bash
curl -X POST "http://localhost:8000/feedback?window_id=5&label=wrong"
```

## 5. Use the UI

Start UI: `make run-ui` then open http://localhost:8501

Four pages:

* Upload: drag PCAP or CSV, see ingest progress, click Run Inference
* Graph: slider to move across windows, see graph update, risky edges in red
* Risk Timeline: line chart of risk over next 10 windows with confidence cone
* Evidence: table of top flows, MITRE technique link, causal sentence, and buttons to mark correct or wrong

## 6. Feedback loop

When you mark a prediction as wrong in the UI or via API, it is saved to `feedback.parquet`. The next training run uses those contested windows to improve. This is how the system gets better on your network without sending data out.

## 7. Zeek live tail (advanced)

If you have Zeek running:

```bash
tail -F /usr/local/zeek/logs/current/conn.log | python -m ghostforge.serve.live_tail --out data/processed/
```

This tails the log and makes windows in real time. The API can then forecast live.

## Tips

* Start with a small PCAP like 10 MB to test the flow
* If you use CIC CSV, make sure it is the LycoS fixed version to avoid leakage
* Keep raw files in `data/raw`, they are ignored by git so you will not leak them by mistake
* Use `configs/inference.yaml` for faster inference with lower threshold
