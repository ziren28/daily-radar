from __future__ import annotations

from daily_radar.fetchers.rss import fetch_rss_source
from daily_radar.models import RadarItem


def build_nitter_rss_urls(cfg: dict) -> list[tuple[str, str, str]]:
    social = cfg.get("social") or {}
    instances = social.get("nitter_instances") or ["https://nitter.net"]
    base = str(instances[0]).rstrip("/")
    urls: list[tuple[str, str, str]] = []
    for person in social.get("watchlist") or []:
        handle = str(person.get("handle", "")).lstrip("@")
        if not handle:
            continue
        category = person.get("category", "social")
        name = person.get("name", handle)
        urls.append((category, name, f"{base}/{handle}/rss"))
    return urls


def fetch_social_items(cfg: dict) -> list[RadarItem]:
    items: list[RadarItem] = []
    for category, name, url in build_nitter_rss_urls(cfg):
        try:
            fetched = fetch_rss_source(category, name, url)
            for item in fetched:
                item.raw = dict(item.raw or {})
                item.raw["social_watch"] = True
            items.extend(fetched)
        except Exception as exc:
            items.append(RadarItem(source=name, category=category, title=f"社交媒体抓取失败: {name} {exc}", score=-1))
    return items
