#!/usr/bin/env python3
"""
策略决策引擎 - 基于康波周期的统一投资决策系统

整合所有模块：
1. 康波周期定位 (kondratiev_model)
2. 多周期共振分析 (cycle_phase_evaluator)
3. 市场指标验证 (market_indicators)
4. 资产配置决策 (asset_allocator)
5. 4%定投法执行 (four_percent_model)

输出：完整的策略决策报告

使用：
    python scripts/strategy_engine.py --report
    python scripts/strategy_engine.py --decision

作者：Claude Code
日期：2026-05-01
"""

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# 路径配置
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
REPORTS_DIR = BASE_DIR / "reports"

REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# 将项目根目录加入路径以便导入同级模块
sys.path.insert(0, str(BASE_DIR / "scripts"))


# ---------------------------------------------------------------------------
# 数据模型
# ---------------------------------------------------------------------------

@dataclass
class StrategyDecision:
    """最终策略决策"""
    cycle_position: str
    resonance_strength: str
    resonance_score: float
    market_score: float
    market_signal: str
    overall_position: float
    position_range: Tuple[float, float]
    asset_allocation: Dict[str, float]
    key_sectors: List[str]
    entry_strategy: str
    exit_strategy: str
    risk_management: List[str]
    four_percent_enabled: bool
    monthly_dca_amount: float
    key_risks: List[str]
    key_opportunities: List[str]


# ---------------------------------------------------------------------------
# 策略引擎核心类
# ---------------------------------------------------------------------------

