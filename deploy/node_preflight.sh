#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
printf 'Paula dual-host preflight\n'
for cmd in bash python3 curl; do command -v "$cmd" >/dev/null && echo "[ok] $cmd" || echo "[missing] $cmd"; done
if command -v docker >/dev/null 2>&1; then sudo docker compose version || true; else echo '[missing] docker'; fi
if [[ -f .env.paula ]]; then echo '[ok] private env file exists'; else echo '[action] create .env.paula from example'; fi
# A responding port is NOT proof that the private server is protected.
# A local-auth demo would incorrectly answer 200, so reject it before routing any tunnel.
code="$(curl --noproxy '*' --silent --max-time 5 --output /dev/null --write-out '%{http_code}' http://127.0.0.1:8768/api/health 2>/dev/null || true)"
case "$code" in
  401|503) echo "[ok] anonymous request refused with HTTP $code (fail-closed)" ;;
  000|'') echo '[info] no local server on 127.0.0.1:8768 yet' ;;
  200) echo '[unsafe] anonymous request succeeded (HTTP 200). STOP: check PAULA_AUTH_MODE before attaching a tunnel!' >&2; exit 1 ;;
  *) echo "[warning] unexpected anonymous HTTP status: $code. Check before attaching a tunnel." >&2; exit 1 ;;
esac
if [[ -d paula-private-data ]]; then echo '[ok] separate node data present'; else echo '[info] private media directory not created'; fi
echo 'No credentials are displayed. No claims about internet deployment.'
