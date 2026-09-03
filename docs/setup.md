# Setup

This doc tells you how to install and run GhostForge step by step.

## What you need

* Python 3.11 or newer
* Git
* Docker if you want the container way (recommended)
* 8 GB RAM, 4 GB free disk
* Optional: GPU for training, but not required for inference

## Option 1: Docker (easiest)

```bash
git clone https://github.com/Amitk003/GhostForge.git
cd GhostForge
docker build -t ghostforge:latest .
docker run --rm -p 8000:8000 -p 8501:8501 -v $(pwd)/data:/app/data ghostforge:latest
```

Windows PowerShell:

```powershell
git clone https://github.com/Amitk003/GhostForge.git
Set-Location GhostForge
docker build -t ghostforge:latest .
docker run --rm -p 8000:8000 -p 8501:8501 -v ${PWD}/data:/app/data ghostforge:latest
```

Open browser:

* UI: http://localhost:8501
* API docs: http://localhost:8000/docs
* Health: http://localhost:8000/health

To stop, press Ctrl+C in the terminal.

## Option 2: Local Python

```bash
git clone https://github.com/Amitk003/GhostForge.git
cd GhostForge
python -m venv .venv
source .venv/bin/activate
# Windows: .venv\Scripts\Activate.ps1

pip install --upgrade pip
pip install -e ".[dev,ml,pcap,explain]"

# Check install
ghostforge version
pytest -q
```

If you only need minimal install for testing:

```bash
pip install -e ".[dev]"
pytest -q
```

## Run services locally

Two terminals:

Terminal 1 API:

```bash
make run-api
# or
uvicorn ghostforge.serve.api:app --reload --port 8000
```

Terminal 2 UI:

```bash
make run-ui
# or
streamlit run ghostforge/serve/app.py --server.port 8501
```

## Make commands

```bash
make install      # install all deps
make install-min  # minimal dev deps
make test         # run tests
make lint         # check code style
make format       # auto fix style
make docker       # build image
make clean        # remove caches
```

## Verify install

```bash
python -c "import ghostforge; print(ghostforge.__version__)"
ghostforge --help
curl http://localhost:8000/health
```

You should see `{"status":"ok","version":"0.1.0"}`.

## Common problems

* Port already in use: change port with `uvicorn ghostforge.serve.api:app --port 8001`
* Scapy not found: install with `pip install -e ".[pcap]"` or use CSV path instead of PCAP
* Torch not found: install with `pip install -e ".[ml]"` or run on CPU only for now
* Docker build fails on Windows: make sure Docker Desktop is running and try `docker build --no-cache -t ghostforge:latest .`

## Data folders

After setup, you will see:

```
data/raw        Put your PCAP or CSV here, not tracked by git
data/processed  Cleaned windows and graphs
data/synthetic  Generated attack chains
models          Saved weights
benchmarks      Results
```

These folders have `.gitkeep` so they exist even when empty. Your raw traffic is never committed.

## Next

Read `docs/usage.md` to learn how to ingest a file and run inference.
