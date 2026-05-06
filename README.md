# StockMoney — 基于康波周期的投资决策系统

> 以康德拉季耶夫长波理论为核心，结合多周期嵌套分析、市场指标验证、ETF多维度甄选和量化执行策略的完整投资研究体系

## 系统架构

```
stockmoney/
├── data/                          # 数据存储
│   ├── history/                   # ETF 历史净值缓存 (CSV)
│   ├── signals/                   # 每日信号报告
│   ├── model_params.json          # 🆕 中央模型参数（编辑此文件更新模型，无需改代码）
│   ├── portfolio_config.json      # 投资组合配置
│   └── valuation_cache.json       # 指数估值缓存（6小时TTL）
├── reports/                       # 研究报告输出（Markdown）
├── scripts/                       # 核心脚本（五层架构 + 辅助模块）
│   ├── config_loader.py           # 🆕 配置加载器（所有模块统一从此读取参数）
│   ├── kondratiev_model.py        # Layer 1: 宏观周期定位
│   ├── cycle_phase_evaluator.py   # Layer 2: 周期共振分析
│   ├── market_indicators.py       # Layer 2: 市场指标验证
│   ├── asset_allocator.py         # Layer 3: 资产配置决策
│   ├── etf_selector.py            # 🆕 ETF 多维度甄选系统（5因子评分）
│   ├── strategy_engine.py         # Layer 4: 策略决策引擎（整合所有模块）
│   ├── four_percent_model.py      # Layer 5: 4% 定投法执行与回测
│   ├── policy_analyzer.py         # 政策与宏观环境分析
│   ├── investment_monitor.py      # 每日监控与信号生成
│   ├── valuation_fetcher.py       # 🆕 实时指数估值获取（东方财富API）
│   ├── research_driver.py         # 🆕 研究更新驱动器（定时自动迭代）
│   ├── sina_fetcher.py            # 新浪数据获取工具
│   └── extract_papers.py          # 论文提取工具
├── tests/                         # 🆕 测试套件
│   └── test_four_percent_model.py # 4% 定投法单元测试（21个用例）
├── papers/                        # 深度研究报告
├── policies/                      # 政策文档
├── deploy/                        # 服务器部署脚本
└── .github/                       # GitHub Actions CI
```

## 五层投资决策架构

| 层级 | 模块 | 周期 | 功能 | 输出 |
|------|------|------|------|------|
| **Layer 1** | 康波周期定位 | 50-60年 | 判断当前所处康波阶段 | 战略方向 |
| **Layer 2** | 周期共振 + 市场指标 | 3-20年 | 多周期嵌套验证 + 市场情绪 | 战术判断 |
| **Layer 3** | 资产配置 + ETF甄选 | — | 根据阶段推荐资产权重 + 多因子ETF评分 | 配置方案 |
| **Layer 4** | 策略决策引擎 | — | 整合所有模块输出统一策略 | 完整报告 |
| **Layer 5** | 4% 定投法执行 | 日/周 | 触发买入/卖出/止盈 | 操作信号 |

## 配置系统（v2.0）

所有模型参数统一存储在 `data/model_params.json`，通过 `scripts/config_loader.py` 加载。各模块优先从配置文件读取，失败时回退到内置默认值。

```
data/model_params.json          ← 编辑此 JSON 更新模型参数
        ↓
scripts/config_loader.py        ← 类型化访问器 (ModelConfig)
    ↓       ↓       ↓
kondratiev  market  asset   policy  etf_selector
```

**优势**：修改模型参数只需编辑 JSON，无需改动 Python 代码。支持滚动更新：修改参数 → 运行回测 → git commit。

## 三大用户触发功能（对话工作流）

在五层架构底座之上，系统提供三个由用户主动触发的闭环功能。完整工作流见 [`reports/操作说明.md`](reports/操作说明.md)。

