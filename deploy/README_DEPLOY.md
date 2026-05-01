# StockMoney 服务器部署指南

> 部署环境: Ubuntu + OpenClaw + Claude Code CLI
> 部署方式: code-server终端一键部署
> 更新日期: 2026-05-01

---

## 快速开始（3分钟完成）

### 方式1：code-server终端一键部署（推荐）

1. **登录您的code-server**（http://192.168.50.6:8080）
2. **打开终端**（Terminal → New Terminal）
3. **复制粘贴以下命令**：

```bash
# 下载部署脚本
curl -fsSL https://raw.githubusercontent.com/lorrin328/stockmoney/main/deploy/deploy.sh -o /tmp/deploy.sh

# 执行部署
bash /tmp/deploy.sh
```

### 方式2：手动复制部署

如果您的服务器无法访问GitHub：

1. 在本机下载 [`deploy.sh`](deploy.sh)
2. 上传到code-server的任意目录
3. 在终端执行：`bash deploy.sh`

---

## 部署完成后配置

### 1. 配置消息平台（必填）

编辑OpenClaw环境变量：

```bash
nano /opt/openclaw/.env
```

添加以下内容（以Telegram为例）：

```env
# Telegram配置
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here

# 可选：Slack配置
SLACK_BOT_TOKEN=xoxb-your-token
SLACK_CHANNEL_ID=Cxxxxx
```

**获取Telegram Bot Token：**
1. 在Telegram中搜索 @BotFather
2. 发送 `/newbot` 创建新Bot
3. 复制提供的Token

**获取Chat ID：**
1. 向Bot发送一条消息
2. 访问 `https://api.telegram.org/bot<Token>/getUpdates`
3. 找到 `"chat":{"id":123456789` 中的数字

### 2. 启动OpenClaw

```bash
cd /opt/openclaw
pnpm gateway:start
```

### 3. 验证部署

在Telegram中向Bot发送：
```
帮助
```

如果返回帮助信息，说明部署成功！

---

## 系统架构

```
用户消息 (Telegram/Slack)
    |
    v
OpenClaw Gateway (端口3000)
    |
    +-- Cron定时器 --+-- 交易日9:25 盘前监控
    |                 +-- 交易日15:05 盘后监控
    |                 +-- 每日20:00 策略摘要
    |                 +-- 每周一9:30 周度报告
    |                 +-- 每月1日 政策分析
    |
    +-- 用户命令解析 --+-- "今日信号" → investment_monitor.py
    |                  +-- "策略" → strategy_engine.py
    |                  +-- "推荐" → strategy_engine.py --decision
    |                  +-- "政策" → policy_analyzer.py
    |                  +-- "研究" → CC CLI研究更新
    |
    v
Python脚本执行 (/opt/stockmoney/scripts/)
    |
    v
报告生成 → 消息推送
```

---

## 可用命令

在消息平台向Bot发送以下命令：

| 命令 | 功能 | 响应速度 |
|------|------|---------|
| `帮助` | 显示可用命令 | 即时 |
| `今日信号` | ETF监控信号+4%定投触发 | ~10秒 |
| `策略` / `决策` | 策略决策摘要 | ~15秒 |
| `推荐` / `买什么` | 标的推荐与仓位建议 | ~15秒 |
| `政策` / `宏观` | 政策与宏观环境分析 | ~10秒 |
| `商品` / `黄金` | 大宗商品分析 | ~10秒 |
| `周期` / `康波` | 周期共振分析 | ~10秒 |
| `市场` / `估值` | 市场指标综合判断 | ~10秒 |
| `配置` / `仓位` | 资产配置方案 | ~10秒 |
| `完整报告` | 生成详细策略报告 | ~20秒 |
| `研究` / `更新` | CC CLI研究更新模块 | ~2-5分钟 |

---

## 定时任务说明

部署后，以下任务将自动运行：

| 时间 | 频率 | 任务 | 输出 |
|------|------|------|------|
| 工作日 9:25 | 每日 | 盘前监控 | 信号摘要 |
| 工作日 15:05 | 每日 | 盘后监控 | 信号摘要 |
| 每日 20:00 | 每日 | 策略摘要 | 决策建议 |
| 每周一 9:00 | 每周 | 周期共振分析 | 共振强度 |
| 每周一 9:30 | 每周 | 周度策略报告 | 完整报告 |
| 每月1日 9:00 | 每月 | 政策分析 | 政策报告 |
| 每月1日 9:30 | 每月 | 全量分析 | 策略报告 |
| 每周三 20:00 | 每周 | CC CLI研究更新 | 模块更新 |

---

## Claude Code CLI 的作用

CC CLI在系统中的职责：

1. **研究更新**（每周自动）：根据最新政策、研究报告，更新Python脚本中的分析逻辑和数据
2. **复杂决策**：在用户请求深度分析时，CC CLI进行多因素综合推理
3. **模块完善**：发现bug或需要新功能时，CC CLI自动修复和增强代码
4. **自然语言报告**：将量化分析结果转化为自然语言解读

**日常使用**：大部分查询由Python脚本直接处理（快速），仅在"研究更新"时调用CC CLI（较慢但更深入）。

---

## 目录结构（部署后）

```
/opt/
├── stockmoney/                 # 投资分析模块
│   ├── scripts/               # Python脚本
│   │   ├── strategy_engine.py
│   │   ├── policy_analyzer.py
│   │   ├── investment_monitor.py
│   │   └── ...
│   ├── data/
│   │   ├── history/           # ETF历史数据
│   │   └── signals/           # 每日信号报告
│   ├── reports/               # 生成的报告
│   ├── logs/                  # 运行日志
│   └── openclaw/              # OpenClaw集成脚本
│       ├── run_cc_cli.sh
│       ├── run_python.sh
│       └── help.txt
│
└── openclaw/                  # OpenClaw框架
    ├── integrations/
    │   └── stockmoney/        # StockMoney配置
    │       ├── cron.yaml      # 定时任务
    │       └── commands.yaml  # 用户命令映射
    └── ...
```

---

## 常见问题

### Q1: 部署脚本执行失败？

**A**: 检查是否有sudo权限。如果没有，请手动安装：
```bash
sudo apt-get update
sudo apt-get install -y curl git python3 python3-pip nodejs npm tmux
```

### Q2: 消息平台收不到推送？

**A**: 检查：
1. `.env`文件中的Token和Chat ID是否正确
2. OpenClaw Gateway是否已启动 (`pnpm gateway:start`)
3. Bot是否有权限向您发送消息

### Q3: 历史数据如何初始化？

**A**: 部署脚本会自动尝试初始化。如果失败，手动执行：
```bash
cd /opt/stockmoney
pip3 install akshare
python3 scripts/investment_monitor.py --init-history
```

### Q4: 如何更新到最新版本？

**A**: 在code-server终端执行：
```bash
cd /opt/stockmoney
git pull origin main
```

### Q5: CC CLI如何自动更新研究？

**A**: 系统已配置每周三20:00自动运行。您也可以手动触发：
```
在Telegram发送: 研究
```

### Q6: 如何查看运行日志？

**A**: 在code-server终端执行：
```bash
tail -f /opt/stockmoney/logs/*.log
```

---

## 安全提示

1. **Bot Token保密**：不要在公开场合分享Telegram Bot Token
2. **服务器安全**：确保192.168.50.6仅在内部网络可访问
3. **投资有风险**：本系统仅供研究参考，不构成投资建议

---

*部署遇到问题？请在Telegram中发送 `帮助` 获取支持信息。*
