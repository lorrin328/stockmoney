# StockMoney - 基于康波周期的投资决策系统

> 以康德拉季耶夫长波理论为核心，结合多周期嵌套分析、市场指标验证和量化执行策略的完整投资研究体系

## 系统架构

```
stockmoney/
├── data/                   # 数据存储
│   ├── history/            # ETF历史净值缓存
│   ├── signals/            # 每日信号报告
│   └── portfolio_config.json   # 投资组合配置
├── reports/                # 研究报告输出
├── scripts/                # 核心脚本（五层架构）
│   ├── kondratiev_model.py         # Layer 1: 宏观周期定位
│   ├── cycle_phase_evaluator.py    # Layer 2: 周期共振分析
│   ├── market_indicators.py        # Layer 2: 市场指标验证
│   ├── asset_allocator.py          # Layer 3: 资产配置决策
│   ├── strategy_engine.py          # Layer 4: 策略决策引擎
│   ├── four_percent_model.py       # Layer 5: 4%定投法执行
│   ├── policy_analyzer.py          # 政策与宏观环境分析
│   ├── investment_monitor.py       # 每日监控与信号生成
│   └── sina_fetcher.py             # 数据获取工具
├── papers/                 # 深度研究报告
│   └── 康波周期深度研究报告.md
├── reports/                # 策略文档
│   └── four_percent_strategy_guide.md
└── data/portfolio_config.json      # 90万ETF组合配置
```

## 五层投资决策架构

| 层级 | 模块 | 周期 | 功能 | 输出 |
|------|------|------|------|------|
| **Layer 1** | 康波周期定位 | 50-60年 | 判断当前所处康波阶段 | 战略方向 |
| **Layer 2** | 周期共振+市场指标 | 3-20年 | 多周期嵌套验证+市场情绪 | 战术判断 |
| **Layer 3** | 资产配置决策 | - | 根据阶段推荐资产权重 | 配置方案 |
| **Layer 4** | 策略决策引擎 | - | 整合所有模块输出统一策略 | 完整报告 |
| **Layer 5** | 4%定投法执行 | 日/周 | 触发买入/卖出/止盈 | 操作信号 |

## 核心模块

### Layer 1: 宏观周期定位

**`scripts/kondratiev_model.py`** — 康波周期模型

- 6轮历史康波数据（1782年至今）
- 当前定位：第六轮康波（AI与新能源）复苏期起点
- 阶段特征与资产配置矩阵
- 2026年投资主题：AI算力、新能源、生物技术、工业金属

```bash
python scripts/kondratiev_model.py --report    # 生成宏观周期报告
python scripts/kondratiev_model.py --phase     # 显示当前阶段
```

### Layer 2: 周期共振与市场验证

**`scripts/cycle_phase_evaluator.py`** — 多周期嵌套评估

基于熊彼特三周期嵌套理论：
- 康德拉季耶夫长波（50-60年）
- 朱格拉中周期（8-10年，设备投资）
- 基钦短周期（3-4年，库存）
- 库兹涅茨周期（15-25年，房地产）

```bash
python scripts/cycle_phase_evaluator.py --report      # 生成共振报告
python scripts/cycle_phase_evaluator.py --resonance   # 显示共振结果
```

**`scripts/market_indicators.py`** — 市场指标系统

- 估值指标：PE/PB分位、E/P、股债利差
- 情绪指标：波动率、融资余额、新发基金
- 流动性指标：M2增速、社融增速、国债收益率
- 商品指标：CRB指数、黄金、原油

```bash
python scripts/market_indicators.py --summary   # 综合判断
python scripts/market_indicators.py --report    # 完整报告
```

### Layer 3: 资产配置决策

**`scripts/asset_allocator.py`** — 资产配置系统

四阶段资产配置矩阵：

