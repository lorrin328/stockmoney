#!/bin/bash
# StockMoney 投资系统 - 一键部署脚本
# 使用方法：在code-server终端中执行：bash deploy.sh
# 日期：2026-05-01

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置
INSTALL_DIR="/opt/stockmoney"
OPENCLAW_DIR="/opt/openclaw"
NODE_VERSION="20"
PYTHON_VERSION="3.10"

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  StockMoney 投资系统 - 一键部署脚本${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# ============================================================
# 步骤1：检测环境
# ============================================================
echo -e "${YELLOW}[1/10] 检测系统环境...${NC}"

UBUNTU_VERSION=$(lsb_release -rs 2>/dev/null || echo "unknown")
echo "  Ubuntu版本: $UBUNTU_VERSION"
echo "  当前用户: $(whoami)"
echo "  当前目录: $(pwd)"

# 检查是否有sudo权限
if sudo -n true 2>/dev/null; then
    echo "  sudo权限: 有"
    HAS_SUDO=1
else
    echo "  sudo权限: 无（部分操作可能需要手动执行）"
    HAS_SUDO=0
fi

echo ""

# ============================================================
# 步骤2：安装系统依赖
# ============================================================
echo -e "${YELLOW}[2/10] 安装系统依赖...${NC}"

install_system_deps() {
    if [ $HAS_SUDO -eq 1 ]; then
        sudo apt-get update -qq
        sudo apt-get install -y -qq \
            curl wget git \
            python3 python3-pip python3-venv \
            nodejs npm \
            tmux \
            build-essential \
            libssl-dev \
            2>/dev/null || true
    else
        echo -e "${RED}  警告：无sudo权限，请手动安装以下依赖：${NC}"
        echo "  - curl, wget, git"
        echo "  - python3, python3-pip, python3-venv"
        echo "  - nodejs, npm"
        echo "  - tmux"
        read -p "  按Enter继续（假设依赖已安装）..."
    fi
}

install_system_deps
echo -e "${GREEN}  系统依赖检查完成${NC}"
echo ""

# ============================================================
# 步骤3：安装/升级 Node.js 和 pnpm
# ============================================================
echo -e "${YELLOW}[3/10] 配置 Node.js 环境...${NC}"

if ! command -v node &> /dev/null || [ "$(node -v | cut -d'v' -f2 | cut -d'.' -f1)" -lt 18 ]; then
    echo "  安装 Node.js ${NODE_VERSION}..."
    if [ $HAS_SUDO -eq 1 ]; then
        curl -fsSL https://deb.nodesource.com/setup_${NODE_VERSION}.x | sudo -E bash -
        sudo apt-get install -y nodejs
    else
        echo -e "${RED}  需要sudo权限安装Node.js，请手动执行：${NC}"
        echo "  curl -fsSL https://deb.nodesource.com/setup_${NODE_VERSION}.x | sudo -E bash -"
        echo "  sudo apt-get install -y nodejs"
        exit 1
    fi
else
    echo "  Node.js已安装: $(node -v)"
fi

# 安装pnpm
if ! command -v pnpm &> /dev/null; then
    echo "  安装 pnpm..."
    npm install -g pnpm
else
    echo "  pnpm已安装: $(pnpm -v)"
fi

echo -e "${GREEN}  Node.js环境配置完成${NC}"
echo ""

# ============================================================
# 步骤4：安装 Claude Code CLI
# ============================================================
echo -e "${YELLOW}[4/10] 安装 Claude Code CLI...${NC}"

if command -v claude &> /dev/null; then
    echo "  Claude Code CLI已安装: $(claude --version 2>/dev/null || echo 'version unknown')"
else
    echo "  安装 Claude Code CLI..."
    npm install -g @anthropic-ai/claude-code
    echo -e "${GREEN}  Claude Code CLI安装完成${NC}"
fi

# 验证安装
if command -v claude &> /dev/null; then
    echo -e "${GREEN}  Claude Code CLI路径: $(which claude)${NC}"
else
    echo -e "${RED}  Claude Code CLI安装失败，请手动安装：${NC}"
    echo "  npm install -g @anthropic-ai/claude-code"
    exit 1
fi
echo ""

# ============================================================
# 步骤5：安装 OpenClaw
# ============================================================
echo -e "${YELLOW}[5/10] 安装 OpenClaw...${NC}"

if [ -d "$OPENCLAW_DIR" ] && [ -f "$OPENCLAW_DIR/package.json" ]; then
    echo "  OpenClaw已存在于 $OPENCLAW_DIR"
    cd "$OPENCLAW_DIR"
    echo "  更新OpenClaw..."
    git pull origin main 2>/dev/null || echo "  更新跳过"
else
    echo "  克隆OpenClaw仓库..."
    git clone https://github.com/openclaw/openclaw.git "$OPENCLAW_DIR"
    cd "$OPENCLAW_DIR"
    echo "  安装依赖..."
    pnpm install
    echo "  初始化OpenClaw..."
    pnpm openclaw setup
fi

echo -e "${GREEN}  OpenClaw安装完成${NC}"
echo ""

# ============================================================
# 步骤6：安装 Python 依赖
# ============================================================
echo -e "${YELLOW}[6/10] 安装 Python 依赖...${NC}"

pip3 install --user --quiet \
    numpy pandas requests \
    akshare \
    2>/dev/null || echo "  部分依赖安装失败，将使用备选方案"

echo -e "${GREEN}  Python依赖安装完成${NC}"
echo ""

# ============================================================
# 步骤7：克隆/更新 StockMoney 项目
# ============================================================
echo -e "${YELLOW}[7/10] 部署 StockMoney 投资模块...${NC}"

if [ -d "$INSTALL_DIR/.git" ]; then
    echo "  更新现有项目..."
    cd "$INSTALL_DIR"
    git pull origin main
else
    echo "  克隆项目到 $INSTALL_DIR..."
    # 如果当前目录是git仓库，直接使用
    if [ -d ".git" ] && [ -f "scripts/strategy_engine.py" ]; then
        echo "  检测到本地仓库，复制到 $INSTALL_DIR..."
        mkdir -p "$INSTALL_DIR"
        cp -r . "$INSTALL_DIR/"
    else
        git clone https://github.com/lorrin328/stockmoney.git "$INSTALL_DIR"
    fi
fi

cd "$INSTALL_DIR"
mkdir -p data/history data/signals reports papers

echo -e "${GREEN}  StockMoney部署完成${NC}"
echo ""

# ============================================================
# 步骤8：创建 OpenClaw 集成配置
# ============================================================
echo -e "${YELLOW}[8/10] 配置 OpenClaw 集成...${NC}"

# 创建OpenClaw配置目录
mkdir -p "$OPENCLAW_DIR/integrations/stockmoney"

# 创建CC CLI驱动脚本
cat > "$INSTALL_DIR/openclaw/run_cc_cli.sh" << 'DRIVER_EOF'
#!/bin/bash
# CC CLI 非交互式驱动脚本
# 由OpenClaw调用，在tmux会话中执行CC CLI命令

SESSION="stockmoney-cc"
WORK_DIR="/opt/stockmoney"
LOG_FILE="/opt/stockmoney/logs/cc_cli_$(date +%Y%m%d_%H%M%S).log"

mkdir -p "$(dirname "$LOG_FILE")"

# 创建或附加到tmux会话
if ! tmux has-session -t "$SESSION" 2>/dev/null; then
    tmux new-session -d -s "$SESSION" "cd $WORK_DIR && claude"
    sleep 8
fi

# 清空面板以便捕获新输出
tmux send-keys -t "$SESSION" C-l
sleep 1

# 发送命令
tmux send-keys -t "$SESSION" "$1" Enter
sleep 2

# 捕获输出（最近50行）
tmux capture-pane -t "$SESSION" -p | tail -50 > "$LOG_FILE"

# 返回日志内容
cat "$LOG_FILE"
DRIVER_EOF

chmod +x "$INSTALL_DIR/openclaw/run_cc_cli.sh"

# 创建Python快速执行脚本
cat > "$INSTALL_DIR/openclaw/run_python.sh" << 'PYEOF'
#!/bin/bash
# Python脚本快速执行器
# 由OpenClaw直接调用，无需CC CLI

WORK_DIR="/opt/stockmoney"
SCRIPT="$1"
LOG_FILE="/opt/stockmoney/logs/python_$(date +%Y%m%d_%H%M%S).log"

mkdir -p "$(dirname "$LOG_FILE")"

cd "$WORK_DIR"
python3 "$SCRIPT" 2>&1 | tee "$LOG_FILE"
PYEOF

chmod +x "$INSTALL_DIR/openclaw/run_python.sh"

# 创建定时任务配置
cat > "$OPENCLAW_DIR/integrations/stockmoney/cron.yaml" << 'CRONEOF'
# StockMoney 定时任务配置
# 中国股市交易日：周一至周五（节假日除外）

jobs:
  - name: "market-open-monitor"
    description: "盘前监控（交易日9:25）"
    schedule: "25 9 * * 1-5"
    command: "/opt/stockmoney/openclaw/run_python.sh scripts/investment_monitor.py"
    output_channel: "telegram"
    enabled: true

  - name: "market-close-monitor"
    description: "盘后监控（交易日15:05）"
    schedule: "5 15 * * 1-5"
    command: "/opt/stockmoney/openclaw/run_python.sh scripts/investment_monitor.py"
    output_channel: "telegram"
    enabled: true

  - name: "daily-strategy-summary"
    description: "每日策略摘要（20:00）"
    schedule: "0 20 * * *"
    command: "/opt/stockmoney/openclaw/run_python.sh scripts/strategy_engine.py --decision"
    output_channel: "telegram"
    enabled: true

  - name: "weekly-cycle-analysis"
    description: "周度周期分析（周一9:00）"
    schedule: "0 9 * * 1"
    command: "/opt/stockmoney/openclaw/run_python.sh scripts/cycle_phase_evaluator.py --resonance"
    output_channel: "telegram"
    enabled: true

  - name: "weekly-strategy-report"
    description: "周度策略报告（周一9:30）"
    schedule: "30 9 * * 1"
    command: "/opt/stockmoney/openclaw/run_python.sh scripts/strategy_engine.py --report"
    output_channel: "telegram"
    enabled: true

  - name: "monthly-policy-update"
    description: "月度政策分析（每月1日9:00）"
    schedule: "0 9 1 * *"
    command: "/opt/stockmoney/openclaw/run_python.sh scripts/policy_analyzer.py --report"
    output_channel: "telegram"
    enabled: true

  - name: "monthly-full-analysis"
    description: "月度全量分析（每月1日9:30）"
    schedule: "30 9 1 * *"
    command: "/opt/stockmoney/openclaw/run_python.sh scripts/strategy_engine.py --report"
    output_channel: "telegram"
    enabled: true

  - name: "cc-cli-research-update"
    description: "CC CLI研究更新（每周三20:00）"
    schedule: "0 20 * * 3"
    command: "/opt/stockmoney/openclaw/run_cc_cli.sh '分析最新政策和市场动态，更新投资模块配置'"
    output_channel: "telegram"
    enabled: true
    timeout: 300
CRONEOF

# 创建用户命令映射配置
cat > "$OPENCLAW_DIR/integrations/stockmoney/commands.yaml" << 'CMDEOF'
# StockMoney 用户命令映射
# 用户在消息平台发送的指令 → 系统动作

commands:
  # ===== 日常查询 =====
  today_signal:
    patterns:
      - "今日信号"
      - "今天信号"
      - "监控"
      - "盘前"
      - "盘后"
    action: "/opt/stockmoney/openclaw/run_python.sh scripts/investment_monitor.py"
    response_type: "summary"
    description: "今日ETF监控信号"

  strategy:
    patterns:
      - "策略"
      - "决策"
      - "策略报告"
    action: "/opt/stockmoney/openclaw/run_python.sh scripts/strategy_engine.py --decision"
    response_type: "structured"
    description: "策略决策摘要"

  full_report:
    patterns:
      - "完整报告"
      - "详细报告"
      - "全量分析"
    action: "/opt/stockmoney/openclaw/run_python.sh scripts/strategy_engine.py --report"
    response_type: "file"
    description: "生成完整策略报告"

  # ===== 政策与宏观 =====
  policy:
    patterns:
      - "政策"
      - "政策分析"
      - "十五五"
      - "宏观"
    action: "/opt/stockmoney/openclaw/run_python.sh scripts/policy_analyzer.py --summary"
    response_type: "structured"
    description: "政策与宏观环境分析"

  commodity:
    patterns:
      - "商品"
      - "大宗商品"
      - "铜"
      - "黄金"
      - "原油"
    action: "/opt/stockmoney/openclaw/run_python.sh scripts/policy_analyzer.py --summary"
    response_type: "structured"
    description: "大宗商品分析"

  # ===== 周期分析 =====
  cycle:
    patterns:
      - "周期"
      - "康波"
      - "共振"
    action: "/opt/stockmoney/openclaw/run_python.sh scripts/cycle_phase_evaluator.py --resonance"
    response_type: "structured"
    description: "周期共振分析"

  market:
    patterns:
      - "市场"
      - "指标"
      - "估值"
    action: "/opt/stockmoney/openclaw/run_python.sh scripts/market_indicators.py --summary"
    response_type: "structured"
    description: "市场指标综合判断"

  # ===== 推荐与决策 =====
  recommend:
    patterns:
      - "推荐"
      - "推荐标的"
      - "买什么"
      - "买什么好"
      - "标的"
    action: "/opt/stockmoney/openclaw/run_python.sh scripts/strategy_engine.py --decision"
    response_type: "recommendation"
    description: "标的推荐与仓位建议"

  allocation:
    patterns:
      - "配置"
      - "资产配置"
      - "仓位"
    action: "/opt/stockmoney/openclaw/run_python.sh scripts/asset_allocator.py --allocation"
    response_type: "structured"
    description: "资产配置方案"

  # ===== 4%定投法 =====
  four_percent:
    patterns:
      - "4%"
      - "定投"
      - "买入"
      - "触发"
    action: "/opt/stockmoney/openclaw/run_python.sh scripts/investment_monitor.py"
    response_type: "summary"
    description: "4%定投法信号"

  # ===== 研究更新 =====
  research:
    patterns:
      - "研究"
      - "更新研究"
      - "完善模块"
      - "升级"
    action: "/opt/stockmoney/openclaw/run_cc_cli.sh '根据最新政策和市场研究，更新scripts/policy_analyzer.py和scripts/strategy_engine.py中的分析逻辑与数据'"
    response_type: "async"
    description: "CC CLI研究更新（耗时较长）"
    timeout: 300

  # ===== 帮助 =====
  help:
    patterns:
      - "帮助"
      - "help"
      - "怎么用"
      - "命令"
    action: "show_help"
    response_type: "text"
    description: "显示帮助信息"
CMDEOF

# 创建帮助文本
cat > "$INSTALL_DIR/openclaw/help.txt" << 'HELPEOF'
StockMoney 投资系统 - 可用命令

【日常查询】
今日信号 / 监控      - 查看今日ETF监控信号和4%定投触发
策略 / 决策          - 获取策略决策摘要（周期+市场+政策）
完整报告             - 生成完整策略报告（详细版）

【分析查询】
政策 / 宏观          - 政策与宏观环境分析（十五五/美联储/大宗商品）
周期 / 康波          - 周期共振分析（康波/朱格拉/基钦）
市场 / 估值          - 市场指标综合判断（PE/PB/情绪/流动性）
商品 / 黄金          - 大宗商品分析

【决策支持】
推荐 / 买什么        - 标的推荐与仓位建议
配置 / 仓位          - 资产配置方案

【维护】
研究 / 更新          - CC CLI自动更新研究模块（每周自动运行）
帮助 / help          - 显示本帮助

【定时推送】
- 工作日9:25:  盘前监控
- 工作日15:05: 盘后监控
- 每日20:00:   策略摘要
- 每周一9:30:  周度策略报告
- 每月1日:     政策分析+全量报告
HELPEOF

echo -e "${GREEN}  OpenClaw集成配置完成${NC}"
echo ""

# ============================================================
# 步骤9：初始化历史数据
# ============================================================
echo -e "${YELLOW}[9/10] 初始化历史数据...${NC}"

cd "$INSTALL_DIR"
mkdir -p data/history data/signals logs

# 检查是否有akshare可用
if python3 -c "import akshare" 2>/dev/null; then
    echo "  akshare可用，开始初始化历史数据..."
    echo "  这将需要几分钟时间..."
    python3 scripts/investment_monitor.py --init-history 2>/dev/null || echo "  初始化失败，将使用实时数据"
else
    echo -e "${YELLOW}  akshare未安装，跳过历史数据初始化${NC}"
    echo "  提示：安装akshare后可运行: python3 scripts/investment_monitor.py --init-history"
fi

echo -e "${GREEN}  数据初始化完成${NC}"
echo ""

# ============================================================
# 步骤10：测试运行
# ============================================================
echo -e "${YELLOW}[10/10] 测试运行...${NC}"

cd "$INSTALL_DIR"

echo "  测试1: 策略引擎..."
python3 scripts/strategy_engine.py --decision > logs/test_strategy.log 2>&1 || echo "  策略引擎测试失败"

echo "  测试2: 政策分析..."
python3 scripts/policy_analyzer.py --summary > logs/test_policy.log 2>&1 || echo "  政策分析测试失败"

echo "  测试3: CC CLI驱动..."
if [ -f "$INSTALL_DIR/openclaw/run_cc_cli.sh" ]; then
    echo "  CC CLI驱动脚本已就绪"
fi

echo -e "${GREEN}  测试完成${NC}"
echo ""

# ============================================================
# 部署完成总结
# ============================================================
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  StockMoney 部署完成！${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo "安装目录: $INSTALL_DIR"
echo "OpenClaw目录: $OPENCLAW_DIR"
echo "日志目录: $INSTALL_DIR/logs"
echo ""
echo "已安装组件:"
echo "  Claude Code CLI: $(which claude)"
echo "  OpenClaw: $OPENCLAW_DIR"
echo "  Python依赖: numpy, pandas, requests, akshare"
echo ""
echo "定时任务配置:"
echo "  $OPENCLAW_DIR/integrations/stockmoney/cron.yaml"
echo ""
echo "用户命令配置:"
echo "  $OPENCLAW_DIR/integrations/stockmoney/commands.yaml"
echo ""
echo -e "${YELLOW}下一步操作：${NC}"
echo ""
echo "1. 配置消息平台（Telegram/Slack）:"
echo "   编辑 $OPENCLAW_DIR/.env 添加:"
echo "   TELEGRAM_BOT_TOKEN=your_token"
echo "   TELEGRAM_CHAT_ID=your_chat_id"
echo ""
echo "2. 启动OpenClaw Gateway:"
echo "   cd $OPENCLAW_DIR && pnpm gateway:start"
echo ""
echo "3. 在消息平台发送命令测试:"
echo "   '今日信号' / '策略' / '推荐' / '帮助'"
echo ""
echo "4. 查看日志:"
echo "   tail -f $INSTALL_DIR/logs/*.log"
echo ""
echo -e "${BLUE}============================================${NC}"
