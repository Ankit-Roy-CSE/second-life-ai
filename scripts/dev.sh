#!/usr/bin/env bash
# =============================================================================
# dev.sh — Local stack helper for Amazon Second Life AI
# =============================================================================
# Usage:
#   ./scripts/dev.sh up       # build + start full stack
#   ./scripts/dev.sh up infra # start infra only (postgres, redis, minio)
#   ./scripts/dev.sh down     # stop all containers (keep volumes)
#   ./scripts/dev.sh reset    # stop + wipe all volumes (clean slate)
#   ./scripts/dev.sh logs     # tail all service logs
#   ./scripts/dev.sh ps       # show container status
# =============================================================================

set -euo pipefail

COMPOSE="docker compose"
INFRA_SERVICES="postgres redis minio minio-init"

cmd="${1:-help}"
shift || true

case "$cmd" in
  up)
    if [ "${1:-}" = "infra" ]; then
      echo "▶ Starting infra services..."
      $COMPOSE up --build -d $INFRA_SERVICES
    else
      # Ensure .env exists
      if [ ! -f .env ]; then
        echo "⚠ .env not found — copying .env.example"
        cp .env.example .env
      fi
      echo "▶ Starting full stack..."
      $COMPOSE up --build -d
    fi
    echo "✅ Stack is up. Waiting for healthchecks..."
    $COMPOSE ps
    ;;
  down)
    echo "▶ Stopping containers..."
    $COMPOSE down
    ;;
  reset)
    echo "⚠ Wiping all volumes (postgres data, minio data)..."
    $COMPOSE down -v
    echo "✅ Volumes wiped. Run './scripts/dev.sh up' to start fresh."
    ;;
  logs)
    $COMPOSE logs -f "${@}"
    ;;
  ps)
    $COMPOSE ps
    ;;
  *)
    echo "Usage: $0 {up [infra]|down|reset|logs [service]|ps}"
    exit 1
    ;;
esac
