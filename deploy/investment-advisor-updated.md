---
name: investment-advisor
description: |
  A股ETF投资组合的4%定投法智能决策系统，基于康波周期理论的多层投资架构。
  提供每日信号监控、策略决策、政策分析、资产配置建议。
  支持用户通过飞书查询：今日信号/策略推荐/政策宏观/周期分析/市场估值/完整报告。
  系统部署在 /opt/stockmoney，由 Python 脚本驱动，定时任务自动执行。
  处理A股ETF组合（14只ETF，90万资金）的买入/卖出/止盈/仓位管理决策。
---

# 智能投资顾问

## 系统架构

本Skill对接 **StockMoney** 投资决策系统，部署于 `/opt/stockmoney`：

```
用户消息 (飞书)
    |
    v
OpenClaw Gateway --> 本Skill解析 --> 执行Python脚本
    |
    +-- 定时任务 (crontab)
        +-- 工作日 9:25  盘前监控
        +-- 工作日 15:05 盘后监控
        +-- 每日 20:00  策略摘要
        +-- 每周一 9:30  周度报告
        +-- 每月1日 9:00 政策分析
```

## 五层决策架构

| 层级 | 模块 | 功能 | 对应脚本 |
|------|------|------|---------|
| Layer 1 | 康波周期定位 | 50-60年宏观周期判断 | `kondratiev_model.py` |
| Layer 2 | 周期共振+市场指标 | 多周期嵌套验证 | `cycle_phase_evaluator.py` + `market_indicators.py` |
| Layer 3 | 资产配置决策 | 资产类别权重推荐 | `asset_allocator.py` |
| Layer 4 | 策略决策引擎 | 统一输出完整策略 | `strategy_engine.py` |
| Layer 5 | 4%定投法执行 | 触发买入/卖出/止盈 | `four_percent_model.py` |
| 政策层 | 政策与宏观分析 | 十五五/美联储/大宗商品 | `policy_analyzer.py` |

## 用户命令映射

当用户发送以下消息时，执行对应脚本：

| 用户消息 | 执行命令 | 说明 |
|---------|---------|------|
| `今日信号`, `盘前`, `盘后`, `monitor`, `信号` | `bash /opt/stockmoney/scripts/run_monitor.sh` | ETF监控+4%定投触发 |
| `策略`, `决策`, `strategy`, `decision`, `推荐`, `买什么` | `bash /opt/stockmoney/scripts/run_strategy.sh` | 策略决策摘要 |
| `政策`, `宏观`, `policy`, `宏观分析` | `bash /opt/stockmoney/scripts/run_policy.sh` | 政策分析摘要 |
| `周期`, `康波`, `cycle`, `共振` | `bash /opt/stockmoney/scripts/run_strategy.sh` | 含周期分析 |
| `市场`, `估值`, `market`, `指标` | `bash /opt/stockmoney/scripts/run_strategy.sh` | 含市场指标 |
| `配置`, `仓位`, `allocation` | `bash /opt/stockmoney/scripts/run_strategy.sh` | 含资产配置 |
| `完整报告`, `报告`, `report`, `full` | `bash /opt/stockmoney/scripts/run_full_report.sh` | 完整策略报告 |
| `研究`, `更新`, `update`, `refresh` | `bash /opt/stockmoney/scripts/run_full_report.sh` | 刷新完整报告 |

## 执行规则

1. **使用 bash 工具执行 wrapper 脚本**，不要直接运行 python
2. Wrapper 脚本会自动激活虚拟环境 `venv`
3. 执行时间：monitor ~10s，strategy ~15s，full report ~30s
4. 将脚本的完整输出返回给用户，不要自行总结（除非超过4000字符）
5. 如果脚本执行失败，检查 `/opt/stockmoney/logs/` 目录下的日志

## 投资组合配置

- **总资金**：90万元
- **标的数量**：14只ETF
- **策略**：4%定投法（研究员雷牛牛强化版）

