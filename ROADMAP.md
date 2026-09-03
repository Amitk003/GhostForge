# GhostForge — Phase Roadmap to Perfect
### AI Network Attack Forecasting via Multiscale Graph-JEPA World Twin

> **Vision:** Learn the *benign* physics of a network as a temporal graph world model. Infiltration = trajectory deviation. Forecast K-steps with calibrated uncertainty, map to MITRE ATT&CK via discrete regime codebook, validate with probabilistic logic, and let analysts contest every prediction. Offline, open-source, plug-into Zeek/Wazuh — not another SIEM island.
>
> **Core Insight (research-backed):** Supervised `P(infiltration|flow)` on CIC-IDS2018 memorizes artifacts (7.5% mislabeled, near-random cross-dataset on LycoS-IDS2017). Self-supervised `P(S_t+1|S_t)` on *benign-only* traffic generalizes to zero-day. TGN+DeepSVDD beats vanilla TGN; MTS-JEPA multi-resolution + soft codebook fixes collapse and decouples transient shocks (port scan) from slow drifts (exfiltration).
>
> **Win Metric:** `Lead Time @ 1% FPR` + `Alert Burden Reduction @ same recall` — not F1 on canned 80/20 split. SANS 2025: 73% cite false positives #1 challenge, 46-83% alerts are false positives, median 1000/day.

---

## Architecture at a Glance

```
[PCAP / CSV / Zeek logs / Argus bi-flows]
        |
        v
L1: DUAL INGESTION & STATE  ──>  G_t = (Hosts as nodes, Flows as timed edges) + X_t vector
    - LycoS-CICFlowMeter v3 | Argus | Zeek
    - Role embeddings (server/WS/OT-PLC) not raw IPs
    - 60s snapshots -> Parquet + windowed graphs
        |
        v
L2: GRAPH-JEPA WORLD TWIN  ──>  z_t (128-d latent) via TGN
    - Benign-only self-supervised, 3 resolutions (10s/60s/300s)
    - Soft codebook K=64 (regimes = latent ATT&CK archetypes)
    - Predictor P: z_t -> z_{t+1} ; anomaly = ||pred - actual||
        |
        v
L3: FORECAST + VALIDATOR   ──>  K=10 rollout (10 min) with conformal cone
    - Ensemble(3) + conformal prediction (calibrated uncertainty)
    - Probabilistic Logic Validator (LTN/KnowGraph): checks MITRE prerequisites
    - Hunt-action counterfactuals (not block-port)
        |
        v
L4: CONTESTABLE EXPLANATION ──>  Evidence Chain UI
    - Top 3-5 flows via attention + GNNExplainer
    - Codebook path: Benign(12) -> Recon(37) -> 42% Lateral shift
    - ATT&CK/CAPEC/CVE links + Correct/Wrong/Missing feedback
        |
        v
L5: INTERFACE & HOOKS       ──>  Offline Streamlit/FastAPI + Zeek/Wazuh plugin
    - docker run ghostforge --pcap X.pcap
    - STIX/Sigma export, no cloud
```

**Repo target layout (created progressively):**
```
GhostForge/
├── data/                  # raw/, processed/, lycoS/, synthetic/
├── ghostforge/
│   ├── ingest/            # pcap_parser, flow_meter, windowing, graph_builder
│   ├── twin/              # tgn_encoder, jepa_predictor, codebook, svdd_head
│   ├── validator/         # mitre_dag, ltn_rules, plausibility
│   ├── explain/           # attention, gnn_explainer, evidence_chain
│   └── serve/             # fastapi, streamlit, zeek_plugin
├── configs/               # yaml for each phase
├── scripts/               # train.py, evaluate.py, rollout.py
├── models/                # weights, codebook prototypes
├── benchmarks/            # baseline results, ablations
└── ROADMAP.md             # this file
```

---

## Phase 0 — Discovery & Foundation (Weeks 1-2) — DO NOT TRAIN YET

**Goal:** Prove *suffering* is real and pick wedge. Failure to do this = build a paper nobody uses.

### Tasks
- [ ] **0.1 Suffering Doc (1 page):** Interview 5 SOC analysts / OT engineers / MSSP. Questions:
  - Tool sprawl count? Alerts/day? FPR? Time spent on false positives?
  - What would make them trust a `risk cone`? What exporter do they actually use (Zeek vs NetFlow vs Suricata)?
  - OT vs IT: Which network is more painfully noisy vs predictably stable?
