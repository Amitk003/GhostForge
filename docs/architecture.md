# Architecture

This doc explains how GhostForge works in simple terms.

## Big picture

```
PCAP or CSV or Zeek logs
        |
        v
Ingest and Clean
  - Remove hidden clues like raw IPs
  - Extract flags, bytes, timing, TTL, scan hints
        |
        v
Time Windows (60 seconds each)
  - Each window is a snapshot of the network
        |
        v
Graph Building
  - Hosts become nodes
  - Flows become edges with attributes
        |
        v
World Model Twin
  - Learns what normal next snapshot looks like
  - Compares real next snapshot to predicted
  - Drift means risk
        |
        v
Forecast and Check
  - Roll out 10 steps ahead with confidence range
  - Check if path makes sense with MITRE rules
        |
        v
Explain and Show
  - Top flows, stage, codebook path, technique link
  - Dashboard and API
```

## Layer 1: Ingest

Two paths:

* Flow path for CSV and NetFlow. Uses polars and custom cleaning. Removes leakage fields like src_ip. Fixes inf and missing values.
* Packet path for PCAP. Uses Scapy or dpkt. Extracts TTL variance, window size, flags, payload size, scan score.

Both paths produce the same window format so the model sees one view.

## Layer 2: Graph Twin

* Encoder: Takes a graph snapshot and makes a vector z of size 128. Simple mean pool now, will become Temporal Graph Network later.
* Codebook: 64 discrete prototypes. Each prototype is a regime like normal, scan, or beacons. The model snaps z to the closest prototypes. This keeps training stable and makes the model explainable.
* Predictor: Three predictors for 10s, 60s, and 300s scales. Fast scan needs 10s. Slow data steal needs 300s. Each predicts next z at its scale.
* Training: Only on benign traffic. Loss is prediction error in latent space plus codebook losses. No attack labels are used here, so it can catch new attacks.

## Layer 3: Stage Head

Small MLP that maps z to one of 7 stages: Benign, Reconnaissance, InitialAccess, Discovery, LateralMovement, CommandAndControl, Exfiltration. Trained separately on labeled data while encoder is frozen. This keeps stages from polluting the normal physics.

## Layer 4: Validator

A simple MITRE DAG that says which stage needs which prior stage. Example: Exfiltration needs CommandAndControl before it. If the model predicts Exfiltration without seeing C2, we lower the risk and flag it as not plausible. This cuts false alarms. It is a post check, not joint training, so it stays stable.

## Layer 5: Forecast

We roll the predictor 10 steps forward. We use an ensemble of 3 models and conformal calibration to draw a confidence cone. The cone shows uncertainty. We also compute counterfactual Hunt actions like pull auth logs for host X and show how risk would drop.

## Layer 6: Explain

For each window we build an evidence chain:

* window_id, risk, stage, confidence
* codebook path like 12 -> 37 -> 41
* top 5 flows with contribution scores
* MITRE technique and link
* causal path sentence
* plausibility score

This goes to the API and UI.

## Layer 7: Serve

* FastAPI for machine use. Endpoints: health, mitre lookup, infer, feedback.
* Streamlit for human use. Four pages: Upload, Graph, Risk Timeline, Evidence.
* Both run offline. No external fetch at runtime. Docker image bundles all deps.

## Data flow example

1. You upload sample.pcap (100 MB)
2. ingest parses it into flows.parquet (45 cleaned features)
3. windowing makes 20 windows, each with a graph
4. encoder makes 20 z vectors
5. predictor forecasts window 21 to 30
6. If window 21 is really attack, drift is high, risk 0.72, stage LateralMovement, evidence shows 3 SMB flows
7. UI shows graph with edge 10.0.0.5 -> 10.0.0.10 on port 445 highlighted

## Why this design

* Graph shows lateral movement clearly
* Benign only training avoids dataset bias
* Codebook gives discrete steps that match human stages
* Validator catches impossible predictions
* Counterfactual Hunt is safe, block is not
* Offline first keeps data private
