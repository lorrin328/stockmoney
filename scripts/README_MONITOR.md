# Investment Monitor 使用说明

## 快速开始

### 1. 每日运行监控（获取实时行情 + 生成信号报告）

```bash
python scripts/investment_monitor.py
```

输出：
- 实时行情：14只ETF的当前价格和涨跌
- 信号检查：加仓/减仓/止盈/再平衡信号
- 报告文件：`data/signals/signal_report_YYYYMMDD.md`

### 2. 初始化历史数据（仅需一次）

网络正常时运行：
```bash
python scripts/investment_monitor.py --init-history
```

若某只标的历史数据损坏/缺失，强制重新获取：
```bash
python scripts/investment_monitor.py --init-history --force
```

### 3. 历史数据补充方式

**方式A：akshare自动获取（推荐，需网络正常）**
```bash
python scripts/investment_monitor.py --init-history
```

**方式B：从券商APP手动导出**
1. 打开券商APP（如华泰、中信、东方财富）
2. 进入每只ETF的K线页面
3. 导出历史数据为CSV
4. 放入 `data/history/` 目录，文件命名为 `{code}_history.csv`
5. CSV格式要求：至少包含 `date` 和 `close` 两列

**方式C：每日自动累积**
- 脚本每天会自动将当日价格追加到缓存
- 连续运行约500个交易日（2年）后，自然形成完整历史数据

### 4. 录入持仓（用于偏离度和止盈检查）

编辑 `data/portfolio_config.json`，在 `positions` 字段中添加：

```json
"positions": {
  "510300": {"shares": 1000, "cost": 4.50, "date": "2026-04-01"},
  "159857": {"shares": 2000, "cost": 0.85, "date": "2026-04-01"}
}
```

- `shares`: 持有份额
- `cost`: 成本价（用于计算浮盈）
- `date`: 买入日期

### 5. 调整阈值规则

编辑 `data/portfolio_config.json` 中各标的的 `rules` 字段：

```json
"rules": [
  {"kind": "price_percentile", "window": 500, "low": 0.20, "high": 0.80}
]
```

规则类型：
- `price_percentile`: 价格分位规则（需历史数据）
  - `window`: 计算分位的历史窗口（交易日数）
  - `low`: 分位低于此值触发加仓（默认20%）
  - `high`: 分位高于此值触发减仓（默认80%）
- `price_threshold`: 绝对价格阈值（无需历史数据）
  - `low`: 价格低于此值触发加仓
  - `high`: 价格高于此值触发减仓

## 文件说明

| 文件 | 用途 |
|------|------|
| `scripts/investment_monitor.py` | 主监控脚本 |
| `data/portfolio_config.json` | 投资组合配置（标的、仓位、规则、持仓） |
| `data/history/{code}_history.csv` | 各标的历史净值缓存 |
| `data/signals/signal_report_YYYYMMDD.md` | 每日信号报告 |

## 信号类型

| 优先级 | 类型 | 触发条件 | 操作建议 |
|--------|------|----------|----------|
| 1 | 加仓 | 价格分位<=20% 或 触及低价阈值 | 加倍定投 |
| 1 | 止盈 | 浮盈>=50% | 卖出盈利部分 |
| 2 | 减仓 | 价格分位>=80% 或 触及高价阈值 | 暂停定投/卖出 |
| 3 | 加仓/减仓 | 实际仓位偏离目标>=10% | 再平衡 |

## 注意事项

1. 本脚本基于公开API获取数据，**不构成投资建议**
2. 历史数据用于计算估值分位，数据量不足时部分信号无法生成
3. 定投计划金额需根据个人资金状况调整
4. 建议结合市场大势和政策面综合判断
