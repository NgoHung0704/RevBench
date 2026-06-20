#!/usr/bin/env bash
# RevBench host bootstrap: build the DuckDB store, then bring up the prod stack.
#
# Raw data is never committed (CLAUDE.md hard rule #5), so a fresh host has no
# data/revbench.duckdb. This builds it once inside the image (the `scheduler`
# service has the read-write data mount), then starts the read-only stack.
#
# Usage (from the repo root on the host):
#   cp .env.example .env && edit .env   # set DEEPSEEK_API_KEY, EDGAR_USER_AGENT
#   bash scripts/bootstrap.sh           # full pipeline (data + agents + fusion)
#   bash scripts/bootstrap.sh --no-agents   # data + ML fusion only (no LLM key)
set -euo pipefail

cd "$(dirname "$0")/.."
COMPOSE="docker compose -f docker-compose.prod.yml"

if [[ ! -f .env ]]; then
  echo "ERROR: .env not found. Copy .env.example to .env and fill in keys first." >&2
  exit 1
fi

NO_AGENTS="${1:-}"
if [[ -z "${NO_AGENTS}" ]] && ! grep -q '^DEEPSEEK_API_KEY=.\+' .env; then
  echo "WARNING: DEEPSEEK_API_KEY is empty in .env -> falling back to --no-agents (ML-only)." >&2
  NO_AGENTS="--no-agents"
fi

echo "==> Building images"
$COMPOSE build

echo "==> Backfilling prices (5y x universe)"
$COMPOSE run --rm scheduler python -m data_pipeline.fetch --all --years 5

echo "==> Running the pipeline once to populate recommendations ${NO_AGENTS}"
$COMPOSE run --rm scheduler python -m data_pipeline.scheduler --once ${NO_AGENTS}

echo "==> Starting the read-only stack (API + web + reverse proxy)"
$COMPOSE up -d

echo
echo "Done. Web app on http://<server-ip> (Caddy on :80; set a domain in ./Caddyfile for HTTPS)."
echo "To accumulate nightly history (R1/R2):  $COMPOSE --profile scheduler up -d"
