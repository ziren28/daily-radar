from argparse import Namespace

from daily_radar.cli import run_social_alert


def test_social_alert_does_not_send_empty_digest(monkeypatch, tmp_path, capsys):
    cfg_path = tmp_path / "sources.yaml"
    cfg_path.write_text(
        "settings:\n"
        "  timezone: Asia/Shanghai\n"
        "  report_title: 每日雷达\n"
        "  social_seen_ttl_hours: 6\n",
        encoding="utf-8",
    )
    calls = []

    monkeypatch.setattr("daily_radar.cli.collect_social_items", lambda cfg: [])
    monkeypatch.setattr("daily_radar.cli.send_weixin_message", lambda *args, **kwargs: calls.append(args))

    code = run_social_alert(
        Namespace(
            config=str(cfg_path),
            db=str(tmp_path / "radar.sqlite"),
            send=True,
            limit="3",
            weixin_url="http://127.0.0.1:18787/send",
            weixin_token="tok",
            weixin_env=str(tmp_path / "missing.env"),
        )
    )

    assert code == 0
    assert calls == []
    assert "social_items=0 sent=False" in capsys.readouterr().out
