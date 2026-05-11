# Daily Radar

个人每日信息雷达：关注 AI 动态、Google/Alphabet 股票、科技新闻、美股新闻、腾讯新闻、福利羊毛，并通过本机微信 webhook 推送日报。

## 功能

- RSS 抓取：OpenAI、Anthropic、Hugging Face、Hacker News、TechCrunch、The Verge
- Google News RSS：Google/Alphabet、美股、腾讯、福利羊毛关键词
- Stooq 股票：GOOG、GOOGL、Nasdaq 100
- 腾讯股价每日估值监控：按“资产垫 + 核心业务 PE”输出买入程度
- 去重：URL + 标题相似度
- 分类/评分：关键词 + 高价值事件权重
- 生成 Markdown 完整日报
- 生成微信短版摘要
- Google 免费翻译接口中文化：`translate.googleapis.com`，无需 key；失败时回退本地词典
- 社交媒体实时监控：马斯克、木头姐、ARK、特朗普、Tesla、SpaceX
- SQLite 历史存储
- systemd timer 每天北京时间 08:30 自动运行
- social-alert timer 每 10 分钟检查社交媒体
- 可靠推送：已见内容 TTL 去重、标题签名跨源去重、微信分片发送、失败重试

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

## 中文翻译

默认优先调用 Google 免费翻译接口：

```text
https://translate.googleapis.com/translate_a/single?client=gtx
```

特点：

```text
无需 API key
无需 Google Cloud 项目
失败时自动回退本地词典
```

配置：

```yaml
settings:
  translate_enabled: true
  translate_provider: google_free
```

回退词典在：

```text
src/daily_radar/pipeline/zh.py
```

例如：

```text
Elon Musk -> 马斯克
Cathie Wood -> 木头姐 Cathie Wood
Trump -> 特朗普
Tesla -> 特斯拉
Fed -> 美联储
```

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

## 腾讯股价买入程度监控

每日跑日报时会附加腾讯估值报告，逻辑按用户给定框架：**不是把底看成现金资产底，而是资产垫 + 核心业务被压到多少倍利润**。

默认基础参数来自 2025 年报/业绩材料附近口径：

```yaml
tencent_stock:
  fallback_price_hkd: 464.4
  fx_hkd_cny: 0.869
  shares_b: 9.02
  non_ifrs_profit_rmb_b: 259.6
  fcf_rmb_b: 182.6
  net_cash_rmb_b: 107.1
  listed_investments_rmb_b: 672.7
  unlisted_investments_rmb_b: 363.1
```

输出会包含：

```text
现价
总市值
2025 非 IFRS PE
净现金 + 上市投资 + 50%非上市投资资产垫
扣资产垫后的核心业务 PE
买入程度 0-100
操作建议
```

买入分层：

| 股价区间 | 买入程度 | 行动 |
|---|---|---|
| HK$460+ | 观察 | 不追高，等 430 下方或业绩确认 |
| HK$430-460 | 小仓/观察 | 可小仓或定投观察 |
| HK$380-420 | 分批买入 | 价值区，越接近 380 越有吸引力 |
| HK$320-360 | 强买 | 恐慌底，需要排雷后明显加仓 |
| HK$300 以下 | 极端机会/需复核基本面 | 先确认游戏、广告、支付生态没坏 |

## 从 claude_paipai 学来的稳定性设计

`claude_paipai` 日报稳定的关键点已经迁移过来：

1. **每个 fetcher 自己兜底**：单源失败不影响整体日报。
2. **定时器 Persistent**：机器睡眠/重启错过触发后，systemd 会补跑。
3. **seen TTL 去重**：已推过的内容一段时间内不重复刷屏。
4. **标题签名去重**：不同来源报道同一件事，也只推一次。
5. **always 内容保留**：行情类内容可每次都推，不受去重影响。
6. **微信分片发送**：长日报按 1500 字切块，避免微信消息过长失败。
7. **发送重试**：webhook/网络短暂失败会自动 retry。
8. **本地翻译缓存/回退**：Google 免费翻译失败时，本地词典兜底。

配置：

```yaml
settings:
  seen_ttl_hours: 24
  social_seen_ttl_hours: 6
```

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