- [ ] **0.2 Wedge Decision:** Default = **OT/ICS Critical Infrastructure** (deterministic traffic, world model shines, aligns with NCIIPC CII) with secondary `Enterprise IT` validation. Document why.
- [ ] **0.3 Dataset Audit Script:** `scripts/audit_datasets.py` that reproduces known issues:
  - Load CIC-IDS2018 raw CSVs -> check duplicated features, flow direction errors, IP/port leakage
  - Compare LycoS-Unicas-IDS2018 corrected vs original -> report 7.5% label flip
  - CTU-13: parse `detailed-bidirectional-flow-labels` -> class imbalance table (benign 80%+), mixed types
- [ ] **0.4 Environment:** `pyproject.toml` / `requirements.txt`, `Python 3.11`, `PyTorch 2.4 + PyG 2.6`, `Polars`, `DuckDB`, `Zeek` Docker, single GPU check (RTX 4080+). `make env` works offline.
- [ ] **0.5 Baseline Repo Skeleton:** Create `ghostforge/` layout above, `configs/base.yaml`, CI `pytest` placeholder.

### Deliverables
- `docs/suffering.md`, `docs/dataset_audit_report.md`, `configs/base.yaml`, working `pip install -e .`
- Go/No-Go: If no analyst confirms `>500 alerts/day & FPR >30%`, pivot wedge — do not proceed to modeling.

### Exit Criteria
- [ ] Audit report shows you can strip IPs/ports/timestamps and still train.
- [ ] At least 2 contacts willing to test a Zeek log triage plugin in Phase 4.

---

## Phase 1 — Ingestion & Benign Twin MVP (Weeks 3-6)

**Goal:** Rock-solid data pipeline + dumb-but-honest baselines + first world model that learns *normal* physics. Most teams fail here; you win here.

### Tasks
- [ ] **1.1 Flow Pipeline:**
  - `ghostforge/ingest/cicflowmeter.py` wrapper for LycoS-CICFlowMeter-v3 (fixes direction/duplication)
  - `ghostforge/ingest/argus.py` for CTU-13 `*.biargus`
  - `ghostforge/ingest/zeek.py` for `conn.log` (production path)
  - Output: `data/processed/flows.parquet` with 78 raw features -> 45 cleaned (drop redundant/Collinear >0.95, drop IP/port raw, hash role)
  - Features per spec: flags, bytes/packets, duration, IAT mean/var/max, bidir ratios, TTL var, win size, frag flags, payload dist, scan signatures, retransmits
- [ ] **1.2 Windowing & State:**
  - `ghostforge/ingest/windowing.py`: 60s tumbling windows, stride 30s
  - `S_t = { X_t: [N_hosts * d], G_t: edge_list with attrs, stats }`
  - Host role inference heuristic: `port 445/22/502 frequency -> server/OT`
  - Persist: `data/processed/snapshots/*.parquet` + `graphs/*.pt`
- [ ] **1.3 Graph Builder:**
  - `ghostforge/ingest/graph_builder.py`: `V=hosts, E=flows in window`, edge_attr normalized, temporal edge timestamps kept
  - Sanity viz: `notebooks/01_graph_viz.ipynb` playback of one Infiltration day vs benign day
- [ ] **1.4 Synthetic Augmentation (fixes <0.001% rare attacks):**
  - Atomic Red Team + Caldera replay: generate 200 synthetic chains for XSS, SQLi, Infiltration with MITRE stage labels
  - Store in `data/synthetic/` with same schema
- [ ] **1.5 Baselines (honest floor):**
  - `scripts/train_baseline.py`: Logistic Regression, XGBoost-Focal, vanilla LSTM (flat vector)
  - Train on CIC 80/20 *and* cross-dataset (train CIC, test CTU-13)
  - Report: Accuracy, Precision, Recall, F1, FPR, **Lead Time** (how many windows before attack label the model fires)
  - Expected failure: LSTM F1 0.99 in-dataset, ~0.55 cross-dataset — document it, don't hide
