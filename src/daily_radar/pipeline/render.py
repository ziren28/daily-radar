from __future__ import annotations

from daily_radar.models import RadarItem

DEFAULT_ORDER = ["ai", "google", "tech", "us_stock", "tencent", "deals"]


def _category_title(category: str, cfg: dict) -> str:
    return cfg.get("categories", {}).get(category, {}).get("title", category)


def render_markdown_report(grouped: dict[str, list[RadarItem]], cfg: dict, report_date: str) -> str:
    title = cfg.get("settings", {}).get("report_title", "每日雷达")
    lines = [f"# {title} {report_date}", ""]
    highlights = []
    for category in DEFAULT_ORDER:
        highlights.extend(grouped.get(category, [])[:1])
    if highlights:
        lines += ["## 今日重点", ""]
        for item in sorted(highlights, key=lambda x: x.score, reverse=True)[:5]:
            url = f" ([link]({item.url}))" if item.url else ""
            lines.append(f"- **{item.title}**{url}")
        lines.append("")
    for category in DEFAULT_ORDER:
        items = grouped.get(category, [])
        if not items:
            continue
        lines += [f"## {_category_title(category, cfg)}", ""]
        for item in items:
            source = f"`{item.source}` " if item.source else ""
            url = f" [来源]({item.url})" if item.url else ""
            summary = f" — {item.summary}" if item.summary else ""
            lines.append(f"- {source}**{item.title}**{summary}{url}")
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def render_weixin_digest(grouped: dict[str, list[RadarItem]], cfg: dict, report_date: str, max_chars: int = 3800) -> str:
    title = cfg.get("settings", {}).get("report_title", "每日雷达")
    lines = [f"【{title}】{report_date}", ""]
    highlights = []
    for category in DEFAULT_ORDER:
        highlights.extend(grouped.get(category, [])[:1])
    if highlights:
        lines.append("今日重点：")
        for idx, item in enumerate(sorted(highlights, key=lambda x: x.score, reverse=True)[:3], 1):
            lines.append(f"{idx}. {item.title}")
        lines.append("")
    for category in DEFAULT_ORDER:
        items = grouped.get(category, [])[:4]
        if not items:
            continue
        lines.append(f"{_category_title(category, cfg)}：")
        for item in items:
            lines.append(f"- {item.title}")
        lines.append("")
    text = "\n".join(lines).strip()
    return text if len(text) <= max_chars else text[: max_chars - 20] + "\n..."