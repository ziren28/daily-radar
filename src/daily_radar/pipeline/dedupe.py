from __future__ import annotations

from rapidfuzz import fuzz

from daily_radar.models import RadarItem


def dedupe_items(items: list[RadarItem], title_threshold: int = 92) -> list[RadarItem]:
    result: list[RadarItem] = []
    seen_urls: set[str] = set()
    for item in items:
        url_key = item.url.strip().lower()
        if url_key and url_key in seen_urls:
            continue
        if any(fuzz.token_sort_ratio(item.title, existing.title) >= title_threshold for existing in result):
            continue
        result.append(item)
        if url_key:
            seen_urls.add(url_key)
    return result
