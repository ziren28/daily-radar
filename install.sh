#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR=${APP_DIR:-/opt/daily-radar}
install -d -m 0755 "$APP_DIR"
if command -v rsync >/dev/null 2>&1; then
  rsync -a --delete --exclude .git --exclude .venv "$ROOT/" "$APP_DIR/"
else
  find "$APP_DIR" -mindepth 1 -maxdepth 1 ! -name data ! -name reports -exec rm -rf {} +
  cp -a "$ROOT"/. "$APP_DIR"/
  rm -rf "$APP_DIR/.git" "$APP_DIR/.venv"
fi
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
