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

* feature/twin-core has 8 commits, ready to push, waiting for codex review

Next:

* Forecast validator and explain branches

## How to add a new log

Edit this file, add a new date section at the bottom, commit with message like `docs: update logs for 2026-09-04`.

Keep language simple. List commands exactly as run.
