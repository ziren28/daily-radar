from __future__ import annotations

from pathlib import Path

import httpx


def read_weixin_token(env_path: str | Path = "/etc/spot-lifecycle.env") -> str:
    path = Path(env_path)
    if not path.exists():
        return ""
    for line in path.read_text(errors="ignore").splitlines():
        line = line.strip()
        if line.startswith("WEIXIN_WEBHOOK_TOKEN="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


def send_weixin_message(url: str, token: str, text: str, timeout: int = 12) -> dict:
    resp = httpx.post(
        url,
        headers={"Authorization": f"Bearer {token}"},
        json={"text": text},
        timeout=timeout,
    )
    resp.raise_for_status()
    return resp.json()
