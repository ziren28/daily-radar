from daily_radar.models import RadarItem
from daily_radar.pipeline.zh import localize_item, localize_title
from daily_radar.fetchers.social import build_nitter_rss_urls, fetch_social_items


def test_localize_title_uses_local_dictionary_without_external_api():
    title = "Alphabet GOOG jumps after earnings and Fed rate cut hopes"

    result = localize_title(title)

    assert "Alphabet/谷歌母公司" in result
    assert "财报" in result
    assert "美联储" in result
    assert "API" not in result


def test_localize_item_adds_chinese_title_but_keeps_original():
    item = RadarItem(source="s", category="google", title="Elon Musk says Tesla AI update")

    result = localize_item(item)

    assert result.raw["original_title"] == "Elon Musk says Tesla AI update"
    assert "马斯克" in result.title
    assert "特斯拉" in result.title


def test_build_nitter_rss_urls_for_social_watchlist():
    cfg = {"social": {"nitter_instances": ["https://nitter.net"], "watchlist": [{"name": "Elon Musk", "handle": "elonmusk", "category": "social"}]}}

    urls = build_nitter_rss_urls(cfg)

    assert urls == [("social", "Elon Musk", "https://nitter.net/elonmusk/rss")]


def test_fetch_social_items_uses_rss_fetcher(monkeypatch):
    calls = []
    def fake_fetch(category, name, url):
        calls.append((category, name, url))
        return [RadarItem(source=name, category=category, title="post")]
    monkeypatch.setattr("daily_radar.fetchers.social.fetch_rss_source", fake_fetch)

    items = fetch_social_items({"social": {"nitter_instances": ["https://nitter.net"], "watchlist": [{"name": "Trump", "handle": "realDonaldTrump", "category": "politics"}]}})

    assert items[0].source == "Trump"
    assert calls[0][2] == "https://nitter.net/realDonaldTrump/rss"
