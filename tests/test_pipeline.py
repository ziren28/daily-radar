from daily_radar.models import RadarItem
from daily_radar.pipeline.dedupe import dedupe_items
from daily_radar.pipeline.score import classify_item, score_item, select_top_by_category
from daily_radar.pipeline.render import render_markdown_report, render_weixin_digest


def item(title, url="", source="test", category="tech"):
    return RadarItem(source=source, category=category, title=title, url=url, published_at="2026-05-11T08:00:00Z")


def test_dedupe_items_by_url_and_similar_title():
    items = [
        item("OpenAI releases new GPT model", "https://example.com/a"),
        item("OpenAI releases new GPT model", "https://example.com/a"),
        item("OpenAI release new GPT models", "https://example.com/b"),
        item("Tencent launches new game", "https://example.com/c"),
    ]

    result = dedupe_items(items)

    assert [x.title for x in result] == ["OpenAI releases new GPT model", "Tencent launches new game"]


def test_classify_and_score_google_stock_news():
    cfg = {
        "categories": {
            "ai": {"keywords": ["OpenAI", "LLM"]},
            "google": {"keywords": ["Google", "Alphabet", "GOOG", "GOOGL", "Gemini"]},
            "deals": {"keywords": ["免费", "优惠", "coupon"]},
        }
    }
    news = item("Alphabet GOOG jumps after Google Gemini earnings beat", category="tech")

    category = classify_item(news, cfg)
    scored = score_item(news, cfg)

    assert category == "google"
    assert scored.category == "google"
    assert scored.score >= 8


def test_select_top_by_category_limits_and_sorts():
    items = [
        RadarItem(source="s", category="ai", title="low", score=1),
        RadarItem(source="s", category="ai", title="high", score=9),
        RadarItem(source="s", category="ai", title="mid", score=5),
        RadarItem(source="s", category="deals", title="deal", score=7),
    ]

    result = select_top_by_category(items, per_category=2)

    assert [x.title for x in result["ai"]] == ["high", "mid"]
    assert [x.title for x in result["deals"]] == ["deal"]


def test_render_markdown_and_weixin_digest():
    grouped = {
        "ai": [RadarItem(source="OpenAI", category="ai", title="GPT update", url="https://openai.com", score=10, summary="重要模型更新")],
        "deals": [RadarItem(source="Deals", category="deals", title="AI tool free credits", url="https://deal.example", score=8)],
    }
    cfg = {"settings": {"report_title": "每日雷达"}, "categories": {"ai": {"title": "AI 动态"}, "deals": {"title": "福利羊毛"}}}

    md = render_markdown_report(grouped, cfg, report_date="2026-05-11")
    digest = render_weixin_digest(grouped, cfg, report_date="2026-05-11")

    assert "# 每日雷达 2026-05-11" in md
    assert "## AI 动态" in md
    assert "GPT update" in md
    assert "【每日雷达】2026-05-11" in digest
    assert "AI 动态" in digest
    assert len(digest) < 4000
