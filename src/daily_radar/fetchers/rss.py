from __future__ import annotations

from email.utils import parsedate_to_datetime

import feedparser

from daily_radar.models import RadarItem


def _published(entry) -> str:
    value = getattr(entry, "published", "") or getattr(entry, "updated", "")
    if not value:
        return ""
    try:
        return parsedate_to_datetime(value).isoformat()
    except Exception:
        return str(value)


def fetch_rss_source(category: str, name: str, url: str, timeout: int = 15) -> list[RadarItem]:
    parsed = feedparser.parse(url, request_headers={"User-Agent": "daily-radar/0.1"})
    items: list[RadarItem] = []
    for entry in parsed.entries[:30]:
        title = getattr(entry, "title", "").strip()
        if not title:
            continue
        items.append(
            RadarItem(
                source=name,
                category=category,
                title=title,
                url=getattr(entry, "link", ""),
                summary=(getattr(entry, "summary", "") or "")[:500],
                published_at=_published(entry),
                raw={"feed": url},
            )
        )
    return items


def fetch_rss(cfg: dict) -> list[RadarItem]:
    items: list[RadarItem] = []
    for category, sources in (cfg.get("rss") or {}).items():
        for src in sources:
            try:
                items.extend(fetch_rss_source(category, src["name"], src["url"]))
            except Exception as exc:
                items.append(RadarItem(source=src.get("name", "rss"), category=category, title=f"RSS 抓取失败: {exc}", score=-1))
    return items