- [ ] **1.6 Benign-Only TGN-SVDD MVP:**
  - `ghostforge/twin/tgn_encoder.py`: TGN with memory (from `pyg_temporal` or custom)
  - `ghostforge/twin/svdd_head.py`: Deep SVDD hypersphere (TGN-SVDD paper replication)
  - Train **only on benign windows** (LycoS benign 80%). Loss: MSE next-embedding + SVDD radius
  - Anomaly score: `|| z_pred - z_actual || + dist_to_center`
  - Eval: `benign MSE << attack MSE` separation plot. If not, debug L1 before tuning model.

### Deliverables
- `data/processed/` reproducibly built via `make data` (documents AWS CLI `s3://cse-cic-ids2018` if needed)
- `benchmarks/baselines.json` + `benchmarks/tgn_svdd_mvp.json`
- `notebooks/02_twin_latent_drift.ipynb` showing deviation at attack onset

### Exit Criteria
- [ ] Pipeline ingests *any* PCAP without crash (fuzz 3 random PCAPs).
- [ ] Benign vs attack MSE distributions are separable (KS test p<0.01).
- [ ] Baseline Lead Time measured (e.g., LSTM 2.1 windows @ 10% FPR).

---

## Phase 2 — Multiscale Graph-JEPA Twin (Weeks 7-11)

**Goal:** Replace MSE with JEPA that sees both fast scan and slow exfiltration; make latent space interpretable.

### Tasks
- [ ] **2.1 Multi-Resolution JEPA:**
  - `ghostforge/twin/jepa_predictor.py`: 3 predictors (10s, 60s, 300s) sharing encoder, EMA target encoder
  - Soft codebook `K=64` (differentiable quantization, per MTS-JEPA Feb 2026): `z -> assignment p -> prototype`
  - Loss: `L_pred (latent) + L_ent_batch (prevent collapse) + L_ent_sample (sharpen) + L_commitment`
  - Theory: drift bounded by codebook radius M — gives stable anomaly score
- [ ] **2.2 Codebook-to-MITRE Alignment:**
  - After training, cluster prototypes: run k-NN of prototype centroids vs labeled attack windows -> map `prototype 37 ~ Reconnaissance`, `42 ~ C2`
  - `configs/codebook_map.yaml`: human-readable `12: Benign-Normal, 37: Recon-Scan, 41: Lateral-SMB...`
  - This is your *discrete regime* explainability, not post-hoc SHAP alone
- [ ] **2.3 Decoupled Stage Head:**
  - `ghostforge/twin/stage_head.py`: `MLP(z_t) -> 5 softmax (Recon, Initial Access, Lateral, C2, Exfiltration)` + `Benign`
  - Train only on labeled attack windows, frozen encoder. Separates dynamics (unsupervised) from annotation (supervised)
  - Calibrate with temperature scaling
- [ ] **2.4 Evaluation Protocol (honest):**
  - `scripts/evaluate_jepa.py`:
    - Held-out attack family: train without `Infiltration`, test on it (zero-day sim)
    - Cross-dataset: train CIC benign, test CTU-13 benign+botnet
    - Metrics: FPR@90% Recall, AUROC, F1, **Lead Time @1% FPR**, **FPR reduction vs LogReg at same recall**
  - Must beat baselines on cross-dataset, not just in-dataset
- [ ] **2.5 Explainability v1:**
  - Attention over edges (which flow pushed `z_t` off-manifold) + Captum Integrated Gradients on packet features
  - `ghostforge/explain/evidence_chain.py` draft

### Deliverables
- `models/jepa_multiscale.pt` + `models/codebook.pt`
- `benchmarks/jepa_multiscale.json`: target `>0.85 AUROC cross-dataset, Lead Time >=5 windows @1% FPR`
- `notebooks/03_codebook_regimes.ipynb` visualizing prototype trajectories

### Exit Criteria
- [ ] No representation collapse (codebook usage >50% of K, entropy > threshold).
- [ ] Held-out family recall >70% @5% FPR — proves generalization, not memorization.
- [ ] Stage head calibrated ECE <0.1

---

## Phase 3 — Validator, Forecasting & Contestability (Weeks 12-15)

**Goal:** Make forecasts trustworthy and actionable without causing outages.

