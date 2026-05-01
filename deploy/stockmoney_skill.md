---
name: stockmoney
description: StockMoney investment decision system based on Kondratiev wave theory. Use when the user asks about investment signals, strategy decisions, ETF monitoring, policy analysis, market indicators, asset allocation, or the 4% DCA method. Handles queries about Chinese A-share ETF portfolio, macro cycle positioning, and quantitative trading signals.
metadata:
  {
    "openclaw":
      {
        "emoji": "📈",
      },
  }
---

# StockMoney Investment System

## Overview

StockMoney is a 5-layer investment decision system deployed at `/opt/stockmoney`. It provides:
- Daily ETF monitoring with 4% DCA signals
- Macro cycle analysis (Kondratiev wave)
- Policy analysis (China 15th Five-Year Plan, Fed, commodities)
- Asset allocation recommendations
- Strategy decision engine

## Available Commands

When the user sends any of these keywords via Feishu, run the corresponding script:

| User Message | Script | Description |
|-------------|--------|-------------|
| `今日信号`, `盘前`, `盘后`, `monitor` | `bash /opt/stockmoney/scripts/run_monitor.sh` | ETF monitoring + 4% DCA triggers |
| `策略`, `决策`, `strategy`, `decision` | `bash /opt/stockmoney/scripts/run_strategy.sh` | Strategy decision summary |
| `推荐`, `买什么`, `recommend` | `bash /opt/stockmoney/scripts/run_strategy.sh` | Same as strategy |
| `政策`, `宏观`, `policy` | `bash /opt/stockmoney/scripts/run_policy.sh` | Policy analysis summary |
| `周期`, `康波`, `cycle` | `bash /opt/stockmoney/scripts/run_strategy.sh` | Macro cycle in strategy report |
| `市场`, `估值`, `market` | `bash /opt/stockmoney/scripts/run_strategy.sh` | Market indicators in strategy report |
| `配置`, `仓位`, `allocation` | `bash /opt/stockmoney/scripts/run_strategy.sh` | Asset allocation in strategy report |
| `完整报告`, `报告`, `report` | `bash /opt/stockmoney/scripts/run_full_report.sh` | Full strategy report |
| `研究`, `更新`, `update` | `bash /opt/stockmoney/scripts/run_strategy.sh` | Research update (run strategy) |

## Execution Rules

1. **Always use bash tool** to execute wrapper scripts. Do NOT run Python directly.
2. The wrapper scripts activate the virtualenv automatically.
3. Execution time: monitor ~10s, strategy ~15s, full report ~30s.
4. If a script times out, retry once.
5. Return the FULL output to the user. Do not summarize unless the output exceeds 4000 characters.

## Portfolio Info

- Total capital: 900,000 CNY
- 14 ETFs covering: broad base (CSI 300, CSI A500, Hang Seng Tech), growth (solar, biotech, battery), satellite (medical devices, robotics, power, chips), defense (dividend low-volatility, banks, gold, securities)
- Strategy: 4% DCA method (25 shares total, max 10 per holding, 4% drop from last buy triggers purchase)

## Current Macro View (2026-05-01)

- Kondratiev cycle: 6th wave recovery phase (2026-2035), AI + new energy driven
- Juglar cycle: Recovery
- Kitchin cycle: Uptrend
- Resonance: Strong (3 cycles aligned)
- Market: Undervalued (CSI 300 PE ~13.5, equity-bond spread 5.5%)
- Policy: 15th Five-Year Plan, 6 future industries + 6 emerging pillars
- Recommended position: 65% (medium-high)

## Log Locations

- Monitor logs: `/opt/stockmoney/logs/monitor.log`
- Strategy logs: `/opt/stockmoney/logs/strategy.log`
- Report logs: `/opt/stockmoney/logs/report.log`
- Policy logs: `/opt/stockmoney/logs/policy.log`

## Data Refresh

Scripts read hardcoded market data for 2026-05. For real-time data, `investment_monitor.py` fetches live ETF quotes from Sina Finance API.