| 功能 | 触发方式 | 输入 | 核心输出 |
|------|---------|------|---------|
| **F1 模型自学习与校验** | 自然语言命令（"更新模型"、"研究黄金"、"回测沪深300"） | 自然语言指令 | `papers/` 研究报告、`reports/` 迭代日志、`scripts/` 代码更新、`data/model_params.json` 参数更新 |
| **F2 持仓记录与建议** | 上传持仓截图后询问（"我现在该买什么？"、"看看我的持仓"） | 持仓截图 + 用户问题 | `data/positions/positions_*.json`、`reports/advice_*.md` |
| **F3 周期性持仓分析报告** | 周末/月末要求总结（"周报"、"月报"、"总结一下"） | 时间范围（周/月/自定义） | `reports/portfolio_review/{周报\|月报}_*.md` |

### 三大功能与五层架构的关系

- **F1** 调用并迭代 Layer 1-5 的模型 + 写入新研究 → 自动更新 `model_params.json`
- **F2** 读取 Layer 4-5 的当前决策，叠加用户实际持仓数据
- **F3** 综合 Layer 1-5 输出 + 持仓收益归因

> 隐私说明：`data/positions/` 中的实际持仓 JSON 和 `reports/portfolio_review/`、`reports/advice_*.md` 已配置 `.gitignore` 排除，不会同步到 GitHub。

---

## 核心模块

### Layer 1: 宏观周期定位

**`scripts/kondratiev_model.py`** — 康波周期模型

- 6 轮历史康波数据（1782 年至今），支持从 `data/model_params.json` 加载
- 当前定位：第六轮康波（AI 与新能源）复苏期起点（2026-2035）
- 阶段特征与资产配置矩阵
- 2026 年投资主题：AI 算力、AI 应用、新能源、高端制造、生物技术、工业金属

```bash
python scripts/kondratiev_model.py --report    # 生成宏观周期报告
python scripts/kondratiev_model.py --phase     # 显示当前阶段
```

### Layer 2: 周期共振与市场验证

**`scripts/cycle_phase_evaluator.py`** — 多周期嵌套评估

基于熊彼特三周期嵌套理论，评估四个周期：
- 康德拉季耶夫长波（50-60 年）
- 朱格拉中周期（8-10 年，设备投资）
- 基钦短周期（3-4 年，库存）
- 库兹涅茨周期（15-25 年，房地产）

```bash
python scripts/cycle_phase_evaluator.py --report      # 生成共振报告
python scripts/cycle_phase_evaluator.py --resonance   # 显示共振结果
```

**`scripts/market_indicators.py`** — 市场指标系统

多维度市场状态评估（数据可从 `model_params.json` 更新）：
- 估值指标：PE/PB 分位、E/P、股债利差
- 情绪指标：波动率、融资余额、新发基金
- 流动性指标：M2 增速、社融增速、国债收益率
- 商品指标：CRB 指数、黄金、原油、美元指数

```bash
python scripts/market_indicators.py --summary   # 综合判断
python scripts/market_indicators.py --report    # 完整报告
```

### Layer 3: 资产配置 + ETF 甄选

**`scripts/asset_allocator.py`** — 资产配置系统

四阶段资产配置矩阵：

| 阶段 | 股票 | 债券 | 商品 | 黄金 | 现金 | 防御 |
|------|------|------|------|------|------|------|
| 复苏期 | 40% | 20% | 25% | 12% | 8% | 8% |
| 繁荣期 | 50% | 15% | 20% | 8% | 7% | 8% |
| 衰退期 | 25% | 35% | 15% | 12% | 13% | 15% |
| 萧条期 | 15% | 35% | 10% | 20% | 25% | 15% |

```bash
python scripts/asset_allocator.py --report        # 生成配置报告
python scripts/asset_allocator.py --allocation    # 显示配置方案
```

**`scripts/etf_selector.py`** — 🆕 ETF 多维度甄选系统

基于 5 大维度对候选 ETF 量化评分，输出最优投资组合：

| 维度 | 权重 | 评分逻辑 |
|------|------|----------|
| 周期定位匹配度 | 20% | 康波复苏期受益程度 |
| 十五五政策匹配度 | 25% | 与国家重点产业契合度 |
| 地缘政治韧性 | 20% | 中美脱钩/台海风险下的抗压能力 |
| 市场估值合理性 | 20% | PE/PB 分位 + E/P 格雷厄姆指标 |
| 盈利景气度 | 15% | 行业增长预期、业绩确定性 |

