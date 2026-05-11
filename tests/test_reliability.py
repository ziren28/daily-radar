from daily_radar.models import RadarItem
from daily_radar.notifiers.weixin import chunk_text, send_weixin_message
from daily_radar.pipeline.reliability import filter_fresh_items, normalize_title_signature
from daily_radar.storage.sqlite import RadarStore


def test_filter_fresh_items_keeps_always_and_dedupes_by_title_signature(tmp_path):
    store = RadarStore(tmp_path / "radar.sqlite")
    store.init()
    seen_id = RadarItem(source="x", category="news", title="Already seen story", url="https://a")
    store.upsert_items([seen_id])

    items = [
        RadarItem(source="x", category="news", title="Already seen story", url="https://a"),
        RadarItem(source="x", category="news", title="OpenAI releases GPT-6", url="https://b"),
        RadarItem(source="y", category="news", title="OpenAI releases GPT 6!!!", url="https://c"),
        RadarItem(source="stock", category="google", title="GOOG $100 ↑1%", url="", raw={"always": True}),
    ]

    fresh = filter_fresh_items(items, store)

    assert [x.title for x in fresh] == ["OpenAI releases GPT-6", "GOOG $100 ↑1%"]
    assert normalize_title_signature("🚀 Musk: Hello, World!!!") == "helloworld"


def test_send_weixin_message_splits_long_text_and_retries(monkeypatch):
    calls = []

    class Resp:
        def __init__(self, ok=True):
            self.ok = ok
            self.status_code = 200 if ok else 500
            self.text = '{"ok":true}' if ok else 'bad'
        def raise_for_status(self):
            if not self.ok:
                raise RuntimeError("server error")
        def json(self):
            return {"ok": True}

    def fake_post(url, headers, json, timeout):
        calls.append(json["text"])
        if len(calls) == 1:
            return Resp(False)
        return Resp(True)

    monkeypatch.setattr("daily_radar.notifiers.weixin.httpx.post", fake_post)
    result = send_weixin_message("http://w/send", "tok", "x" * 1700, chunk_size=1000, retries=2)

    assert result["ok"] is True
    assert result["chunks"] == 2
    assert len(calls) == 3  # first chunk failed once then retried; second once
    assert all(len(c) <= 1000 for c in calls)


def test_chunk_text_preserves_short_text():
    assert chunk_text("abc", 10) == ["abc"]
    assert chunk_text("abcdef", 3) == ["abc", "def"]
