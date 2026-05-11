from __future__ import annotations

import time
from pathlib import Path
from typing import Any

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


def chunk_text(text: str, chunk_size: int = 1500) -> list[str]:
    text = text or ""
    if len(text) <= chunk_size:
        return [text]
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0
    for line in text.splitlines(keepends=True):
        if len(line) > chunk_size:
            if current:
                chunks.append("".join(current))
                current, current_len = [], 0
            for i in range(0, len(line), chunk_size):
                chunks.append(line[i : i + chunk_size])
            continue
        if current_len + len(line) > chunk_size and current:
            chunks.append("".join(current))
            current, current_len = [], 0
        current.append(line)
        current_len += len(line)
    if current:
        chunks.append("".join(current))
    return chunks or [""]


def _post_once(url: str, token: str, text: str, timeout: int) -> dict[str, Any]:
    resp = httpx.post(
        url,
        headers={"Authorization": f"Bearer {token}"},
        json={"text": text},
        timeout=timeout,
    )
    resp.raise_for_status()
    try:
        return resp.json()
    except Exception:
        return {"ok": True, "status_code": resp.status_code}


def send_weixin_message(
    url: str,
    token: str,
    text: str,
    timeout: int = 15,
    chunk_size: int = 1500,
    retries: int = 3,
    retry_sleep: float = 1.0,
) -> dict[str, Any]:
    """Send Weixin message with WX-friendly chunking and retry.

    Mirrors claude_paipai's reliability trick: never send overlong payloads as one
    request, and retry transient webhook/network failures.
    """
    results = []
    chunks = chunk_text(text, chunk_size)
    for chunk in chunks:
        last_exc: Exception | None = None
        for attempt in range(1, retries + 1):
            try:
                results.append(_post_once(url, token, chunk, timeout))
                last_exc = None
                break
            except Exception as exc:
                last_exc = exc
                if attempt < retries:
                    time.sleep(retry_sleep * attempt)
        if last_exc:
            raise last_exc
    return {"ok": True, "chunks": len(chunks), "results": results}