- 候选池：50+ 只 ETF（宽基/港股/QDII/科技/新能源/医药/军工/金融/消费/商品/防御/债券）
- 组合约束：强制保留宽基和防御类至少各 1 只
- 实时估值：通过 `valuation_fetcher.py` 获取最新 PE/PB 并覆盖候选数据

```bash
python scripts/etf_selector.py --evaluate        # 评估候选池（全排名）
python scripts/etf_selector.py --select          # 筛选最优组合
python scripts/etf_selector.py --compare         # 对比新旧组合
python scripts/etf_selector.py --update-config   # 更新 portfolio_config.json
```

### 政策与宏观环境分析

**`scripts/policy_analyzer.py`** — 政策分析系统

结合中国政策大势与国际环境，提供政策面投资指引：

- **十五五规划**：六大未来产业 + 六大新兴支柱产业投资映射
- **大宗商品**：铜/黄金/原油/锂/铝供需分析与价格预测
- **美联储政策**：利率、缩表、降息预期、主席换届跟踪
- **中国货币政策**：LPR、降准、结构性工具
- **地缘政治**：中美博弈、中东局势（霍尔木兹封锁）、OPEC+ 分裂、台海风险

```bash
python scripts/policy_analyzer.py --report    # 生成政策分析报告
python scripts/policy_analyzer.py --summary   # 显示分析摘要
```

### Layer 4: 策略决策引擎

**`scripts/strategy_engine.py`** — 统一决策输出

整合所有模块（康波→共振→市场→资产配置→政策→ETF甄选），输出完整策略决策报告：
- 宏观周期定位 + 周期共振分析
- 政策综合评分及仓位修正
- 资产配置方案 + 关键赛道推荐
- 进入/退出策略 + 4% 定投法状态
- 风险管理清单 + 关键风险与机会
- 操作待办清单（本周/月度）

```bash
python scripts/strategy_engine.py --report      # 生成完整策略报告
python scripts/strategy_engine.py --decision    # 显示决策摘要
```

### Layer 5: 4% 定投法执行与回测

**`scripts/four_percent_model.py`** — 核心定投模型

基于 B站UP主"研究员雷牛牛"强化版理论（修正版），包含三种策略对比回测：

| 参数 | 值 | 说明 |
|------|-----|------|
| **总份数** | **25份** | 总资金平均分 25 份 |
| **单标的上限** | **10份** | 同一只基金最多 10 份（40%） |
| **触发基准** | **上一个买入点** | 从上次买入价下跌触发（非 2 年低点） |
| **触发跌幅** | 4% | 下跌 ≥4% 触发买入 1 份 |
| **买入过滤** | E/P > 10% | 格雷厄姆低估线 |
| **卖出条件** | E/P < 6.4% | 格雷厄姆高估线 |
| **等待纪律** | 严格 | 未跌穿 4% 绝不提前买入 |

**改进版额外特性**：
- 动态买入倍率（根据 E/P：0.5x-3x）
- 分层止盈（15%/25%/35%）+ 移动止盈（高点回撤 10%）
- 右侧补仓（E/P > 12% 且连续涨 3 天）

```bash
# 回测单个标的
python scripts/four_percent_model.py --backtest 510300 --start 2022-01-01 --capital 100000

# 回测所有配置标的
python scripts/four_percent_model.py --backtest-all
```

### 每日监控

**`scripts/investment_monitor.py`** — 投资组合监控

功能：
1. 拉取 ETF 实时行情（东方财富 push2 API，市场前缀自动匹配）
2. 加载本地历史缓存并追加当日价格
3. 计算价格分位（2 年窗口）和 E/P 代理值
4. 检查 4% 定投法触发条件 + 仓位偏离度
5. 检查组合止损/单标止损/止盈信号
6. 输出每日信号报告（含宏观周期定位）

