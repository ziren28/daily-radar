from daily_radar.models import RadarItem
from daily_radar.pipeline.translate import GoogleFreeTranslator, translate_items


def test_google_free_translator_calls_public_endpoint(monkeypatch):
    calls = []

    class Resp:
        def raise_for_status(self):
            return None
        def json(self):
            return [[['你好世界', 'hello world', None, None]]]

    def fake_get(url, params, headers, timeout):
        calls.append({"url": url, "params": params, "headers": headers, "timeout": timeout})
        return Resp()

    monkeypatch.setattr("daily_radar.pipeline.translate.httpx.get", fake_get)
    tr = GoogleFreeTranslator()

    assert tr.translate("hello world") == "你好世界"
    assert calls[0]["url"] == "https://translate.googleapis.com/translate_a/single"
    assert calls[0]["params"]["client"] == "gtx"
    assert calls[0]["params"]["tl"] == "zh-CN"
    assert calls[0]["params"]["q"] == "hello world"


def test_translate_items_prefers_google_and_keeps_original(monkeypatch):
    class FakeTranslator:
        def translate(self, text):
            return "马斯克表示特斯拉 AI 更新"

    item = RadarItem(source="x", category="social", title="Elon Musk says Tesla AI update")
    result = translate_items([item], translator=FakeTranslator())

    assert result[0].title == "马斯克表示特斯拉 AI 更新"
    assert result[0].raw["original_title"] == "Elon Musk says Tesla AI update"
    assert result[0].raw["translation_provider"] == "google_free"


def test_translate_items_falls_back_to_local_dictionary_on_failure():
    class BrokenTranslator:
        def translate(self, text):
            raise RuntimeError("network down")

    item = RadarItem(source="x", category="google", title="Alphabet earnings after Fed rate cut hopes")
    result = translate_items([item], translator=BrokenTranslator())

    assert "Alphabet/谷歌母公司" in result[0].title
    assert result[0].raw["translation_provider"] == "local_fallback"
    assert "network down" in result[0].raw["translation_error"]
