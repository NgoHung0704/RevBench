# RevBench API image. Build from the repo root:
#   docker build -f backend/Dockerfile -t revbench-api .
FROM python:3.12-slim

WORKDIR /app

# Runtime system libs: lightgbm's native lib needs libgomp (OpenMP), which the
# slim image omits — without it `import lightgbm` fails with
# "libgomp.so.1: cannot open shared object file".
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy only what the package needs (see .dockerignore for exclusions).
COPY pyproject.toml ./
COPY data_pipeline ./data_pipeline
COPY ml ./ml
COPY agents ./agents
COPY ui ./ui
COPY backend ./backend

# Install the package + API extra. (Heavy ML deps come along via the core
# dependencies; trimming them is a future image-size optimization.)
RUN pip install --no-cache-dir ".[api]"

ENV REVBENCH_DB=/data/revbench.duckdb
EXPOSE 8000

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
