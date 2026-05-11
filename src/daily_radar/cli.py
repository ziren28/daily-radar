from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from daily_radar.config import load_config
from daily_radar.fetchers.google_news import fetch_google_news
from daily_radar.fetchers.rss import fetch_rss
from daily_radar.fetchers.stooq import fetch_stocks
from daily_radar.notifiers.weixin import read_weixin_token, send_weixin_message
from daily_radar.pipeline.dedupe import dedupe_items
from daily_radar.pipeline.render import render_markdown_report, render_weixin_digest
from daily_radar.pipeline.score import score_items, select_top_by_category
from daily_radar.storage.sqlite import RadarStore


def collect_items(cfg: dict):
    items = []
    items.extend(fetch_rss(cfg))
    items.extend(fetch_google_news(cfg))
    items.extend(fetch_stocks(cfg))
    return items


def report_date(cfg: dict) -> str:
    tz = ZoneInfo(cfg.get("settings", {}).get("timezone", "Asia/Shanghai"))
    return datetime.now(tz).date().isoformat()


def run_pipeline(args) -> int:
    cfg = load_config(args.config)
    db_path = Path(args.db or "data/radar.sqlite")
    store = RadarStore(db_path)
    store.init()
    items = collect_items(cfg)
    items = dedupe_items(score_items(items, cfg))
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
    sent = False
    if args.send:
        token = args.weixin_token or read_weixin_token(args.weixin_env)
        url = args.weixin_url or cfg.get("settings", {}).get("weixin_webhook_url", "http://127.0.0.1:18787/send")
        if not token:
            raise SystemExit("WEIXIN_WEBHOOK_TOKEN not found")
        send_weixin_message(url, token, digest)
        sent = True
    store.save_report(date, markdown, sent=sent)
    print(f"items={len(items)} report={report_path} sent={sent}")
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
    args = p.parse_args(argv)
    if args.cmd in (None, "run"):
        return run_pipeline(args)
    p.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
