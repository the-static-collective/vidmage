#!/usr/bin/env bash
# Run from inside a checked-out copy of the Vidmage Paula branch.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
[[ -f .env.paula ]] || { echo 'Missing .env.paula. Copy .env.paula.example, fill it privately, chmod 600 .env.paula' >&2; exit 2; }
chmod 600 .env.paula
# Parse expected keys safely, without sourcing an arbitrary .env as shell commands.
for key in PAULA_CF_TEAM_DOMAIN PAULA_CF_AUD PAULA_ALLOWED_EMAILS PAULA_NODE_LABEL PAULA_HOME_URL PAULA_AWS_URL; do
  grep -q "^${key}=" .env.paula || { echo "Missing $key in .env.paula" >&2; exit 2; }
done
if grep -Eq 'YOURTEAM|YOURDOMAIN|PASTE_APPLICATION|paula@example.com' .env.paula; then
  echo 'Replace the sample values in .env.paula before launch.' >&2; exit 2
fi
if ! command -v docker >/dev/null 2>&1; then echo 'Run deploy/install_docker_ubuntu.sh first.' >&2; exit 2; fi
sudo docker compose version >/dev/null || { echo 'Docker Compose plugin is required' >&2; exit 2; }
sudo install -d -m 0700 -o 10001 -g 10001 "$ROOT/paula-private-data"
sudo docker compose -f compose.paula.yaml up --build --detach
printf '\nPaula node container started. API listens on host 127.0.0.1:8768 only.\n'
printf 'Use Cloudflare Dashboard to connect this local port via a separate tunnel and Access application.\n'
printf 'Check: sudo docker compose -f compose.paula.yaml ps\n'