| 类型 | ETF | 代码 | 目标权重 |
|------|-----|------|---------|
| 宽基底仓 | 沪深300ETF | 510300 | 11.1% |
| 宽基底仓 | 中证A500ETF | 560610 | 11.1% |
| 宽基底仓 | 恒生科技ETF | 513130 | 11.1% |
| 核心进攻 | 光伏ETF | 159857 | 8.9% |
| 核心进攻 | 创新药ETF | 159992 | 8.9% |
| 核心进攻 | 电池ETF | 159755 | 6.7% |
| 卫星配置 | 医疗器械ETF | 159898 | 5.6% |
| 卫星配置 | 机器人ETF | 562500 | 5.6% |
| 卫星配置 | 电力ETF | 159611 | 4.4% |
| 卫星配置 | 芯片ETF | 159995 | 4.4% |
| 防御配置 | 红利低波ETF | 512890 | 8.9% |
| 防御配置 | 银行ETF | 512800 | 5.6% |
| 防御配置 | 黄金ETF | 518880 | 4.4% |
| 防御配置 | 证券ETF | 512880 | 3.3% |

## 4%定投法核心规则

- **总份数**：25份（总资金平均分25份）
- **单标的上限**：10份
- **触发基准**：上一个买入点（非最低点）
- **触发跌幅**：下跌 >= 4% 触发买入1份
- **买入过滤**：E/P > 10%（格雷厄姆低估线）
- **卖出条件**：E/P < 6.4%（格雷厄姆高估线）
- **止盈策略**：盈利超30%启动动态止盈，回撤50%止盈

## 当前宏观判断（2026-05-01）

- **康波定位**：第六轮康波复苏期起点（2026-2035），AI+新能源驱动
- **周期共振**：康波复苏 + 朱格拉复苏 + 基钦上行 = 三周期同向（强共振）
- **市场情绪**：BULLISH（68分）
- **推荐仓位**：65%（中高位，65%-80%区间）
- **4%定投法状态**：启用（震荡市特征明显）
- **核心赛道**：AI算力/半导体/创新药/新能源/工业金属

## 政策面要点

- **十五五规划**：六大未来产业 + 六大新兴支柱产业，总投资超10万亿
- **美联储**：3.50%-3.75%，缩表已暂停，全年预计降息0-1次
- **中国央行**：适度宽松，择机降准降息，1年期LPR 3.10%
- **大宗商品**：黄金看涨至4900-5000美元，铜均价11,400美元/吨

## 日志与报告位置

- 监控日志：`/opt/stockmoney/logs/monitor.log`
- 策略日志：`/opt/stockmoney/logs/strategy.log`
- 报告日志：`/opt/stockmoney/logs/report.log`
- 政策日志：`/opt/stockmoney/logs/policy.log`
- 每日信号报告：`/opt/stockmoney/data/signals/signal_report_YYYYMMDD.md`
- 策略报告：`/opt/stockmoney/reports/strategy_decision_YYYYMMDD.md`

## 数据更新机制

- **实时数据**：`investment_monitor.py` 从新浪财经API获取ETF实时行情
- **历史数据**：akshare库补充，首次运行需初始化：`cd /opt/stockmoney && source venv/bin/activate && python scripts/investment_monitor.py --init-history`
- **研究更新**：CC CLI 每周自动更新分析逻辑（已安装 Claude Code CLI v2.1.126）

## 风险提示

1. 康波周期存在学术争议，不应作为唯一决策依据
2. 周期拐点判断通常滞后2-5年
3. 4%定投法在单边上涨市会严重踏空
4. 历史回测不代表未来收益
5. 本系统仅为研究参考，不构成投资建议

## 关联文档

- 本地文档：`/opt/stockmoney/README.md`
- 部署文档：`/opt/stockmoney/deploy/README_DEPLOY.md`
- 4%策略手册：`/opt/stockmoney/reports/four_percent_strategy_guide.md`
- 原有参考文档（保留）：
  - `references/investment-strategy.md`
  - `references/portfolio-mgmt.md`
  - `references/data-schema.md`
  - `references/usage-guide.md`
