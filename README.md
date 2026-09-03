# GhostForge

**Predict attacks before they complete. Not after.**

GhostForge is an open source world model for network security. It learns how your network normally behaves, then forecasts when traffic starts to drift toward an attack. It runs fully offline, explains every prediction, and plugs into the tools you already use.

---

## Why GhostForge

Most intrusion systems look at one flow at a time and say benign or malicious. Real attacks are not one packet. They are a sequence: a scan, a probe, a login attempt, a move to another host, a command channel.

GhostForge learns the sequence.

*   **Forecast, not just detect.** See an infiltration risk timeline for the next 10 minutes, not just an alert for the last packet.
*   **Fewer false alarms.** Trained only on benign traffic, so it flags real drift, not known signatures. Validated with MITRE ATT&CK logic to cut noisy alerts.
*   **Graph view of your network.** Hosts are nodes, flows are edges. Lateral movement shows as movement on the graph, not a row in a table.
*   **Explain every alert.** Top flows, ports, flags, and MITRE stage that caused the shift, with links to technique details. No black box.
*   **Analyst can contest.** Mark a prediction as wrong. The system learns from your feedback.
*   **Offline and private.** No cloud calls. Runs on your machine or on premise. Your PCAPs never leave your network.
*   **Works with your stack.** Ingests PCAP or CSV or Zeek logs. Exports Sigma and STIX. Integrates with Suricata, Wazuh, and any NetFlow exporter.

If you run a SOC, an enterprise network, or critical infrastructure, GhostForge gives you early warning with less noise.

---

## How It Works in 30 Seconds

1. You give it traffic: a PCAP file or flow CSV or Zeek `conn.log`.
2. It builds time windows (60 second snapshots) and a temporal graph of hosts and flows.
3. The world model predicts the next graph state from the current one. This model was trained only on benign traffic, so it knows what normal looks like.
4. When real traffic drifts from the predicted normal, it raises risk, maps the drift to MITRE stages (Recon, Initial Access, Lateral Movement, Command and Control, Exfiltration), and shows which flows caused it.
5. You see a risk timeline, a graph playback, and an evidence chain you can act on.

The core is a Temporal Graph Network plus a multi scale JEPA predictor with a discrete codebook. In simple terms, it learns normal physics at different time scales and spots when physics breaks.

---

## Quick Start

### Option 1: Docker (recommended)

```bash
docker build -t ghostforge:latest .
docker run --rm -p 8000:8000 -p 8501:8501 -v $(pwd)/data:/app/data ghostforge:latest
```

Open `http://localhost:8501` for the dashboard and `http://localhost:8000/docs` for the API.

### Option 2: Local Python

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev,ml,pcap,explain]"

# Run API
make run-api

# In another terminal, run UI
make run-ui
```

### Try With Sample Data

```bash
# Put a PCAP or CIC CSV in data/raw
ghostforge ingest --input data/raw/sample.pcap --out data/processed/
ghostforge infer --input data/processed/snapshot.parquet --out benchmarks/sample.json
```

---

## Features

*   **Dual ingestion:** flow level (NetFlow/IPFIX, CIC CSV, Argus) and packet level (PCAP via Scapy, Zeek)
*   **Temporal graph world model:** learns `P(next_state | current_state)` without attack labels
*   **Multi scale forecast:** 10 second, 60 second, 300 second predictors with calibrated confidence
*   **MITRE ATT&CK mapping:** from Recon to Exfiltration with prerequisites validation
*   **Explainability:** attention over flows, SHAP style feature attribution, codebook path
*   **Counterfactual Hunt actions:** what to check next to reduce risk, not risky auto block
*   **Offline dashboard:** Streamlit app with graph playback, risk cone, and feedback loop
*   **Evaluation you can trust:** in dataset, cross dataset, and held out family tests with lead time at 1 percent FPR

---

## Documentation

All docs are in `docs/` and written in simple English.

*   [Overview](docs/overview.md) - what the project does and why it matters
*   [Architecture](docs/architecture.md) - system design without jargon
*   [Setup](docs/setup.md) - install and run step by step
*   [Usage](docs/usage.md) - ingest, train, infer, and UI guide
*   [Evaluation](docs/evaluation.md) - benchmarks and how we measure
*   [API](docs/api.md) - API reference
*   [Logs](docs/logs.md) - command history and daily notes

---

## Benchmarks Preview

We compare against a logistic regression baseline on the same features. The goal is not just higher F1, but earlier warning at the same false positive rate.

| Model | F1 | Precision | Recall | FPR | Lead Time @1 percent FPR |
|-------|----|-----------|--------|-----|--------------------------|
| Logistic Regression (baseline) | to be measured | - | - | - | - |
| GhostForge Twin | to be measured | - | - | - | - |

See `benchmarks/` for full results. Honest reporting, including where we fail.

---

## Project Structure

```
ghostforge/
  ingest/     Flow and packet parsers, windowing, graph building
  twin/       Graph encoder, JEPA predictor, codebook, stage head
  validator/  MITRE DAG and plausibility checks
  explain/    Evidence chains and attributions
  serve/      FastAPI service and Streamlit app
configs/      Training and inference settings
scripts/      Train, evaluate, and infer entry points
docs/         Simple English documentation
tests/        Unit and integration tests
```

---

## Security and Privacy

*   No cloud dependency. All inference is local.
*   Your raw traffic stays on your machine. Only optional contested windows are stored for retraining.
*   Data folders `data/raw` and `data/processed` are ignored by git.

---

## Contributing

We welcome issues and pull requests. Please run `make lint` and `make test` before submitting.

---

## License

Apache 2.0. See [LICENSE](LICENSE).

---

## Contact

GitHub: https://github.com/Amitk003/GhostForge
For questions, open an issue. For security reports, use a private advisory.
