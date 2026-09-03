FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md LICENSE ./
COPY ghostforge/ ghostforge/
COPY configs/ configs/
COPY scripts/ scripts/

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -e ".[dev]"

EXPOSE 8000 8501

CMD ["sh", "-c", "uvicorn ghostforge.serve.api:app --host 0.0.0.0 --port 8000 & streamlit run ghostforge/serve/app.py --server.port 8501 --server.address 0.0.0.0"]
