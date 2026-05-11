from daily_radar.fetchers.tencent_stock import TencentValuationInputs, classify_buy_degree, render_tencent_report


def test_tencent_buy_degree_by_price_band():
    assert classify_buy_degree(465).level == "观察"
    assert classify_buy_degree(410).level == "分批买入"
    assert classify_buy_degree(350).level == "强买"
    assert classify_buy_degree(295).level == "极端机会/需复核基本面"


def test_tencent_report_core_pe_and_asset_cushion():
    data = TencentValuationInputs(price_hkd=464.4, fx_hkd_cny=0.869, shares_b=9.02)
    report = render_tencent_report(data)

    assert "腾讯监控" in report
    assert "HK$464.40" in report
    assert "核心业务 PE" in report
    assert "约10" in report or "10." in report
    assert "观察" in report
    assert "HK$380-420" in report
    assert "HK$320-360" in report