```bash
# 每日监控
python scripts/investment_monitor.py

# 初始化历史数据缓存（需 akshare）
python scripts/investment_monitor.py --init-history --force
```

报告输出：`data/signals/signal_report_YYYYMMDD.md`

详细说明：[`scripts/README_MONITOR.md`](scripts/README_MONITOR.md)

### 实时估值获取

**`scripts/valuation_fetcher.py`** — 🆕 指数估值数据获取

- 从东方财富 API 拉取沪深300/中证500/科创50/恒生科技等 11 个指数的实时 PE/PB
- 本地缓存 6 小时 TTL，避免频繁请求
- `apply_valuations_to_candidates()` 将实时估值合并到 ETF 候选池
- 被 `etf_selector.py` 自动调用，网络不可用时静默回退

### 研究更新驱动器

**`scripts/research_driver.py`** — 🆕 自动化研究迭代

闭环流程：收集系统状态 → 对比外部信息 → 生成修改清单 → 执行代码修改 → 验证 → git commit/push → 输出更新报告

```bash
python scripts/research_driver.py --auto                          # 自动模式（定时任务）
python scripts/research_driver.py --manual                        # 手动模式（交互式）
python scripts/research_driver.py --prompt "更新美联储利率判断"    # 指定主题
```

---

## 测试

```bash
# 安装依赖
pip install pytest pandas numpy

# 运行全部测试（21 个用例）
python -m pytest tests/ -v

# 仅运行 4% 定投法测试
python -m pytest tests/test_four_percent_model.py -v
```

测试覆盖：
- `calc_ep_proxy`：短历史默认值、低价高 E/P 逻辑
- `FourPercentModel`：首次观察、4% 触发、E/P 过滤、后续买入、强制卖出、10 份上限
- `EnhancedFourPercentModel`：分层止盈、移动止盈、动态倍率（3x）
- `MonthlyDcaModel`：月度定投基准
- 边界情况：零价格、空历史、现金约束

---

## 投资组合配置

当前配置基于 ETF 多维度甄选模型（2026-05-01 评分），14 只 ETF，总规模 90 万元：

| 类型 | ETF | 代码 | 目标权重 | 甄选理由 |
|------|-----|------|---------|----------|
| 实物资产 | 黄金 ETF | 518880 | 12.6% | 地缘避险首选 + 央行购金 + 去美元化 |
| 硬科技核心 | 芯片 ETF | 159995 | 10.4% | 十五五集成电路支柱 + 国产替代 |
| 硬科技核心 | 创新药 ETF | 159992 | 10.4% | 生物医药新兴支柱 + 一季报超预期 |
| 硬科技核心 | 机器人 ETF | 562500 | 8.3% | 具身智能未来产业 + AI 应用落地 |
| 硬科技核心 | 科创 50 ETF | 588000 | 8.3% | 硬科技综合载体 + 十五五核心赛道 |
| 硬科技核心 | 医疗器械 ETF | 159898 | 8.3% | 高端医疗器械国产替代 |
| 实物资产 | 有色金属 ETF | 512400 | 7.3% | 实物资产主线接力（铜铝紧缺） |
| AI 与科技 | 人工智能 ETF | 159819 | 6.2% | AI 产业链 + 十五五未来产业 |
| AI 与科技 | 科技 ETF | 515880 | 6.2% | 泛科技综合（电子/计算机/通信） |
| 新能源 | 光伏 ETF | 159857 | 5.2% | 新型储能支柱 + 光伏平价 |
| 新能源 | 新能源车 ETF | 515030 | 4.2% | 电动车出口高增 |
| 新能源 | 电池 ETF | 159755 | 4.2% | 储能临界点 + 固态电池突破 |
| 防御卫星 | 红利低波 ETF | 512890 | 4.2% | 高股息防御 + 新国九条鼓励分红 |
| 防御卫星 | 中证 A500 ETF | 560610 | 4.2% | 中大盘均衡底仓 |

---

## 2026 年核心判断（2026-05-06 更新）

