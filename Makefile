.PHONY: install test lint format run-api run-ui docker clean

PY = python
PIP = pip

install:
	$(PIP) install -e ".[dev,ml,pcap,explain]"

install-min:
	$(PIP) install -e ".[dev]"

test:
	pytest -v

lint:
	ruff check ghostforge tests
	black --check ghostforge tests
	mypy ghostforge

format:
	ruff check --fix ghostforge tests
	black ghostforge tests

run-api:
	uvicorn ghostforge.serve.api:app --reload --host 0.0.0.0 --port 8000

run-ui:
	streamlit run ghostforge/serve/app.py --server.port 8501 --server.address 0.0.0.0

docker:
	docker build -t ghostforge:latest .

docker-run:
	docker run --rm -p 8000:8000 -p 8501:8501 ghostforge:latest

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage
	rm -rf dist build *.egg-info

data-dirs:
	mkdir -p data/raw data/processed data/synthetic models benchmarks

help:
	@echo "Targets:"
	@echo "  install      Install all deps"
	@echo "  install-min  Install minimal dev deps"
	@echo "  test         Run tests"
	@echo "  lint         Lint and type check"
	@echo "  format       Auto format code"
	@echo "  run-api      Run FastAPI service"
	@echo "  run-ui       Run Streamlit dashboard"
	@echo "  docker       Build Docker image"
	@echo "  clean        Clean caches"
