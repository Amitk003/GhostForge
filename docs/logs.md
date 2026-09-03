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

## How to add a new log

Edit this file, add a new date section at the bottom, commit with message like `docs: update logs for 2026-09-04`.

Keep language simple. List commands exactly as run.