class StrategyEngine:
    """策略决策引擎"""

    def __init__(self):
        self.year = 2026
        self._init_submodules()

    def _init_submodules(self):
        """初始化各子模块"""
        try:
            from kondratiev_model import KondratievModel
            self.kondratiev = KondratievModel()
        except Exception as e:
            print(f"[WARN] Kondratiev model not available: {e}")
            self.kondratiev = None

        try:
            from cycle_phase_evaluator import CyclePhaseEvaluator
            self.cycle_eval = CyclePhaseEvaluator()
        except Exception as e:
            print(f"[WARN] Cycle evaluator not available: {e}")
            self.cycle_eval = None

        try:
            from market_indicators import MarketIndicatorSystem
            self.market = MarketIndicatorSystem()
        except Exception as e:
            print(f"[WARN] Market indicators not available: {e}")
            self.market = None

        try:
            from asset_allocator import AssetAllocator
            self.allocator = AssetAllocator()
        except Exception as e:
            print(f"[WARN] Asset allocator not available: {e}")
            self.allocator = None

    def evaluate_all(self) -> StrategyDecision:
        """执行完整评估，输出策略决策"""

        # 1. 康波周期定位
        if self.kondratiev:
            kondratiev_phase = self.kondratiev.get_current_phase()
            cycle_pos = self.kondratiev.get_cycle_position(self.year)
            tech_drivers = cycle_pos.tech_drivers if cycle_pos else ["AI", "新能源"]
        else:
            kondratiev_phase = "复苏期"
            tech_drivers = ["AI", "新能源", "生物技术", "量子计算"]

        # 2. 多周期共振
        if self.cycle_eval:
            phases, resonance = self.cycle_eval.evaluate_all(self.year)
            resonance_strength = resonance.resonance_strength
            resonance_score = resonance.resonance_score
            position_range = resonance.position_range
            aligned = resonance.aligned_cycles
            opposed = resonance.opposed_cycles
        else:
            resonance_strength = "中共振偏强"
            resonance_score = 70.0
            position_range = (0.50, 0.70)
            aligned = ["康德拉季耶夫长波", "朱格拉周期", "基钦周期"]
            opposed = []

        # 3. 市场指标
        if self.market:
            summary = self.market.calculate_summary()
            market_score = summary.overall_score
            market_signal = summary.overall_signal
            market_risks = summary.key_risks
            market_opps = summary.key_opportunities
        else:
            market_score = 60.0
            market_signal = "bullish"
            market_risks = []
            market_opps = []

        # 4. 资产配置
        if self.allocator:
            plan = self.allocator.generate_plan(
                phase=kondratiev_phase,
                resonance="强共振" if resonance_score >= 75 else ("弱共振" if resonance_score <= 40 else "medium")
            )
            asset_alloc = {w.asset_class: w.weight_mid for w in plan.asset_weights}
            overall_position = plan.overall_position
        else:
            asset_alloc = {"stock": 0.40, "bond": 0.20, "commodity": 0.25, "gold": 0.10, "cash": 0.05}
            overall_position = 0.70

        # 5. 关键赛道（基于康波主题）
        key_sectors = self._derive_sectors(kondratiev_phase, tech_drivers)

        # 6. 进入/退出策略
        entry_strategy = self._derive_entry(kondratiev_phase, market_signal, resonance_strength)
        exit_strategy = self._derive_exit(kondratiev_phase, market_signal)

        # 7. 风险管理
        risk_mgmt = self._derive_risk_mgmt(kondratiev_phase, resonance_score, market_score)

        # 8. 4%定投法是否启用
        four_pct_enabled = market_signal in ("bullish", "neutral") and kondratiev_phase in ("复苏期", "萧条期")

        # 9. 月度定投金额（90万18个月方案）
        monthly_dca = 50000 if four_pct_enabled else 0

        # 整合风险与机会
        all_risks = market_risks.copy() if market_risks else []
        all_opps = market_opps.copy() if market_opps else []

        if kondratiev_phase == "复苏期":
            all_opps.extend([
                "第六轮康波复苏起点，长期布局窗口",
                "AI+新能源为核心引擎，成长空间大",
                "朱格拉周期触底回升，设备投资景气上行",
            ])
            all_risks.extend([
                "房地产周期仍在触底，政策效果待验证",
                "地缘政治不确定性",
                "周期拐点判断可能滞后2-3年",
            ])

        return StrategyDecision(
            cycle_position=kondratiev_phase,
            resonance_strength=resonance_strength,
            resonance_score=resonance_score,
            market_score=market_score,
            market_signal=market_signal,
            overall_position=overall_position,
            position_range=position_range,
            asset_allocation=asset_alloc,
            key_sectors=key_sectors,
            entry_strategy=entry_strategy,
            exit_strategy=exit_strategy,
            risk_management=risk_mgmt,
            four_percent_enabled=four_pct_enabled,
            monthly_dca_amount=monthly_dca,
            key_risks=all_risks,
            key_opportunities=all_opps,
        )

    def _derive_sectors(self, phase: str, tech_drivers: List[str]) -> List[str]:
        """根据周期阶段推导关键赛道"""
        base_sectors = {
            "复苏期": [
                "AI算力基础设施（芯片、服务器、数据中心）",
                "AI应用落地（行业大模型、智能体）",
                "新能源产业链（储能、智能电网、氢能）",
                "高端制造替代（半导体设备、工业软件）",
                "工业金属（铜、铝、锂）",
                "创新药与生物技术",
            ],
            "繁荣期": [
                "科技成长股（全面享受泡沫）",
                "大宗商品（通胀受益）",
                "周期股（产能扩张期）",
                "消费升级",
            ],
            "衰退期": [
                "高股息防御（红利低波）",
                "债券（利率下行受益）",
                "黄金（避险）",
                "公用事业（电力）",
            ],
            "萧条期": [
                "黄金（超配避险）",
                "债券（标配/超配）",
                "现金（保持流动性）",
                "逆向布局优质资产（为复苏做准备）",
            ],
        }
        return base_sectors.get(phase, base_sectors["复苏期"])

    def _derive_entry(self, phase: str, market_signal: str, resonance: str) -> str:
        """推导进入策略"""
        if phase == "复苏期":
            if market_signal == "bullish":
                return "左侧布局+右侧确认：4%定投法触发时买入，同时关注右侧突破信号"
            else:
                return "严格左侧布局：仅使用4%定投法，等待下跌触发，不急不躁"
        elif phase == "繁荣期":
            return "趋势跟随：减少4%定投触发，关注移动止盈，享受泡沫但不追高"
        elif phase == "衰退期":
            return "防御为主：暂停新增买入，逐步减仓，保留现金和债券"
        elif phase == "萧条期":
            return "逆向布局：大跌大买，小跌小买，为复苏期积攒筹码"
        return "观望等待"

    def _derive_exit(self, phase: str, market_signal: str) -> str:
        """推导退出策略"""
        if phase == "复苏期":
            return "E/P<6.4%强制卖出 + 盈利35%分层止盈 + 最高点回撤10%移动止盈"
        elif phase == "繁荣期":
            return "积极止盈：分层止盈（15%/25%/35%）+ 移动止盈，逐步降低仓位"
        elif phase == "衰退期":
            return "果断减仓：E/P<6.4%全卖 + 盈利即止盈，不恋战"
        elif phase == "萧条期":
            return "极少卖出：仅在极端高估时减仓，主要策略是持有和增持"
        return "E/P<6.4%全卖"

    def _derive_risk_mgmt(self, phase: str, resonance: float, market: float) -> List[str]:
        """推导风险管理措施"""
        rules = []

        # 仓位上限
        if phase == "复苏期":
            rules.append(f"股票仓位上限：70%（当前建议{int(market * 0.7)}%）")
        elif phase == "繁荣期":
            rules.append("股票仓位上限：80%，但建议逐步降低至60%")
        elif phase == "衰退期":
            rules.append("股票仓位上限：40%，实际建议20-30%")
        elif phase == "萧条期":
            rules.append("股票仓位上限：30%，实际建议10-20%")

        # 止损
        rules.append("单标的最大亏损：-20%（硬止损）")
        rules.append("组合最大回撤：-15%（触发全面减仓）")

        # 再平衡
        rules.append("偏离度≥5%触发再平衡")
        rules.append("每季度强制检查一次配置偏离度")

        # 流动性
        rules.append("始终保持5-10%现金（4%定投法需要现金储备）")
        rules.append("黄金配置10-15%作为避险底仓")

        # 周期风险
        rules.append("康波周期判断可能滞后2-5年，保持灵活")
        rules.append("政策干预可能改变周期轨迹，关注央行动向")

        return rules


