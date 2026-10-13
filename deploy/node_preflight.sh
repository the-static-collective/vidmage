#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
printf 'Paula dual-host preflight\n'
for cmd in bash python3 curl; do command -v "$cmd" >/dev/null && echo "[ok] $cmd" || echo "[missing] $cmd"; done
if command -v docker >/dev/null 2>&1; then sudo docker compose version || true; else echo '[missing] docker'; fi
if [[ -f .env.paula ]]; then echo '[ok] private env file exists'; else echo '[action] create .env.paula from example'; fi
if sudo curl --silent --show-error --max-time 5 -o /dev/null http://127.0.0.1:8768/api/health; then
  echo '[ok] local HTTP reachable (401 or 503 is EXPECTED when unauthenticated)'
else
  echo '[info] app has not been started on localhost'
fi
if [[ -d paula-private-data ]]; then echo '[ok] separate node data present'; else echo '[info] private media directory not created'; fi
echo 'No credentials are displayed. No claims about internet deployment.'
