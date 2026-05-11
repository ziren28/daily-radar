# Daily Radar

个人每日信息雷达：关注 AI 动态、Google/Alphabet 股票、科技新闻、美股新闻、腾讯新闻、福利羊毛，并通过本机微信 webhook 推送日报。

## 功能

- RSS 抓取：OpenAI、Anthropic、Hugging Face、Hacker News、TechCrunch、The Verge
- Google News RSS：Google/Alphabet、美股、腾讯、福利羊毛关键词
- Stooq 股票：GOOG、GOOGL、Nasdaq 100
- 去重：URL + 标题相似度
- 分类/评分：关键词 + 高价值事件权重
- 生成 Markdown 完整日报
- 生成微信短版摘要
- 本地词典中文化：不依赖翻译 API
- 社交媒体实时监控：马斯克、木头姐、ARK、特朗普、Tesla、SpaceX
- SQLite 历史存储
- systemd timer 每天北京时间 08:30 自动运行
- social-alert timer 每 10 分钟检查社交媒体

## Quick Start

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e '.[test]'
pytest -q
daily-radar run --config configs/sources.yaml
```

发送微信：

```bash
TOKEN=$(sudo awk -F= '/^WEIXIN_WEBHOOK_TOKEN=/{print $2}' /etc/spot-lifecycle.env | tail -1)
daily-radar run --config configs/sources.yaml --send --weixin-token "$TOKEN"
```

默认微信 webhook：

```text
http://127.0.0.1:18787/send
```

## 输出

```text
reports/YYYY-MM-DD.md
data/radar.sqlite
```

## 不依赖 API 的中文化

当前不是调用翻译 API，而是用本地词典做中文增强：

```text
Alphabet -> Alphabet/谷歌母公司
Elon Musk -> 马斯克
Cathie Wood -> 木头姐 Cathie Wood
Trump -> 特朗普
Tesla -> 特斯拉
earnings -> 财报
Fed -> 美联储
```

好处：稳定、免费、不需要外部 key。后面可以继续扩展 `src/daily_radar/pipeline/zh.py`。

## 社交媒体实时监控

默认通过 Nitter-compatible RSS，不用 X/Twitter 官方 API：

```yaml
social:
  nitter_instances:
    - https://nitter.net
  watchlist:
    - name: Elon Musk / 马斯克
      handle: elonmusk
      category: social
    - name: Cathie Wood / 木头姐
      handle: CathieDWood
      category: social
    - name: ARK Invest / 方舟投资
      handle: ARKInvest
      category: social
    - name: Donald Trump / 特朗普
      handle: realDonaldTrump
      category: politics
```

手动检查：

```bash
daily-radar social-alert --config configs/sources.yaml
```

推微信：

```bash
TOKEN=$(sudo awk -F= '/^WEIXIN_WEBHOOK_TOKEN=/{print $2}' /etc/spot-lifecycle.env | tail -1)
daily-radar social-alert --config configs/sources.yaml --send --weixin-token "$TOKEN"
```

注意：公共 Nitter 实例可能不稳定，挂了就换 `configs/sources.yaml` 里的 `nitter_instances`。

## 安装为定时任务

```bash
sudo ./install.sh
```

timer：

```text
OnCalendar=*-*-* 00:30:00 UTC
```

即北京时间 08:30。

## 配置数据源

编辑：

```text
configs/sources.yaml
```

可以调整：

- RSS 源
- Google News 关键词
- 股票 symbol
- 分类关键词
- 每个分类最多输出条数
- 微信 webhook URL

## 手动测试微信 webhook

```bash
TOKEN=$(sudo awk -F= '/^WEIXIN_WEBHOOK_TOKEN=/{print $2}' /etc/spot-lifecycle.env | tail -1)

curl -X POST http://127.0.0.1:18787/send \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text":"Daily Radar test"}'
```

## 下一步可增强

- 接入 OpenAI-compatible LLM 做中文总结和观点提炼
- 增加网页归档
- 增加实时快讯模式
- 加入 Telegram/邮件推送
- 增加个股 watchlist
- 增加羊毛源专项 crawler