# ---------------------------------------------------------------------------
# 报告生成
# ---------------------------------------------------------------------------

def generate_strategy_report(decision: StrategyDecision) -> str:
    """生成完整策略决策报告"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    def signal_icon(signal: str) -> str:
        return "📈" if signal == "bullish" else ("📉" if signal == "bearish" else "➖")

    lines = [
        f"# 投资策略决策报告",
        f"",
        f"**生成时间**: {now}",
        f"**当前年份**: 2026年",
        f"",
        "---",
        "",
        "## 一、宏观周期定位",
        "",
        "### 1.1 康波周期",
        "",
        f"| 维度 | 内容 |",
        f"|------|------|",
        f"| 康波轮次 | 第六轮康波周期 |",
        f"| 周期名称 | 人工智能与新能源 |",
        f"| 核心技术 | AI、新能源、生物技术、量子计算 |",
        f"| 主导国家 | 中美竞争 |",
        f"| 当前阶段 | **{decision.cycle_position}** |",
        f"| 阶段含义 | 长期布局窗口，播种而非收割之年 |",
        f"",
        "### 1.2 周期共振",
        "",
        f"| 维度 | 内容 |",
        f"|------|------|",
        f"| 共振强度 | **{decision.resonance_strength}** |",
        f"| 共振评分 | {decision.resonance_score:.0f}/100 |",
        f"| 建议仓位 | **{decision.overall_position:.0%}**（区间 {decision.position_range[0]:.0%}-{decision.position_range[1]:.0%}） |",
        f"",
        "### 1.3 市场指标验证",
        "",
        f"| 维度 | 内容 |",
        f"|------|------|",
        f"| 综合评分 | {decision.market_score:.0f}/100 |",
        f"| 综合信号 | {signal_icon(decision.market_signal)} **{decision.market_signal.upper()}** |",
        f"",
        "---",
        "",
        "## 二、资产配置决策",
        "",
        "### 2.1 资产类别权重",
        "",
        "| 资产类别 | 目标权重 | 配置逻辑 |",
        "|----------|----------|----------|",
    ]

    asset_names = {
        "stock": "股票", "bond": "债券", "commodity": "大宗商品",
        "gold": "黄金", "cash": "现金", "defensive": "防御",
    }
    for asset, weight in sorted(decision.asset_allocation.items(), key=lambda x: x[1], reverse=True):
        name = asset_names.get(asset, asset)
        lines.append(f"| {name} | {weight:.0%} | - |")

    lines.extend([
        "",
        "### 2.2 关键赛道",
        "",
    ])
    for i, sector in enumerate(decision.key_sectors, 1):
        lines.append(f"{i}. {sector}")

    lines.extend([
        "",
        "---",
        "",
        "## 三、执行策略",
        "",
        "### 3.1 进入策略",
        "",
        f"{decision.entry_strategy}",
        "",
        "### 3.2 退出策略",
        "",
        f"{decision.exit_strategy}",
        "",
        "### 3.3 4%定投法",
        "",
    ])

    if decision.four_percent_enabled:
        lines.extend([
            f"- **状态**: 启用 ✅",
            f"- **月度定投**: {decision.monthly_dca_amount:,.0f}元",
            f"- **核心纪律**: 总资金分25份，从上次买入点跌4%才买，E/P>10%才启动",
            f"- **卖出纪律**: E/P<6.4%全卖，盈利15%/25%/35%分层止盈",
            "",
            "**适用场景**: 震荡市/下跌市/筑底期表现最佳",
            "**不适用场景**: 单边上涨市容易踏空",
        ])
    else:
        lines.extend([
            "- **状态**: 暂停 ⏸️",
            "- **原因**: 当前市场阶段不适合4%定投法",
            "- **替代方案**: 普通月定投或一次性买入",
        ])

    lines.extend([
        "",
        "---",
        "",
        "## 四、风险管理",
        "",
    ])
    for rule in decision.risk_management:
        lines.append(f"- {rule}")

    lines.extend([
        "",
        "---",
        "",
        "## 五、关键风险与机会",
        "",
        "### 5.1 关键风险 ⚠️",
        "",
    ])
    for risk in decision.key_risks:
        lines.append(f"- {risk}")

    lines.extend([
        "",
        "### 5.2 关键机会 ✅",
        "",
    ])
    for opp in decision.key_opportunities:
        lines.append(f"- {opp}")

    lines.extend([
        "",
        "---",
        "",
        "## 六、操作清单",
        "",
        "### 本周待办",
        "",
        "- [ ] 运行 `python scripts/investment_monitor.py` 检查每日信号",
        "- [ ] 运行 `python scripts/strategy_engine.py --report` 更新策略报告",
        "- [ ] 检查4%定投法触发条件（如有持仓）",
        "- [ ] 检查资产配置偏离度（季度）",
        "",
        "### 月度待办",
        "",
        "- [ ] 执行定投计划（{decision.monthly_dca_amount:,.0f}元）".format(decision=decision),
        "- [ ] 更新市场指标评估",
        "- [ ] 复盘上月操作，检查止损/止盈执行",
        "- [ ] 阅读康波周期研究报告更新",
        "",
        "---",
        "",
        "*本报告基于康波周期理论、多周期共振分析和市场指标综合生成，仅供研究参考，不构成投资建议。*",
        "*经济周期理论存在争议，历史规律不代表未来表现。投资有风险，入市需谨慎。*",
        "",
    ])

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="策略决策引擎")
    parser.add_argument("--report", action="store_true", help="生成完整策略报告")
    parser.add_argument("--decision", action="store_true", help="显示策略决策摘要")
    parser.add_argument("--year", type=int, default=2026, help="指定年份")
    args = parser.parse_args()

    engine = StrategyEngine()
    decision = engine.evaluate_all()

    if args.report:
        report = generate_strategy_report(decision)
        report_path = REPORTS_DIR / f"strategy_decision_{datetime.now().strftime('%Y%m%d')}.md"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"报告已保存: {report_path}")
        print("\n报告预览（前3000字符）：")
        print(report[:3000])
    elif args.decision:
        print("投资策略决策")
        print("=" * 60)
        print(f"康波阶段: {decision.cycle_position}")
        print(f"共振强度: {decision.resonance_strength} ({decision.resonance_score:.0f}分)")
        print(f"市场信号: {decision.market_signal.upper()} ({decision.market_score:.0f}分)")
        print(f"建议仓位: {decision.overall_position:.0%} ({decision.position_range[0]:.0%}-{decision.position_range[1]:.0%})")
        print(f"\n4%定投法: {'启用' if decision.four_percent_enabled else '暂停'}")
        print(f"月度定投: {decision.monthly_dca_amount:,.0f}元")
        print(f"\n进入策略: {decision.entry_strategy}")
        print(f"退出策略: {decision.exit_strategy}")
        print(f"\n关键赛道:")
        for s in decision.key_sectors[:5]:
            print(f"  - {s}")
        print(f"\n风险: {len(decision.key_risks)}项 | 机会: {len(decision.key_opportunities)}项")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
