# RevBench API image. Build from the repo root:
#   docker build -f backend/Dockerfile -t revbench-api .
FROM python:3.12-slim

WORKDIR /app

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
