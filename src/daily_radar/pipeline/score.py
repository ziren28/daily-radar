from __future__ import annotations

from collections import defaultdict

from daily_radar.models import RadarItem

HIGH_VALUE_TERMS = {
    "earnings": 3,
    "财报": 3,
    "jumps": 2,
    "surges": 2,
    "plunges": 2,
    "antitrust": 3,
    "反垄断": 3,
    "openai": 2,
    "google": 2,
    "alphabet": 3,
    "goog": 3,
    "googl": 3,
    "gemini": 2,
    "免费": 3,
    "限免": 3,
    "优惠": 2,
    "coupon": 2,
    "credit": 2,
}


def classify_item(item: RadarItem, cfg: dict) -> str:
    text = f"{item.title} {item.summary}".lower()
    best_category = item.category or "tech"
    best_score = 0
    for category, meta in (cfg.get("categories") or {}).items():
        score = 0
        for kw in meta.get("keywords", []):
            if str(kw).lower() in text:
                score += 1
        if score > best_score:
            best_category = category
            best_score = score
    return best_category


def score_item(item: RadarItem, cfg: dict) -> RadarItem:
    category = classify_item(item, cfg)
    text = f"{item.title} {item.summary}".lower()
    score = 1.0
    for kw in (cfg.get("categories", {}).get(category, {}).get("keywords", [])):
        if str(kw).lower() in text:
            score += 1.5
    for term, weight in HIGH_VALUE_TERMS.items():
        if term in text:
            score += weight
    item.category = category
    item.score = round(score, 2)
    return item


def score_items(items: list[RadarItem], cfg: dict) -> list[RadarItem]:
    return [score_item(item, cfg) for item in items]


def select_top_by_category(items: list[RadarItem], per_category: int = 6) -> dict[str, list[RadarItem]]:
    grouped: dict[str, list[RadarItem]] = defaultdict(list)
    for item in sorted(items, key=lambda x: x.score, reverse=True):
        bucket = grouped[item.category]
        if len(bucket) < per_category:
            bucket.append(item)
    return dict(grouped)
