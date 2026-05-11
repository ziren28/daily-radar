from __future__ import annotations

import csv
import io
from dataclasses import dataclass
from datetime import datetime, timezone

import httpx

from daily_radar.models import RadarItem


@dataclass(slots=True)
class TencentValuationInputs:
    price_hkd: float
    fx_hkd_cny: float = 0.869
    shares_b: float = 9.02
    non_ifrs_profit_rmb_b: float = 259.6
    fcf_rmb_b: float = 182.6
    net_cash_rmb_b: float = 107.1
    listed_investments_rmb_b: float = 672.7
    unlisted_investments_rmb_b: float = 363.1


@dataclass(slots=True)
class BuyDegree:
    level: str
    score: int
    action: str
    reason: str


def classify_buy_degree(price_hkd: float) -> BuyDegree:
    if price_hkd < 300:
        return BuyDegree(
            "极端机会/需复核基本面",
            95,
            "若游戏、广告、支付生态没有破坏，可重仓；但必须先排雷。",
            "股价低于正常估值底，通常意味着市场在定价基本面断裂。",
        )
    if price_hkd <= 360:
        return BuyDegree(
            "强买",
            85,
            "适合明显加仓，优先检查监管、AI 投入、回购和业绩是否恶化。",
            "核心业务大概率被压到 6-7 倍利润，属于恐慌底区域。",
        )
    if price_hkd <= 420:
        return BuyDegree(
            "分批买入",
            70,
            "可以按计划分批买入，越接近 380 吸引力越高。",
            "核心业务约 8-9 倍利润，资产垫明显，性价比开始很好。",
        )
    if price_hkd <= 460:
        return BuyDegree(
            "小仓/观察",
            45,
            "可以小仓或定投观察，等待 Q1/回购/AI capex 信号。",
            "估值偏克制但未到价值投资意义上的硬底。",
        )
    return BuyDegree(
        "观察",
        25,
        "不追高；保留跟踪，等待 430 下方或业绩超预期确认。",
        "当前价格附近核心业务约 10 倍利润，不贵但安全边际一般。",
    )


def _fmt_hkd(x: float) -> str:
    return f"HK${x:,.2f}"


def calculate_metrics(data: TencentValuationInputs) -> dict[str, float]:
    market_cap_hkd_b = data.price_hkd * data.shares_b
    market_cap_rmb_b = market_cap_hkd_b * data.fx_hkd_cny
    pe = market_cap_rmb_b / data.non_ifrs_profit_rmb_b
    asset_cushion_rmb_b = data.net_cash_rmb_b + data.listed_investments_rmb_b + 0.5 * data.unlisted_investments_rmb_b
    asset_cushion_hkd_per_share = asset_cushion_rmb_b / data.fx_hkd_cny / data.shares_b
    core_value_rmb_b = market_cap_rmb_b - asset_cushion_rmb_b
    core_pe = core_value_rmb_b / data.non_ifrs_profit_rmb_b
    return {
        "market_cap_hkd_b": market_cap_hkd_b,
        "market_cap_rmb_b": market_cap_rmb_b,
        "pe": pe,
        "asset_cushion_rmb_b": asset_cushion_rmb_b,
        "asset_cushion_hkd_per_share": asset_cushion_hkd_per_share,
        "core_value_rmb_b": core_value_rmb_b,
        "core_pe": core_pe,
    }


def render_tencent_report(data: TencentValuationInputs) -> str:
    m = calculate_metrics(data)
    degree = classify_buy_degree(data.price_hkd)
    lines = [
        f"腾讯监控：{_fmt_hkd(data.price_hkd)}，买入程度：{degree.level}（{degree.score}/100）",
        f"市值约 HK${m['market_cap_hkd_b']/1000:.2f} 万亿 / RMB{m['market_cap_rmb_b']/1000:.2f} 万亿；2025 非 IFRS PE 约{m['pe']:.1f}倍。",
        f"按“净现金 + 上市投资 + 50%非上市投资”扣除，资产垫约 HK${m['asset_cushion_hkd_per_share']:.0f}/股，核心业务 PE 约{m['core_pe']:.1f}倍。",
        f"操作建议：{degree.action}",
        f"理由：{degree.reason}",
        "价格分层：HK$430-460 小仓/观察；HK$380-420 分批买入；HK$320-360 强买；HK$300 以下需先确认基本面没有破坏。",
        "重点跟踪：2026 Q1 业绩、广告/游戏/金融科技增速、AI 投入是否吞利润、回购力度、监管和港股流动性。",
    ]
    return "\n".join(lines)


def fetch_tencent_price_stooq() -> float | None:
    # Stooq supports HK tickers inconsistently; try common variants.
    symbols = ["0700.HK", "700.HK", "TCEHY.US"]
    for symbol in symbols:
        url = f"https://stooq.com/q/l/?s={symbol.lower()}&f=sd2t2ohlcv&h&e=csv"
        try:
            r = httpx.get(url, timeout=12, headers={"User-Agent": "daily-radar/0.1"})
            r.raise_for_status()
            rows = list(csv.DictReader(io.StringIO(r.text)))
            if rows and rows[0].get("Close") not in (None, "", "N/D"):
                return float(rows[0]["Close"])
        except Exception:
            continue
    return None


def fetch_tencent_stock_item(cfg: dict | None = None) -> RadarItem:
    cfg = cfg or {}
    stock_cfg = (cfg.get("tencent_stock") or {}) if isinstance(cfg, dict) else {}
    price = fetch_tencent_price_stooq() or float(stock_cfg.get("fallback_price_hkd", 464.4))
    inputs = TencentValuationInputs(
        price_hkd=price,
        fx_hkd_cny=float(stock_cfg.get("fx_hkd_cny", 0.869)),
        shares_b=float(stock_cfg.get("shares_b", 9.02)),
        non_ifrs_profit_rmb_b=float(stock_cfg.get("non_ifrs_profit_rmb_b", 259.6)),
        fcf_rmb_b=float(stock_cfg.get("fcf_rmb_b", 182.6)),
        net_cash_rmb_b=float(stock_cfg.get("net_cash_rmb_b", 107.1)),
        listed_investments_rmb_b=float(stock_cfg.get("listed_investments_rmb_b", 672.7)),
        unlisted_investments_rmb_b=float(stock_cfg.get("unlisted_investments_rmb_b", 363.1)),
    )
    degree = classify_buy_degree(inputs.price_hkd)
    title = render_tencent_report(inputs)
    return RadarItem(
        source="Tencent valuation",
        category="tencent",
        title=title,
        url="https://www.tencent.com/en-us/investors.html",
        summary=f"买入程度 {degree.level} {degree.score}/100",
        published_at=datetime.now(timezone.utc).isoformat(),
        raw={"always": True, "price_hkd": inputs.price_hkd, "buy_score": degree.score},
        score=20 + degree.score / 10,
    )
