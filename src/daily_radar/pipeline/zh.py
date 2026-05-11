from __future__ import annotations

import re

from daily_radar.models import RadarItem

PHRASE_MAP = {
    "Alphabet": "Alphabet/谷歌母公司",
    "Google": "Google/谷歌",
    "GOOG": "GOOG/谷歌股票",
    "GOOGL": "GOOGL/谷歌股票",
    "earnings": "财报",
    "Fed": "美联储",
    "rate cut": "降息",
    "stock market": "股市",
    "Nasdaq": "纳斯达克",
    "S&P 500": "标普500",
    "Dow": "道指",
    "OpenAI": "OpenAI",
    "Anthropic": "Anthropic",
    "Claude": "Claude",
    "Gemini": "Gemini",
    "Hugging Face": "Hugging Face",
    "Elon Musk": "马斯克",
    "Musk": "马斯克",
    "Tesla": "特斯拉",
    "SpaceX": "SpaceX",
    "Trump": "特朗普",
    "Donald Trump": "特朗普",
    "Cathie Wood": "木头姐 Cathie Wood",
    "ARK Invest": "ARK Invest/方舟投资",
    "AI": "AI/人工智能",
    "launches": "发布",
    "says": "表示",
    "jumps": "上涨",
    "surges": "大涨",
    "falls": "下跌",
    "plunges": "大跌",
    "after": "因/在...之后",
    "hopes": "预期",
    "update": "更新",
}


def localize_title(title: str) -> str:
    """Local dictionary Chinese enrichment without calling any translation API."""
    result = title
    for eng, zh in sorted(PHRASE_MAP.items(), key=lambda x: len(x[0]), reverse=True):
        result = re.sub(rf"\b{re.escape(eng)}\b", zh, result, flags=re.IGNORECASE)
    return result


def localize_item(item: RadarItem) -> RadarItem:
    original = item.title
    localized = localize_title(original)
    if localized != original:
        item.raw = dict(item.raw or {})
        item.raw.setdefault("original_title", original)
        item.title = localized
    return item


def localize_items(items: list[RadarItem]) -> list[RadarItem]:
    return [localize_item(item) for item in items]
