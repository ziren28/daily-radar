# Daily Radar

个人每日信息雷达：关注 AI 动态、Google/Alphabet 股票、科技新闻、美股新闻、腾讯新闻、福利羊毛，并通过本机微信 webhook 推送日报。

## Quick Start

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e '.[test]'
daily-radar run --config configs/sources.yaml --send
```

需要本机微信 webhook：

```text
http://127.0.0.1:18787/send
```

Token 默认从 `/etc/spot-lifecycle.env` 的 `WEIXIN_WEBHOOK_TOKEN` 读取。