### 周期面
1. **康波定位**：第六轮康波复苏期起点（2026-2035），AI + 新能源为核心引擎
2. **周期共振**：康波复苏 + 朱格拉复苏 + 基钦补库存 = 三周期同向，中共振偏强
3. **市场状态**：沪深300 PE 14.6（分位 86%），PB 1.46（分位 57%），E/P 6.8%；A股节后首日硬科技爆发：芯片ETF +8.35%，科创50 +7.38%

### 政策面
4. **政治局定调**：4·28 会议首次将"稳定和增强资本市场信心"升至战略高度，定性"信心建设战"
5. **十五五规划**：六大未来产业 + 六大新兴支柱产业，六张网投资超 7 万亿
6. **美联储**：维持 3.50%-3.75%（4/29 FOMC 8:4 分歧，1992 年来最高），鲍威尔 5/15 卸任，沃什接任
7. **中国央行**：适度宽松，5/6 开展 3000 亿买断式逆回购（3 个月），全年预计 1-2 次降准降息

### 大宗商品（5 月 6 日更新）
8. **黄金**：4558 美元/盎司（5/6 企稳反弹+0.8%，走出一个月低谷，从 4555 回升），年内目标 5000，摩根大通目标 6300
9. **原油**：Brent 109.87 美元/桶（5/6 停火维持油价-4%回落），WTI 102.27 美元，年内目标 115
10. **铜**：LME 11700 美元/吨，铜矿紧缺 + 新能源需求 + 冶炼厂检修，年内目标 12000
11. **美元指数**：DXY 98.3，停火维持+伊朗外长访华外交斡旋→避险需求边际降温但仍在高位

### 地缘政治（5 月 6 日更新）
12. **美伊停火**：5/5-6 美防长确认停火有效；美军护航两艘商船成功穿越霍尔木兹海峡
13. **伊朗新战略**：启动海峡通行管理新机制，声称"通行须获伊朗许可"；伊朗外长 5/6 访华斡旋
14. **中美**：关税整体休战但半导体 232 关税延续；商务部发布阻断禁令反制美国涉伊朗制裁

### 策略方向
15. **核心赛道**：芯片/AI/科创（超配，美股芯片暴涨+A股节后硬科技爆发）→ 黄金（超配 12-15%）→ 有色（标配）→ 能化（降仓至标配，油价回落）
16. **仓位建议**：中高仓位（50-70%），停火维持风险偏好改善，但仍需保持现金储备
17. **4% 定投法**：启用，震荡市特征明显；节后首日不追涨，等回踩确认

---

## 数据来源

- 东方财富 push2 API（A股 ETF 实时行情 + 指数估值 PE/PB）
- akshare（历史 K 线数据补充）
- Alpha Vantage（美股/全球股票）
- Yahoo Finance（美股/港股/基金）

## 文档体系

| 文档 | 内容 |
|------|------|
| `reports/操作说明.md` | **三大用户触发功能完整工作流（本系统对话入口）** |
| `reports/OPERATION_MANUAL.md` | 命令行/脚本技术操作手册 |
| `reports/four_percent_strategy_guide.md` | 4% 定投法完整策略手册（修正版） |
| `papers/康波周期深度研究报告.md` | 康波周期理论研究 |
| `reports/macro_cycle_report_YYYYMMDD.md` | 宏观周期定位报告 |
| `reports/cycle_resonance_report_YYYYMMDD.md` | 周期共振分析报告 |
| `reports/market_indicators_YYYYMMDD.md` | 市场指标综合报告 |
| `reports/asset_allocation_YYYYMMDD.md` | 资产配置决策报告 |
| `reports/etf_evaluation_YYYYMMDD.md` | ETF 多维度甄选评估报告 |
| `reports/etf_portfolio_YYYYMMDD.md` | ETF 甄选组合配置方案 |
| `reports/strategy_decision_YYYYMMDD.md` | 策略决策报告 |
| `reports/policy_analysis_YYYYMMDD.md` | 政策与宏观环境分析报告 |
| `reports/research_YYYYMMDD.md` | F1 模型迭代日志 |
| `reports/advice_YYYYMMDD.md` | F2 持仓建议报告（已 gitignore） |
| `reports/portfolio_review/` | F3 周报/月报目录（已 gitignore） |
| `data/signals/signal_report_YYYYMMDD.md` | 每日监控报告 |
| `data/positions/positions_YYYYMMDD.json` | F2 持仓快照（已 gitignore） |

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

