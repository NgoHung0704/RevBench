"""Publish a read-only snapshot of the store for the API (docs/REVISIT.md R11).

DuckDB is single-writer *across processes*: while the nightly pipeline holds the
write lock, a reader cannot open the file at all —

    IOException: Could not set lock on file "...": Conflicting lock is held

— so pointing the API at the live store takes the whole site down for the
duration of every run (~30 min), not the "brief blip" originally assumed.

Instead the writer publishes an atomic snapshot when it finishes, and the API
reads only that snapshot. Reader and writer never touch the same file, so there
is no contention at any point. Serving the last *completed* run is also the
semantically correct thing for a batch-first system: the UI's "as of" stamp
always describes a consistent, finished pipeline run.

CLI (run it once on an existing deployment to create the first replica):

    python -m data_pipeline.publish
"""

from __future__ import annotations

import argparse
import logging
import os
import shutil
from pathlib import Path

import duckdb

from .store import DEFAULT_DB_PATH

logger = logging.getLogger("revbench.publish")

READ_SUFFIX = "-read"


def read_replica_path(db_path: str | Path) -> Path:
    """`data/revbench.duckdb` -> `data/revbench-read.duckdb`."""
    p = Path(db_path)
    return p.with_name(f"{p.stem}{READ_SUFFIX}{p.suffix}")


def publish_read_replica(db_path: str | Path = DEFAULT_DB_PATH) -> Path:
    """Atomically publish a snapshot of `db_path` for readers.

    Checkpoints first so the main file is self-contained (no pending WAL to copy),
    writes to a temp file in the same directory, then `os.replace`s it into place.
    The rename is atomic within a filesystem, so a reader either sees the whole
    old snapshot or the whole new one — never a half-copied file.
    """
    src = Path(db_path)
    if not src.exists():
        raise FileNotFoundError(f"no store to publish at {src}")

    # Fold the WAL into the main file so a plain copy is complete.
    con = duckdb.connect(str(src))
    try:
        con.execute("CHECKPOINT")
    finally:
        con.close()

    dst = read_replica_path(src)
    tmp = dst.with_name(f".{dst.name}.tmp")
    shutil.copy2(src, tmp)
    os.replace(tmp, dst)  # atomic within the same filesystem

    logger.info("published read replica: %s (%.1f MB)", dst, dst.stat().st_size / 1e6)
    return dst


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Publish the API's read-only snapshot.")
    parser.add_argument("--db", default=str(DEFAULT_DB_PATH), help="primary DuckDB path")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    publish_read_replica(args.db)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
