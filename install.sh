#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR=${APP_DIR:-/opt/daily-radar}
install -d -m 0755 "$APP_DIR"
rsync -a --delete --exclude .git --exclude .venv "$ROOT/" "$APP_DIR/"
cd "$APP_DIR"
python3 -m venv .venv
. .venv/bin/activate
pip install -e '.[test]'
install -m 0644 systemd/*.service /etc/systemd/system/
install -m 0644 systemd/*.timer /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now daily-radar.timer
systemctl enable --now daily-radar-social-alert.timer
systemctl list-timers --all | grep daily-radar || true