### Tasks
- [ ] **3.1 Conformal Rollout:**
  - `ghostforge/twin/rollout.py`: autoregress `P` K=10 steps, ensemble(3) with different seeds, produce `risk timeline + 80/95% cone`
  - Conformal calibration on benign validation set -> guarantee `coverage 90%`
  - Output: `prob_infiltration timeline [0..1] + uncertainty`
- [ ] **3.2 Probabilistic Logic Validator (KnowGraph/LTN style):**
  - `ghostforge/validator/mitre_dag.yaml`: DAG from MITRE + CAPEC prerequisites
    ```yaml
    Exfiltration:
      requires: [CommandAndControl]
      evidence: [large_outbound_bytes, DNS_tunnel]
    LateralMovement:
      requires: [Discovery]
      evidence: [SMB_445, WinRM_5985]
    ```
  - `ghostforge/validator/ltn_validator.py`: soft logic, outputs `plausibility [0..1]`, dampens `prob *= plausibility`
  - Example: `P(Exfiltration|no prior C2) -> 0.2` + flag `implausible`
  - Start with 10 rules, expand to 30. Keep as post-hoc filter — never joint train
- [ ] **3.3 Hunt-Action Counterfactuals:**
  - `ghostforge/validator/counterfactual.py`: action space
    - `collect: {auth_logs host X, payload capture, DNS query}`
    - `deceive: {honeypot subnet Y}`
    - `rate_limit: {protocol}` (low-risk only)
  - Re-roll *assuming* evidence collected: `delta_prob = prob_before - prob_after`
  - UI shows: `If you pull auth logs on 10.0.0.12, Lateral prob 0.72 -> 0.41 (-43%)`
- [ ] **3.4 Triggered Active Learning (PACT-style):**
  - `ghostforge/twin/active_learner.py`: Pareto-aware controller wrapping frozen screener
  - Trigger: `uncertainty > tau OR analyst marks Wrong`
  - Stores `feedback.parquet` -> nightly fine-tune on contested windows only (controls burden)
- [ ] **3.5 Explainability v2 (shippable):**
  - `ghostforge/explain/`: `attention.py` + `gnn_explainer.py` -> `evidence_chain.json`
  - Each prediction: `{top_flows: [{src,dst,port,flags,contrib}], codebook_path: [12->37], mitre: T1021, cve: CVE-2020-1472, causal_path: "..."}`
  - Links to `attack.mitre.org` + `NVD`

### Deliverables
- `ghostforge/validator/` tested with `pytest` on synthetic ATT&CK chains (must catch impossible `Exfil before C2`)
- `benchmarks/validator_ablation.json`: `JEPA alone vs JEPA+Validator` (expect +5-10% precision, -FPR)
- `notebooks/04_rollout_cone.ipynb`

### Exit Criteria
- [ ] Rollout coverage 90% +/-3% on holdout.
- [ ] Validator reduces FPR by >=15% at same recall.
- [ ] Counterfactual UI renders delta in <200ms.

---

## Phase 4 — Offline Demo Hardening (Weeks 16-18) — THE DIFFERENTIATOR

**Goal:** A demo that *never* crashes on a random PCAP and runs fully offline. This is where experienced teams win judges.

### Tasks
- [ ] **4.1 FastAPI Service:**
  - `ghostforge/serve/api.py`: `POST /infer` (CSV/PCAP) -> `state + rollout + evidence` JSON, <2s for 60s window on CPU
  - `GET /health`, `GET /mitre/{technique}` (cached offline ATT&CK)
  - `ONNX` export for CPU inference
- [ ] **4.2 Streamlit App:**
  - `ghostforge/serve/app.py` 4 views:
    1. Upload + parsing progress (Scapy/Argus logs streaming)
    2. Graph playback (temporal slider, host nodes colored by risk)
    3. Risk cone timeline + stage annotations (Recon/Lateral/C2...)
    4. Evidence Chain + Hunt panel + feedback buttons (`Correct/Wrong`)
  - Must handle `0-10k flows/sec` without OOM (Polars streaming)
  - Branding: `GhostForge` dark theme, MITRE Navigator style stage bar
- [ ] **4.3 Offline Guarantee:**
  - `Dockerfile` with `python:3.11-slim` + `requirements.lock`, no `pip` at runtime, `ATT&CK json` bundled
  - `make docker` -> `docker run -p 8501:8501 ghostforge --pcap /data/test.pcap` works air-gapped
  - Test: disconnect WiFi, `pytest tests/test_offline.py` passes
