from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import httpx

from daily_radar.models import RadarItem
from daily_radar.pipeline.zh import localize_item


class Translator(Protocol):
    def translate(self, text: str) -> str: ...


@dataclass(slots=True)
class GoogleFreeTranslator:
    target: str = "zh-CN"
    source: str = "auto"
    timeout: int = 12
    endpoint: str = "https://translate.googleapis.com/translate_a/single"

    def translate(self, text: str) -> str:
        text = (text or "").strip()
        if not text:
            return ""
        resp = httpx.get(
            self.endpoint,
            params={
                "client": "gtx",
                "sl": self.source,
                "tl": self.target,
                "dt": "t",
                "q": text,
            },
            headers={"User-Agent": "daily-radar/0.1"},
            timeout=self.timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        parts: list[str] = []
        for chunk in data[0]:
            if chunk and chunk[0]:
                parts.append(str(chunk[0]))
        return "".join(parts).strip()


def should_translate(text: str) -> bool:
    if not text:
        return False
    ascii_chars = sum(1 for ch in text if ord(ch) < 128 and ch.isalpha())
    cjk_chars = sum(1 for ch in text if "\u4e00" <= ch <= "\u9fff")
    return ascii_chars > 8 and cjk_chars < max(2, ascii_chars // 8)


def translate_item(item: RadarItem, translator: Translator | None = None, enabled: bool = True) -> RadarItem:
    if not enabled or not should_translate(item.title):
        return localize_item(item)
    translator = translator or GoogleFreeTranslator()
    original = item.title
    try:
        translated = translator.translate(original)
        if translated and translated != original:
            item.raw = dict(item.raw or {})
            item.raw.setdefault("original_title", original)
            item.raw["translation_provider"] = "google_free"
            item.title = translated
            return item
    except Exception as exc:
        item = localize_item(item)
        item.raw = dict(item.raw or {})
        item.raw.setdefault("original_title", original)
        item.raw["translation_provider"] = "local_fallback"
        item.raw["translation_error"] = str(exc)[:200]
        return item
    return localize_item(item)


def translate_items(items: list[RadarItem], translator: Translator | None = None, enabled: bool = True) -> list[RadarItem]:
    return [translate_item(item, translator=translator, enabled=enabled) for item in items]
