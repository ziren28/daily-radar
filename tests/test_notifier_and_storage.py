import json
import os
from pathlib import Path

from daily_radar.models import RadarItem
from daily_radar.notifiers.weixin import read_weixin_token, send_weixin_message
from daily_radar.storage.sqlite import RadarStore


def test_read_weixin_token_from_env_file(tmp_path):
    env = tmp_path / "spot.env"
    env.write_text("WEIXIN_WEBHOOK_TOKEN=abc123\nOTHER=x\n")

    assert read_weixin_token(env) == "abc123"


def test_send_weixin_message_posts_json(monkeypatch):
    calls = []

    class Resp:
        status_code = 200
        text = '{"ok":true}'
        def raise_for_status(self):
            return None
        def json(self):
            return {"ok": True}

    def fake_post(url, headers, json, timeout):
        calls.append({"url": url, "headers": headers, "json": json, "timeout": timeout})
        return Resp()

    monkeypatch.setattr("daily_radar.notifiers.weixin.httpx.post", fake_post)

    result = send_weixin_message("http://127.0.0.1:18787/send", "tok", "hello")

    assert result == {"ok": True}
    assert calls[0]["headers"]["Authorization"] == "Bearer tok"
    assert calls[0]["json"] == {"text": "hello"}


def test_radar_store_upserts_items_and_reports(tmp_path):
    db = tmp_path / "radar.sqlite"
    store = RadarStore(db)
    store.init()
    item = RadarItem(source="s", category="ai", title="Title", url="https://x", score=3)

    store.upsert_items([item])
    store.upsert_items([item])
    items = store.list_items(limit=10)
    report_id = store.save_report("2026-05-11", "# report", sent=False)
    reports = store.list_reports(limit=10)

    assert len(items) == 1
    assert items[0].title == "Title"
    assert report_id
    assert reports[0]["markdown"] == "# report"
