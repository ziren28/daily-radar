from __future__ import annotations

import argparse
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from daily_radar.config import load_config
from daily_radar.fetchers.google_news import fetch_google_news
from daily_radar.fetchers.rss import fetch_rss
from daily_radar.fetchers.social import fetch_social_items
from daily_radar.fetchers.stooq import fetch_stocks
from daily_radar.fetchers.tencent_stock import fetch_tencent_stock_item
from daily_radar.notifiers.weixin import read_weixin_token, send_weixin_message
from daily_radar.pipeline.dedupe import dedupe_items
from daily_radar.pipeline.render import render_markdown_report, render_weixin_digest
from daily_radar.pipeline.reliability import filter_fresh_items
from daily_radar.pipeline.score import score_items, select_top_by_category
from daily_radar.pipeline.translate import translate_items
from daily_radar.storage.sqlite import RadarStore


def _translate_enabled(cfg: dict) -> bool:
    return bool(cfg.get("settings", {}).get("translate_enabled", True))


def collect_items(cfg: dict):
    items = []
    items.extend(fetch_social_items(cfg))
    items.extend(fetch_rss(cfg))
    items.extend(fetch_google_news(cfg))
    items.extend(fetch_stocks(cfg))
    items.append(fetch_tencent_stock_item(cfg))
    return translate_items(items, enabled=_translate_enabled(cfg))


def collect_social_items(cfg: dict):
    return translate_items(fetch_social_items(cfg), enabled=_translate_enabled(cfg))


def report_date(cfg: dict) -> str:
    tz = ZoneInfo(cfg.get("settings", {}).get("timezone", "Asia/Shanghai"))
    return datetime.now(tz).date().isoformat()


def _send_if_needed(args, cfg: dict, text: str) -> bool:
    if not args.send:
        return False
    token = args.weixin_token or read_weixin_token(args.weixin_env)
    url = args.weixin_url or cfg.get("settings", {}).get("weixin_webhook_url", "http://127.0.0.1:18787/send")
    if not token:
        raise SystemExit("WEIXIN_WEBHOOK_TOKEN not found")
    send_weixin_message(url, token, text)
    return True


def run_pipeline(args) -> int:
    cfg = load_config(args.config)
    db_path = Path(args.db or "data/radar.sqlite")
    store = RadarStore(db_path)
    store.init()
    seen_hours = int(cfg.get("settings", {}).get("seen_ttl_hours", 24))
    items = filter_fresh_items(dedupe_items(score_items(collect_items(cfg), cfg)), store, seen_hours)
    store.upsert_items(items)
    per_cat = int(cfg.get("settings", {}).get("max_items_per_category", 6))
    grouped = select_top_by_category(items, per_cat)
    date = report_date(cfg)
    markdown = render_markdown_report(grouped, cfg, date)
    report_dir = Path(args.report_dir or "reports")
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"{date}.md"
    report_path.write_text(markdown, encoding="utf-8")
    digest = render_weixin_digest(grouped, cfg, date)
    sent = _send_if_needed(args, cfg, digest)
    if sent or not args.send:
        store.mark_seen_items(items)
    store.prune_seen_keys((datetime.now(ZoneInfo("UTC")) - timedelta(hours=seen_hours)).isoformat())
    store.save_report(date, markdown, sent=sent)
    print(f"items={len(items)} report={report_path} sent={sent}")
    return 0


def run_social_alert(args) -> int:
    cfg = load_config(args.config)
    db_path = Path(args.db or "data/radar.sqlite")
    store = RadarStore(db_path)
    store.init()
    seen_hours = int(cfg.get("settings", {}).get("social_seen_ttl_hours", 6))
    items = filter_fresh_items(dedupe_items(score_items(collect_social_items(cfg), cfg)), store, seen_hours)
    store.upsert_items(items)
    grouped = select_top_by_category(items, int(args.limit))
    date = report_date(cfg)
    digest = render_weixin_digest(grouped, cfg, date, max_chars=1800)
    sent = _send_if_needed(args, cfg, digest)
    if sent or not args.send:
        store.mark_seen_items(items)
    store.prune_seen_keys((datetime.now(ZoneInfo("UTC")) - timedelta(hours=seen_hours)).isoformat())
    print(f"social_items={len(items)} sent={sent}")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="daily-radar")
    sub = p.add_subparsers(dest="cmd")
    run = sub.add_parser("run", help="fetch, render and optionally send daily report")
    run.add_argument("--config", default="configs/sources.yaml")
    run.add_argument("--db", default="data/radar.sqlite")
    run.add_argument("--report-dir", default="reports")
    run.add_argument("--send", action="store_true")
    run.add_argument("--weixin-url", default="")
    run.add_argument("--weixin-token", default="")
    run.add_argument("--weixin-env", default="/etc/spot-lifecycle.env")
    alert = sub.add_parser("social-alert", help="fetch social watchlist and optionally send short alert")
    alert.add_argument("--config", default="configs/sources.yaml")
    alert.add_argument("--db", default="data/radar.sqlite")
    alert.add_argument("--send", action="store_true")
    alert.add_argument("--limit", default="3")
    alert.add_argument("--weixin-url", default="")
    alert.add_argument("--weixin-token", default="")
    alert.add_argument("--weixin-env", default="/etc/spot-lifecycle.env")
    args = p.parse_args(argv)
    if args.cmd in (None, "run"):
        return run_pipeline(args)
    if args.cmd == "social-alert":
        return run_social_alert(args)
    p.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