## 服务器部署（OpenClaw + CC CLI）

本系统支持部署到 Ubuntu 服务器，由 OpenClaw 驱动，Claude Code CLI 管理：

### 快速部署（code-server 终端）

```bash
# 1. 登录 code-server（http://192.168.50.6:8080），打开终端
# 2. 下载并执行部署脚本
curl -fsSL https://raw.githubusercontent.com/lorrin328/stockmoney/main/deploy/deploy.sh -o /tmp/deploy.sh
bash /tmp/deploy.sh

# 3. 配置消息平台（Telegram/Slack）
nano /opt/openclaw/.env
# 添加 TELEGRAM_BOT_TOKEN 和 TELEGRAM_CHAT_ID

# 4. 启动 OpenClaw
cd /opt/openclaw && pnpm gateway:start

# 5. 在 Telegram 中发送"帮助"测试
```

### 部署后可用命令（消息平台）

| 命令 | 功能 |
|------|------|
| `帮助` | 显示可用命令 |
| `今日信号` | ETF 监控 + 4% 定投触发 |
| `策略` / `决策` | 策略决策摘要 |
| `推荐` / `买什么` | 标的推荐与仓位建议 |
| `政策` / `宏观` | 政策与宏观环境分析 |
| `完整报告` | 生成详细策略报告 |
| `研究` / `更新` | CC CLI 自动更新研究模块 |

### 定时推送（自动）

- **工作日 9:25** — 盘前监控
- **工作日 15:05** — 盘后监控
- **每日 20:00** — 策略摘要
- **每周一 9:30** — 周度策略报告
- **每月 1 日** — 政策分析 + 全量报告

详细部署指南：[deploy/README_DEPLOY.md](deploy/README_DEPLOY.md)

---

## 使用方式

### 完整决策流程

```bash
# 1. 生成宏观周期报告
python scripts/kondratiev_model.py --report

# 2. 生成周期共振报告
python scripts/cycle_phase_evaluator.py --report

# 3. 生成市场指标报告
python scripts/market_indicators.py --report

# 4. 生成政策分析报告（十五五 + 大宗商品 + 美联储 + 地缘）
python scripts/policy_analyzer.py --report

# 5. 生成 ETF 甄选评估（5 因子评分）
python scripts/etf_selector.py --evaluate

# 6. 生成资产配置报告
python scripts/asset_allocator.py --report

# 7. 生成统一策略报告（整合以上所有）
python scripts/strategy_engine.py --report

# 8. 每日监控（含 4% 定投信号）
python scripts/investment_monitor.py
```

### 快速查看决策摘要

```bash
python scripts/strategy_engine.py --decision
```

### 更新模型参数

```bash
# 编辑 data/model_params.json 后运行回测验证
python scripts/four_percent_model.py --backtest-all

# 如果参数变更影响 ETF 评分，更新组合配置
python scripts/etf_selector.py --update-config
```

## 风险提示

1. **康波周期争议**：学术上存在争议，不应作为唯一决策依据
2. **周期识别滞后性**：周期拐点判断通常滞后 2-5 年
3. **政策干预**：各国央行政策可能改变周期运行轨迹
4. **4% 定投法局限**：单边上涨市会严重踏空；需要极强纪律性接受大量现金闲置
5. **地缘政治黑天鹅**：中东冲突（霍尔木兹封锁）、台海风险可能引发剧烈波动
6. **估值代理局限**：ETF 无直接 E/P 数据，使用价格分位反向映射作为代理，存在误差
7. **历史不代表未来**：回测基于历史数据，市场环境变化可能导致策略失效

> **本系统仅为研究参考，不构成投资建议。投资有风险，入市需谨慎。**

## License

MIT