| 阶段 | 股票 | 债券 | 商品 | 黄金 | 现金 | 防御 |
|------|------|------|------|------|------|------|
| 复苏期 | 40% | 20% | 25% | 10% | 5% | 8% |
| 繁荣期 | 50% | 15% | 20% | 8% | 7% | 8% |
| 衰退期 | 25% | 35% | 15% | 12% | 13% | 15% |
| 萧条期 | 15% | 35% | 10% | 20% | 25% | 15% |

```bash
python scripts/asset_allocator.py --report        # 生成配置报告
python scripts/asset_allocator.py --allocation    # 显示配置方案
```

### 政策与宏观环境分析

**`scripts/policy_analyzer.py`** — 政策分析系统

结合中国政策大势与国际环境，提供政策面投资指引：

- **十五五规划**：六大未来产业 + 六大新兴支柱产业投资映射
- **大宗商品**：铜/黄金/原油/锂/铝供需分析与价格预测
- **美联储政策**：利率、缩表、降息预期跟踪
- **中国货币政策**：LPR、降准、结构性工具
- **地缘政治**：中美博弈、中东局势影响评估

```bash
python scripts/policy_analyzer.py --report    # 生成政策分析报告
python scripts/policy_analyzer.py --summary   # 显示分析摘要
```

### Layer 4: 策略决策引擎

**`scripts/strategy_engine.py`** — 统一决策输出

整合所有模块，输出完整策略决策报告：
- 宏观周期定位
- 周期共振分析
- 市场指标验证
- 资产配置方案
- 关键赛道推荐
- 进入/退出策略
- 风险管理清单
- 操作待办事项

```bash
python scripts/strategy_engine.py --report      # 生成策略报告
python scripts/strategy_engine.py --decision    # 显示决策摘要
```

### Layer 5: 4%定投法执行

**`scripts/four_percent_model.py`** — 核心定投模型

基于B站UP主"研究员雷牛牛"强化版理论（修正版）：

| 参数 | 值 | 说明 |
|------|-----|------|
| **总份数** | **25份** | 总资金平均分25份 |
| **单标的上限** | **10份** | 同一只基金最多10份 |
| **触发基准** | **上一个买入点** | 从上次买入价下跌触发 |
| **触发跌幅** | 4% | 下跌≥4%触发买入1份 |
| **买入过滤** | E/P > 10% | 格雷厄姆低估线 |
| **卖出条件** | E/P < 6.4% | 格雷厄姆高估线 |
| **等待纪律** | 严格 | 未跌穿4%绝不提前买入 |

**适用场景**：
- ✅ 震荡市/下跌市/筑底期 — 表现最佳
- ❌ 单边上涨市 — 容易踏空

```bash
# 回测单个标的
python scripts/four_percent_model.py --backtest 510300 --start 2022-01-01 --capital 100000

# 回测所有配置标的
python scripts/four_percent_model.py --backtest-all
```

### 每日监控

**`scripts/investment_monitor.py`** — 投资组合监控

功能：
1. 拉取14只ETF实时行情（东方财富API）
2. 计算价格分位（2年）和E/P代理值
3. 检查4%定投法触发条件
4. 检查仓位偏离度
5. 输出每日信号报告（含宏观周期定位）

```bash
# 每日监控（生成报告）
python scripts/investment_monitor.py

# 初始化历史数据缓存
python scripts/investment_monitor.py --init-history --force
```

报告输出：`data/signals/signal_report_YYYYMMDD.md`

## 投资组合配置

当前配置：14只ETF，总规模90万元，18个月定投方案

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

## 2026年核心判断（2026-05-01更新）

### 周期面
1. **康波定位**：第六轮康波复苏期起点（2026-2035），AI+新能源为核心引擎
2. **周期共振**：康波复苏 + 朱格拉复苏 + 基钦上行 = 三周期同向
3. **市场状态**：估值偏低（沪深300 PE 13.5，股债利差5.5%），情绪中性

