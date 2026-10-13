#!/usr/bin/env bash
# Ubuntu 22.04 / 24.04 only; install Docker Engine + Compose plugin from Docker's HTTPS apt repo.
set -euo pipefail
if ! command -v apt-get >/dev/null 2>&1; then echo 'Ubuntu/Debian apt required' >&2; exit 1; fi
. /etc/os-release
if [[ "${ID:-}" != 'ubuntu' && "${ID:-}" != 'debian' ]]; then echo 'Unsupported host OS. Follow Docker documentation instead.' >&2; exit 1; fi
if command -v docker >/dev/null 2>&1 && sudo docker compose version >/dev/null 2>&1; then echo 'Docker and Compose already installed'; exit 0; fi
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL "https://download.docker.com/linux/${ID}/gpg" -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
printf 'deb [arch=%s signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/%s %s stable\n' "$(dpkg --print-architecture)" "$ID" "${VERSION_CODENAME}" | sudo tee /etc/apt/sources.list.d/docker.list >/dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo systemctl enable --now docker
sudo docker compose version
