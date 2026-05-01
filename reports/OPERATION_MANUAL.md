# StockMoney 投资决策系统 - 操作方法手册

> 版本: v1.0
> 更新日期: 2026-05-01
> 适用对象: 本系统使用者

---

## 目录

1. [系统概述](#一系统概述)
2. [环境准备](#二环境准备)
3. [日常操作流程](#三日常操作流程)
4. [模块详细用法](#四模块详细用法)
5. [投资决策流程](#五投资决策流程)
6. [定期维护任务](#六定期维护任务)
7. [常见问题](#七常见问题)
8. [风险提示](#八风险提示)

---

## 一、系统概述

本系统是一个基于康波周期理论的五层投资决策体系，整合宏观周期、市场指标、政策分析、资产配置和量化执行策略。

### 系统架构

```
Layer 1: 康波周期定位 (kondratiev_model.py)       -> 50-60年战略方向
Layer 2: 周期共振+市场指标                        -> 3-20年战术判断
         (cycle_phase_evaluator.py + market_indicators.py)
Layer 3: 资产配置决策 (asset_allocator.py)        -> 资产类别权重
Layer 4: 策略决策引擎 (strategy_engine.py)        -> 统一决策报告
Layer 5: 4%定投法执行 (four_percent_model.py)      -> 具体操作信号
+
policy_analyzer.py -> 政策面分析（十五五/大宗商品/美联储）
investment_monitor.py -> 每日实时监控
```

### 核心文件位置

| 文件 | 路径 | 用途 |
|------|------|------|
| 系统配置 | `data/portfolio_config.json` | ETF组合配置 |
| 历史数据 | `data/history/` | ETF历史净值缓存 |
| 每日信号 | `data/signals/` | 每日监控报告 |
| 研究报告 | `reports/` | 各类分析报告 |
| 深度研究 | `papers/` | 理论研究资料 |

---

## 二、环境准备

### 2.1 Python环境

```bash
# 推荐Python 3.10+
python --version

# 安装依赖
pip install numpy pandas requests

# 可选（用于获取历史数据）
pip install akshare
```

### 2.2 初始化历史数据

首次使用或需要补充数据时：

```bash
cd stockmoney

# 初始化所有标的的历史数据（需要网络连接）
python scripts/investment_monitor.py --init-history

# 强制重新获取（覆盖已有缓存）
python scripts/investment_monitor.py --init-history --force
```

**数据说明**：
- 历史数据缓存在 `data/history/` 目录下，文件名为 `{code}_history.csv`
- 如果akshare不可用，可以从券商APP导出历史净值CSV，放入 `data/history/` 目录
- CSV格式要求：包含 `date` 和 `close` 两列

### 2.3 配置投资组合

编辑 `data/portfolio_config.json`：

```json
{
  "total_capital": 900000,
  "holdings": [
    {"code": "510300", "name": "沪深300ETF", "target_pct": 11.1, ...},
    ...
  ],
  "positions": {
    "510300": {"shares": 0, "cost": 0, "last_buy_price": 0}
  }
}
```

**positions字段说明**：
- `shares`: 持仓份额
- `cost`: 成本价
- `last_buy_price`: 上次买入价（4%定投法触发基准）

---

## 三、日常操作流程

### 3.1 每日必做（约5分钟）

```bash
# 1. 运行每日监控
python scripts/investment_monitor.py
```

输出：`data/signals/signal_report_YYYYMMDD.md`

**重点查看**：
- 4%定投法触发信号（买入/卖出/等待）
- 估值分位（是否低估/高估）
- E/P代理值（是否达标）
- 宏观周期定位（康波/朱格拉/基钦阶段）

### 3.2 每周必做（约10分钟）

```bash
# 2. 生成策略决策报告
python scripts/strategy_engine.py --report
```

输出：`reports/strategy_decision_YYYYMMDD.md`

**重点查看**：
- 康波阶段与周期共振
- 建议仓位区间
- 关键赛道推荐
- 进入/退出策略
- 风险管理措施

### 3.3 每月必做（约30分钟）

```bash
# 3. 更新政策分析
python scripts/policy_analyzer.py --report

# 4. 更新市场指标
python scripts/market_indicators.py --report

# 5. 更新资产配置
python scripts/asset_allocator.py --report
```

### 3.4 每季度必做

- [ ] 检查资产配置偏离度（偏离>=5%触发再平衡）
- [ ] 复盘上季度操作，检查止损/止盈执行
- [ ] 更新周期阶段判断
- [ ] 检查持仓标的的基本面变化

---

## 四、模块详细用法

### 4.1 政策分析 (policy_analyzer.py)

**功能**：综合分析中国政策大势与国际环境

**用法**：
```bash
# 生成完整报告
python scripts/policy_analyzer.py --report

# 快速摘要
python scripts/policy_analyzer.py --summary
```

**输出**：
- 政策综合评分（-100到+100）
- 十五五规划产业映射
- 大宗商品配置建议
- 美联储/中国央行政策跟踪
- 行业推荐（核心推荐/防御配置/机会关注）

### 4.2 策略引擎 (strategy_engine.py)

**功能**：整合所有模块，输出统一策略决策

**用法**：
```bash
# 生成完整策略报告
python scripts/strategy_engine.py --report

# 快速决策摘要
python scripts/strategy_engine.py --decision

# 指定年份
python scripts/strategy_engine.py --decision --year 2027
```

**输出内容**：
1. 宏观周期定位（康波+共振+市场指标）
2. 政策与宏观环境分析
3. 资产配置决策
4. 执行策略（进入/退出/4%定投）
5. 风险管理
6. 关键风险与机会
7. 操作清单

### 4.3 每日监控 (investment_monitor.py)

**功能**：实时监控14只ETF，生成操作信号

**用法**：
```bash
# 日常监控
python scripts/investment_monitor.py

# 初始化历史数据
python scripts/investment_monitor.py --init-history
```

**报告结构**：
1. 宏观周期定位（康波/朱格拉/基钦）
2. 今日信号摘要（紧急/关注/提示）
3. 持仓概览（现价/仓位/浮盈/信号）
4. 估值分位详情（2年最低/最高/分位/判断）
5. 4%定投法策略建议
6. 本月定投计划

### 4.4 康波模型 (kondratiev_model.py)

**用法**：
```bash
python scripts/kondratiev_model.py --report    # 完整报告
python scripts/kondratiev_model.py --phase     # 当前阶段
```

### 4.5 周期评估 (cycle_phase_evaluator.py)

**用法**：
```bash
python scripts/cycle_phase_evaluator.py --report      # 共振报告
python scripts/cycle_phase_evaluator.py --resonance   # 共振摘要
```

### 4.6 市场指标 (market_indicators.py)

**用法**：
```bash
python scripts/market_indicators.py --summary   # 综合判断
python scripts/market_indicators.py --report    # 完整报告
```

### 4.7 资产配置 (asset_allocator.py)

**用法**：
```bash
python scripts/asset_allocator.py --report        # 配置报告
python scripts/asset_allocator.py --allocation    # 配置摘要
```

### 4.8 4%定投模型 (four_percent_model.py)

**用法**：
```bash
# 回测单个标的
python scripts/four_percent_model.py --backtest 510300 --start 2022-01-01 --capital 100000

# 回测所有配置标的
python scripts/four_percent_model.py --backtest-all
```

---

## 五、投资决策流程

### 5.1 完整决策流程（月度）

```
步骤1: 政策分析
  └── python scripts/policy_analyzer.py --report
  └── 判断：政策面是否有重大变化？
      ├── 十五五规划新动向？
      ├── 美联储政策转向？
      └── 大宗商品供需变化？

步骤2: 周期定位
  └── python scripts/kondratiev_model.py --phase
  └── python scripts/cycle_phase_evaluator.py --resonance
  └── 判断：当前处于什么阶段？
      ├── 康波阶段：复苏/繁荣/衰退/萧条
      ├── 共振强度：强/中/弱
      └── 建议仓位：高/中/低

步骤3: 市场验证
  └── python scripts/market_indicators.py --summary
  └── 判断：市场指标是否支持周期判断？
      ├── 估值：低估/合理/高估
      ├── 情绪：恐慌/中性/贪婪
      └── 流动性：宽松/中性/紧缩

步骤4: 资产配置
  └── python scripts/asset_allocator.py --allocation
  └── 根据周期阶段确定资产权重

步骤5: 统一决策
  └── python scripts/strategy_engine.py --decision
  └── 整合所有信息，输出最终决策

步骤6: 执行操作
  └── python scripts/investment_monitor.py
  └── 检查4%定投触发条件
  └── 执行买入/卖出/等待
```

### 5.2 4%定投法操作流程

**首次使用**：
1. 选择标的：成立>7年的宽基指数ETF
2. 判断估值：确认E/P > 10%（可用监控系统的E/P代理值）
3. 设定观察价：记录当前价格为观察基准
4. 等待触发：等待价格跌到观察价 x 0.96
5. 触发买入：买入1份（总资金的1/25）
6. 更新基准：新的触发线变为买入价 x 0.96
7. 重复等待：等待下一次触发

**持仓管理**：
```
持仓状态：
  - 记录last_buy_price（上次买入价）
  - 计算触发线 = last_buy_price x 0.96
  - 每日检查：当前价 <= 触发线？
    - 是 -> 检查E/P > 10%？
      - 是 -> 买入1份
      - 否 -> 继续等待
    - 否 -> 继续等待
  - 同时检查E/P < 6.4%？
    - 是 -> 全部卖出
    - 否 -> 持有
```

---

## 六、定期维护任务

### 6.1 每日（自动运行）

- [ ] 运行 `python scripts/investment_monitor.py`
- [ ] 查看 `data/signals/signal_report_YYYYMMDD.md`
- [ ] 检查是否有4%定投触发信号

### 6.2 每周

- [ ] 运行 `python scripts/strategy_engine.py --decision`
- [ ] 检查策略方向是否需要调整
- [ ] 关注重大政策/市场事件

### 6.3 每月（月初）

- [ ] 运行 `python scripts/policy_analyzer.py --report`
- [ ] 运行 `python scripts/market_indicators.py --report`
- [ ] 执行定投计划（5万元）
- [ ] 更新持仓成本/份额记录
- [ ] 复盘上月操作

### 6.4 每季度

- [ ] 运行完整决策流程（所有模块）
- [ ] 检查资产配置偏离度（>=5%再平衡）
- [ ] 更新 `data/portfolio_config.json` 中的positions
- [ ] 评估是否需要调整标的/权重

### 6.5 每年

- [ ] 全面复盘年度收益/回撤
- [ ] 评估策略有效性
- [ ] 更新投资目标和风险承受能力
- [ ] 检查标的是否需要替换

---

## 七、常见问题

### Q1: 4%定投法在什么市场环境下表现最好？

**A**: 震荡市、下跌市、筑底期表现最佳。单边上涨市容易踏空。

### Q2: 为什么回测显示0交易？

**A**: 在2024年9月-2026年4月的单边上涨市中，4%定投法因纪律性等待下跌触发而0交易，这是策略设计的正常表现。

### Q3: E/P代理值准确吗？

**A**: ETF无直接E/P数据，使用价格分位反向映射作为代理值，可能与实际E/P有偏差。建议结合PE/PB估值综合判断。

### Q4: 康波周期判断可靠吗？

**A**: 康波周期在学术界存在争议，拐点判断通常滞后2-5年。本系统仅将其作为长期战略参考，不应作为唯一决策依据。

### Q5: 没有akshare怎么办？

**A**: 可以从券商APP导出历史净值CSV，放入 `data/history/` 目录。格式要求包含 `date` 和 `close` 两列。

### Q6: 如何更新持仓信息？

**A**: 编辑 `data/portfolio_config.json` 中的 `positions` 字段：
```json
"positions": {
  "510300": {"shares": 1000, "cost": 3.5, "last_buy_price": 3.8}
}
```

### Q7: 报告中的emoji显示乱码？

**A**: Windows控制台编码问题，不影响报告文件本身。报告文件使用UTF-8编码，用VS Code等编辑器打开即可正常显示。

---

## 八、风险提示

1. **模型风险**：本系统基于历史数据和理论模型，市场环境变化可能导致策略失效
2. **周期识别滞后**：康波周期拐点判断通常滞后2-5年
3. **政策干预**：各国央行政策可能改变周期运行轨迹
4. **4%定投局限**：单边上涨市会严重踏空
5. **数据准确性**：E/P代理值、价格分位等可能存在偏差
6. **地缘政治**：战争、制裁等突发事件可能颠覆所有模型预测
7. **流动性风险**：极端市场条件下可能无法按预期价格成交

> **本系统仅为研究参考，不构成投资建议。投资有风险，入市需谨慎。**
> **请勿将全部资金投入单一策略，建议分散配置。**
> **过往业绩不代表未来表现。**

---

*本手册基于系统v1.0编写，随着系统迭代更新，请以最新版本为准。*
