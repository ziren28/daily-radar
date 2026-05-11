from __future__ import annotations

from urllib.parse import quote_plus

from daily_radar.fetchers.rss import fetch_rss_source
from daily_radar.models import RadarItem


def google_news_rss_url(query: str, hl: str = "zh-CN", gl: str = "US", ceid: str = "US:zh-Hans") -> str:
    return f"https://news.google.com/rss/search?q={quote_plus(query)}&hl={hl}&gl={gl}&ceid={quote_plus(ceid)}"


def fetch_google_news(cfg: dict) -> list[RadarItem]:
    items: list[RadarItem] = []
    for category, queries in (cfg.get("google_news") or {}).items():
        for query in queries:
            url = google_news_rss_url(str(query))
            try:
                items.extend(fetch_rss_source(category, f"Google News: {query}", url))
            except Exception as exc:
                items.append(RadarItem(source="Google News", category=category, title=f"Google News 抓取失败: {query} {exc}", score=-1))
    return items