### 政策面
4. **十五五规划**：六大未来产业（量子/生物制造/氢能/脑机接口/具身智能/6G）+ 六大新兴支柱产业（集成电路/航空航天/生物医药/新型储能/低空经济/智能机器人），总投资超10万亿
5. **美联储**：维持3.50%-3.75%，缩表已暂停，全年预计降息0-1次，5月美联储主席换届
6. **中国央行**：适度宽松，择机降准降息，1年期LPR 3.10%

### 大宗商品
7. **黄金**：看涨至4900-5000美元，央行购金+地缘避险+去美元化
8. **铜**：供应紧缺+新能源需求，均价11,400美元/吨
9. **原油**：高位震荡，基准86美元/桶，5月后取决于霍尔木兹海峡局势

### 策略方向
10. **核心赛道**：AI算力/半导体/创新药/新能源/工业金属
11. **仓位建议**：中高仓位（60-75%，政策面修正后）
12. **4%定投法**：启用，震荡市特征明显，宽基为主

## 文档体系

| 文档 | 内容 |
|------|------|
| `reports/four_percent_strategy_guide.md` | 4%定投法完整策略手册（修正版） |
| `papers/康波周期深度研究报告.md` | 康波周期理论研究 |
| `reports/macro_cycle_report_YYYYMMDD.md` | 宏观周期定位报告 |
| `reports/cycle_resonance_report_YYYYMMDD.md` | 周期共振分析报告 |
| `reports/market_indicators_YYYYMMDD.md` | 市场指标综合报告 |
| `reports/asset_allocation_YYYYMMDD.md` | 资产配置决策报告 |
| `reports/strategy_decision_YYYYMMDD.md` | 策略决策报告 |
| `reports/policy_analysis_YYYYMMDD.md` | 政策与宏观环境分析报告 |
| `data/signals/signal_report_YYYYMMDD.md` | 每日监控报告 |

## MCP 服务器配置

| MCP 服务器 | 用途 | 安装方式 |
|-----------|------|---------|
| alpha-vantage-mcp | 股票/加密货币数据 | `npx -y alpha-vantage-mcp` |
| investor-agent | Yahoo Finance 数据 | `npx -y investor-agent` |
| finbud-data-mcp | 综合金融数据 | `npx -y finbud-data-mcp` |
| helium-mcp | 新闻+市场数据 | `npx -y helium-mcp` |
| katzilla | 政府/经济数据 | `npx -y @katzilla/mcp` |
| playwright-mcp | 网页抓取 | `npx -y @playwright/mcp` |
| github-mcp-server | GitHub 操作 | 内置 |

## 使用方式

### 完整决策流程

```bash
# 1. 生成宏观周期报告
python scripts/kondratiev_model.py --report

# 2. 生成周期共振报告
python scripts/cycle_phase_evaluator.py --report

# 3. 生成市场指标报告
python scripts/market_indicators.py --report

# 4. 生成政策分析报告（十五五+大宗商品+美联储）
python scripts/policy_analyzer.py --report

# 5. 生成资产配置报告
python scripts/asset_allocator.py --report

# 6. 生成统一策略报告（整合以上所有）
python scripts/strategy_engine.py --report

# 7. 每日监控（含4%定投信号）
python scripts/investment_monitor.py
```

### 快速查看决策摘要

```bash
python scripts/strategy_engine.py --decision
```

## 数据来源

- 东方财富 push2 API（A股ETF实时行情）
- akshare（历史数据补充）
- Alpha Vantage（美股/全球股票）
- Yahoo Finance（美股/港股/基金）

## 风险提示

1. **康波周期争议**：学术上存在争议，不应作为唯一决策依据
2. **周期识别滞后性**：周期拐点判断通常滞后2-5年
3. **政策干预**：各国央行政策可能改变周期运行轨迹
4. **4%定投法局限**：单边上涨市会严重踏空
5. **历史不代表未来**：回测基于历史数据，市场环境变化可能导致策略失效

> **本系统仅为研究参考，不构成投资建议。投资有风险，入市需谨慎。**

## License

MIT
