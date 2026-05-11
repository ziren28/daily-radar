from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone

from daily_radar.models import RadarItem
from daily_radar.storage.sqlite import RadarStore

PREFIXES = (
    "🟢 NS: ", "🛠️ HL: ", "🐧 LD: ", "📱 微博: ", "❓ 知乎: ",
    "📺 B站: ", "🎬 豆瓣: ", "🌈 HG: ", "🐯 虎嗅: ", "🚀 36Kr: ",
    "💎 掘金: ", "🌐 ", "🚀 Musk: ", "🇺🇸 Trump: ", "🔥 ",
)


def normalize_title_signature(title: str) -> str:
    title = title or ""
    for prefix in PREFIXES:
        if title.startswith(prefix):
            title = title[len(prefix):]
            break
    title = re.sub(r"^\[[^\]]+\]\s*", "", title)
    keep = re.sub(r"[^\w\u4e00-\u9fff]+", "", title).lower()
    return keep[:48]


def _seen_cutoff(hours: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()


def filter_fresh_items(items: list[RadarItem], store: RadarStore, seen_ttl_hours: int = 24) -> list[RadarItem]:
    """Drop previously reported items and same-title cross-source duplicates.

    Items with raw["always"] are kept every run, like prices/market snapshots.
    """
    known = store.get_recent_seen_keys(_seen_cutoff(seen_ttl_hours))
    batch_sigs: set[str] = set()
    fresh: list[RadarItem] = []
    for item in items:
        if (item.raw or {}).get("always"):
            fresh.append(item)
            continue
        sig = normalize_title_signature(item.title)
        sig_key = f"sig:{sig}" if sig else ""
        if item.id in known or (sig_key and sig_key in known) or (sig and sig in batch_sigs):
            continue
        if sig:
            batch_sigs.add(sig)
            item.raw = dict(item.raw or {})
            item.raw["title_signature"] = sig
        fresh.append(item)
    return fresh
