# Logs

Daily notes of what was done. Simple and honest.

## How to use

Each day, add a new section with date, commands run, what was installed, what was changed, and result.

We keep two logs:

* `docs/logs.md` in git for shared history
* `memory/logs/` local only for detailed private notes, not pushed to GitHub

## Template

```
## YYYY-MM-DD

Commands:
- git checkout -b feature/name
- pip install torch

Installed:
- torch 2.2

Changed:
- added ghostforge/twin/encoder.py

Result:
- tests pass, 5 passed
```

## 2026-09-03

Commands:

* git init
* git remote add origin https://github.com/Amitk003/GhostForge.git
* git config user.name amitee, user.email amitkumar023410@gmail.com
* pip install -e ".[dev]" (planned, not yet run in this env)
* pytest -q (planned)

Installed:

* project scaffold with fastapi, streamlit, pydantic, typer, rich, polars, networkx

Changed:

* Created main with .gitignore, LICENSE, pyproject, Makefile, README, ROADMAP
* Created branch setup/project-scaffold with ghostforge package, ingest, twin, validator, explain, serve, configs, scripts, tests, Docker
* Merged scaffold to main via PR #1

Result:

* 12 commits on scaffold branch, all pushed, main is up to date
* Tests scaffolded, not yet run in this env due to missing deps

Next:

* Finish docs/guides branch with 7 docs files
* Create memory folder locally with idea, roadmap, memory.md, and detailed logs
* Start ingest pipeline branch with real parsing logic

## 2026-09-03 - Docs and Ingest

Commands:

* git checkout -b docs/guides, created 7 docs files, pushed to origin, PR #2 merged to main
* Created memory folder locally with idea.md, roadmap.md, memory.md, logs, not pushed via .gitignore
* git checkout -b feature/ingest from main
* Added ghostforge/ingest/utils.py, zeek_parser.py, argus_parser.py, improved flow_parser, windowing, graph_builder
* Added scripts/audit_datasets.py and tests/test_ingest_extended.py
* pip install polars networkx pydantic typer rich pyyaml torch, ran pytest, fixed inf handling and replace_strict

Installed:

* polars, networkx, torch, pydantic, typer, rich

Changed:

* Ingest now handles CIC CSV with leakage strip and derived features, Zeek conn.log with gzip, Argus biargus with label unify, windowing with timestamp parse and save, graph builder with dedup and stats
* All ingest tests now pass 12 passed, twin tests 6 passed

Result:

* feature/ingest branch has 12 commits, merged to main via PR #3

Next:

* Twin core multi scale JEPA improvements
* Validator and forecast engine

## 2026-09-03 - Twin Core

Commands:

* git checkout -b feature/twin-core from main
* Added ghostforge/twin/losses.py, dataset.py, trainer.py with EMA, rollout.py with ensemble, anomaly.py with SVDD center
* Updated twin __init__.py exports
* Added tests/test_twin_core.py with 6 tests
* pip install torch, pytest passed 6 tests

Installed:

* torch 2.2

Changed:

* Twin now has full training loop for benign only, checkpoint save, K step rollout with confidence cone, anomaly scorer

Result:

* feature/twin-core has 9 commits with merge fix, merged to main via PR #4

Next:

* Forecast validator and explain branches

## 2026-09-03 - Forecast Validator

Commands:

* git checkout -b feature/forecast-validator from main
* Added .gitignore fix for ROADMAP.md private, git rm --cached ROADMAP.md kept local
* Added ghostforge/validator/counterfactual.py with hunt actions and risk simulation
* Added ghostforge/validator/conformal.py for calibrated intervals
* Added ghostforge/twin/feedback.py for contestable store
* Added tests/test_validator.py with 5 tests, pytest passed

Installed:

* numpy for conformal

Changed:

* Validator now has hunt counterfactual safe actions, conformal intervals, feedback store for active learning

Result:

* feature/forecast-validator has 7 commits, merged to main via PR #5

Next:

* Explain and serve branches

## 2026-09-03 - Explain

Commands:

* git checkout -b feature/explain from main
* Added ghostforge/explain/attribution.py with baseline delta and top k
* Added ghostforge/explain/attention.py with edge softmax
* Enhanced ghostforge/explain/evidence.py with MITRE map, codebook path and markdown render
* Added tests/test_explain.py with 3 tests, pytest passed

Installed:

* torch for attention

Changed:

* Explain now has feature attribution, edge attention, and full evidence chain with MITRE links

Result:

* feature/explain has 6 commits, merged to main via PR #6

Next:

* Serve API and UI polish, then benchmarks and Docker

## 2026-09-03 - Serve

Commands:

* git checkout -b feature/serve from main
* Added ghostforge/serve/schemas.py with pydantic models
* Hardened ghostforge/serve/api.py with cors, validation, feedback store and sigma export
* Added ghostforge/serve/ui_components.py with risk badge and stage bar
* Polished ghostforge/serve/app.py with health check, hunt cards and export
* Added tests/test_serve.py with 9 tests, pytest passed

Installed:

* fastapi, httpx for TestClient

Changed:

* Serve now has typed schemas, validated API, and polished UI with hunt plan

Result:

* feature/serve has 6 commits, merged to main via PR #7

Next:

* Benchmarks and Docker

## 2026-09-03 - Bench

Commands:

* git checkout -b feature/bench from main
* Added benchmarks/metrics.py with precision, recall, f1, fpr, auroc and lead time
* Added benchmarks/report.py with json and markdown generator
* Added scripts/benchmark.py with dummy run and ablation notes
* Added .dockerignore, updated Dockerfile to copy benchmarks and tests and run pytest
* Added .github/workflows/ci.yml for test and bench
* Added tests/test_bench.py with 4 tests, pytest passed
* Fixed benchmarks package import and ignore generated reports

Installed:

* numpy already present, no new deps

Changed:

* Bench now has honest metrics, report generation, benchmark runner, CI and Docker polish

Result:

* feature/bench has 9 commits, ready to push, waiting for codex review

Next:

* Final polish and handover

## How to add a new log

Edit this file, add a new date section at the bottom, commit with message like `docs: update logs for 2026-09-04`.

Keep language simple. List commands exactly as run.
