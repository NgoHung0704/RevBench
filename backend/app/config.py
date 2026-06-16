"""Backend config — read-only over the precomputed DuckDB store (batch-first)."""

import os

from data_pipeline.store import DEFAULT_DB_PATH


def db_path() -> str:
    return os.environ.get("REVBENCH_DB", str(DEFAULT_DB_PATH))


# CORS origins for the Next.js dev server.
ALLOWED_ORIGINS = os.environ.get(
    "REVBENCH_CORS", "http://localhost:3000,http://127.0.0.1:3000"
).split(",")
