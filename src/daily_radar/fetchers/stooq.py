from __future__ import annotations

import csv
import io

import httpx

from daily_radar.models import RadarItem


def fetch_stooq_symbol(symbol: str, name: str) -> RadarItem | None:
    url = f"https://stooq.com/q/l/?s={symbol.lower()}&f=sd2t2ohlcv&h&e=csv"
    resp = httpx.get(url, timeout=15, headers={"User-Agent": "daily-radar/0.1"})
    resp.raise_for_status()
    rows = list(csv.DictReader(io.StringIO(resp.text)))
    if not rows:
        return None
    row = rows[0]
    close = row.get("Close") or "N/D"
    open_ = row.get("Open") or "N/D"
    pct = ""
    try:
        c = float(close)
        o = float(open_)
        if o:
            pct = f" ({(c - o) / o * 100:+.2f}%)"
    except Exception:
        pass
    title = f"{name} {symbol} close {close}{pct}"
    return RadarItem(source="Stooq", category="google" if "goog" in symbol.lower() else "us_stock", title=title, url=url, raw=row, score=5)


def fetch_stocks(cfg: dict) -> list[RadarItem]:
    items: list[RadarItem] = []
    for spec in cfg.get("stocks") or []:
        try:
            item = fetch_stooq_symbol(spec["symbol"], spec.get("name", spec["symbol"]))
            if item:
                items.append(item)
        except Exception as exc:
            items.append(RadarItem(source="Stooq", category="us_stock", title=f"股票抓取失败: {spec.get('symbol')} {exc}", score=-1))
    return items