- [ ] **4.4 Benchmark Dashboard:**
  - `benchmarks/dashboard.md` auto-generated: tables + plots `F1/Precision/Recall/FPR/Lead Time` vs baselines + ablations (`vector vs graph, single vs multiscale, with/without codebook, with/without validator`)
  - Include failure modes honestly
- [ ] **4.5 Fuzz & Robustness:**
  - `tests/test_ingest_fuzz.py`: 20 random PCAPs (CIC, CTU-13, synthetic, empty) — none crash, all produce JSON or graceful error
  - `tests/test_reproducibility.py`: `seed=42` -> same `codebook_map.yaml`

### Deliverables
- `Dockerfile`, `docker-compose.yml`, `ghostforge/serve/` fully working
- `benchmarks/dashboard.html` (static)
- `README.md` with `Quickstart: docker run ...` + 3-min Loom video

### Exit Criteria
- [ ] Non-technical tester can upload PCAP and see risk cone in <30s without help.
- [ ] Fuzz suite 100% pass.
- [ ] Offline test pass (air-gapped).

---

## Phase 5 — Real Pilot & Benchmark Publication (Weeks 19-24)

**Goal:** Prove value on *real* traffic, not just CIC. This turns a hackathon project into a product people use this week.

### Tasks
- [ ] **5.1 Pilot Recruitment:**
  - Target 1: University lab / home lab with Zeek (easy) or small enterprise / OT testbed (high value)
  - Offer: `We run shadow mode, no blocking, just triage enrichment. You keep data.`
  - Agreement: 1-week Zeek `conn.log` sharing (or on-prem run)
- [ ] **5.2 Shadow Deployment:**
  - Deploy `ghostforge` as Zeek log consumer: tails `conn.log` -> windows -> twin -> outputs `ghostforge_alerts.json` alongside existing SIEM
  - Measure: `alerts/day before vs after`, `analyst triage minutes`, `true positives caught` (validate with analyst)
  - Log contested predictions
- [ ] **5.3 Pilot Report:**
  - `docs/pilot_report.md`: `FPR reduction %, time saved, lead time on any true event, analyst quotes`
  - If no true events: `detection on synthetic Caldera attack injected into pilot traffic` (with permission)
- [ ] **5.4 Paper-Ready Benchmarks:**
  - Final `scripts/evaluate_final.py` reproduces all numbers from `benchmarks/` with one command
  - Release `models/*` + `configs/*` + `Training logs` for reproducibility
  - Write `docs/TECH_REPORT.md`: method, ablations, cross-dataset, pilot — honest about limits
- [ ] **5.5 Wazuh/Suricata Plugin:**
  - `ghostforge/serve/zeek_plugin/` + `wazuh_integration/` : `ghostforge -> Sigma rule suggestion`
  - Example: `title: GhostForge Lateral Movement | logsource: zeek | detection: ... | level: high`

### Deliverables
- `docs/pilot_report.md` + `docs/TECH_REPORT.md`
- `models/` public release
- At least 1 pilot reference (even if small)

### Exit Criteria
- [ ] Pilot shows `>=30% FPR reduction @ same recall` OR `>=5 min lead time on injected attack` — otherwise reposition as `triage assistant` not `forecasting`.

---

## Phase 6 — Perfect (Hardening to Production-Grade) (Weeks 25+)

**Goal:** Make it survive a SOC's worst day and adapt per-site without leaking data.

### Tasks
- [ ] **6.1 Per-Site Federated Adaptation:**
  - `ghostforge/twin/federated.py`: LoRA adapter per site, trained locally on benign traffic, no raw flows leave site. Global encoder frozen, site adapter learns local `normal` drift.
  - Addresses privacy + distribution shift (enterprise vs OT)
- [ ] **6.2 Streaming & Scale:**
  - `Polars` streaming + `DuckDB` windowing -> handle `100k flows/sec` (enterprise core)
  - `ghostforge/ingest/live_tail.py`: follow `zeek conn.log` with backpressure, checkpointed
- [ ] **6.3 Adversarial Robustness:**
  - Test evasions: slow scan, TTL spoof, flow splitting. `TGN-SVDD` anomaly is harder to evade than port-based rules, but measure.
  - `ghostforge/validator/adversarial_test.py`
- [ ] **6.4 Edge/Global Hooks:**
  - Lightweight `ONNX` edge model for OT gateway (Raspberry Pi / industrial PC)
  - Global `ATT&CK` auto-update: `scripts/update_mitre.py` pulls `mitre/cti` -> rebuilds `mitre_dag.yaml`
- [ ] **6.5 UX Polish:**
  - `GhostForge` CLI: `ghostforge ingest --pcap X --out Y`, `ghostforge train --config configs/jepa.yaml`, `ghostforge serve`
  - Telemetry (local only): `triaged/alerted/contested` counts for SOC manager dashboard
- [ ] **6.6 Community & Docs:**
  - `docs/ARCHITECTURE.md` (deep dive), `docs/DATASETS.md` (LycoS fix guide), `CONTRIBUTING.md`
  - Release `v1.0` with `CITATION.cff`, `LICENSE` (Apache-2.0)

### Deliverables
- `v1.0` tagged, `pip install ghostforge` works
- `benchmarks/scale_test.md` (100k flows/sec latency)
- 2nd pilot (OT) if possible

### Exit Criteria (Perfect)
- [ ] `make test` 90%+ coverage, `make bench` reproduces paper in <1h on single GPU
- [ ] Air-gapped Docker runs on fresh Ubuntu + on Windows (your `win32` env) without `bash` hacks
- [ ] Analyst can go `upload PCAP -> see risk cone -> export Sigma rule -> feed back Wrong -> retrain` end-to-end without docs.

---

## Cross-Cutting Checklists

### Evaluation (Every Phase)
- [ ] In-dataset vs Cross-dataset vs Held-out family — never report only 80/20 F1
- [ ] Always at `1% FPR` operating point for lead time
- [ ] Leak audit: `grep -r "192.168\|192.168.1" data/processed` must be 0 after stripping
- [ ] Seed 42 reproducibility

### Security & Privacy
- [ ] PCAPs never committed; `data/raw/` in `.gitignore`, `dvc` or `s3://cse-cic-ids2018` via AWS CLI
- [ ] No cloud calls; `webfetch` only at build time for MITRE JSON, bundled at runtime
- [ ] Pilot data stays on-prem; only `feedback.parquet` (contested windows) optionally shared

### Documentation (Never skip)
- [ ] `README.md` quickstart (3 commands)
- [ ] `configs/` yamls commented with paper refs (TGN-SVDD, MTS-JEPA, KnowGraph)
- [ ] `CHANGELOG.md` per phase

---

## Timeline Gantt (Dependency-Driven, No Hard Deadlines)

```
P0 [Discovery]      ████
P1 [Ingest+MVP]         ███████
P2 [Multiscale JEPA]          ███████
P3 [Validator]                      █████
P4 [Demo]                               ████
P5 [Pilot]                                  ███████
P6 [Perfect]                                      █████████
```

*Each phase gates next: do not start P2 if P1 benign MSE not separable.*

---

## How to Use This File

- `Ctrl+F` phase -> check boxes as you build. Each `[ ]` is a commit.
- `make phase1`, `make phase2` etc. targets to run that phase's tests (to be added).
- Brutal truth: If you tick all boxes through P4, you already beat 95% of competitors on engineering + honesty. P5-P6 is what makes people *use* it next week.

---

## References (Built-In)

- LycoS-Unicas-IDS2018 fix: Cantone et al. 2024, Sarhan et al. 2021
- TGN-SVDD: Liu et al. arXiv:2508.12885 (TGN encoder + SVDD, vanilla TGN insufficient)
- NID-TGN: SPACE 2024 (spatiotemporal IDS, 97% IoT)
- MTS-JEPA / SC-JEPA: He et al. Feb 2026 (multi-resolution JEPA + soft codebook, early-warning SOTA)
- KnowGraph: CCS 2024 (logic on graphs)
- SANS 2025 / MS/Omdia 2026: 73% FPR #1 challenge, 46-83% FP, 1000/day median

> **Next command:** `make env && make data` — start Phase 0. When P0 suffering doc is done, commit and tick boxes here. This file is the source of truth.
