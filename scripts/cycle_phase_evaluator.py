#!/usr/bin/env python3
"""
周期阶段评估系统 - 多周期嵌套共振分析

基于熊彼特三周期嵌套理论：
- 康德拉季耶夫长波：50-60年（技术革命驱动）
- 朱格拉中周期：8-10年（设备投资/资本开支驱动）
- 基钦短周期：3-4年（库存调整驱动）

功能：
1. 各周期阶段独立评估
2. 周期共振强度计算
3. 仓位建议生成
4. 共振报告输出

使用：
    python scripts/cycle_phase_evaluator.py --report
    python scripts/cycle_phase_evaluator.py --resonance

作者：Claude Code
日期：2026-05-01
"""

import argparse
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np

# ---------------------------------------------------------------------------
# 路径配置
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
CYCLE_DATA_DIR = DATA_DIR / "cycle_data"
REPORTS_DIR = BASE_DIR / "reports"

CYCLE_DATA_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# 数据模型
# ---------------------------------------------------------------------------

@dataclass
class CyclePhase:
    """单个周期阶段"""
    cycle_name: str
    cycle_type: str  # kondratiev / juglar / kitchin
    period_years: int
    current_phase: str  # 繁荣/衰退/萧条/复苏
    phase_progress: float  # 0-1
    direction: str  # up / down / flat
    confidence: str  # high / medium / low
    description: str


@dataclass
class ResonanceResult:
    """共振分析结果"""
    resonance_strength: str  # strong / medium / weak
    resonance_score: float  # 0-100
    aligned_cycles: List[str]
    opposed_cycles: List[str]
    recommended_position: str  # 高仓位 / 中仓位 / 低仓位
    position_range: Tuple[float, float]  # (min%, max%)
    risk_level: str
    notes: str


# ---------------------------------------------------------------------------
# 周期数据（基于历史规律和研究推算）
# ---------------------------------------------------------------------------

# 康波周期（已由kondratiev_model.py提供，此处引用结论）
KONDRATIEV_2026 = {
    "cycle_name": "第六轮康波（AI与新能源）",
    "current_phase": "复苏期",
    "phase_progress": 0.0,  # 刚起步
    "direction": "up",
    "confidence": "medium",
    "description": "2026年为第六轮康波复苏元年，AI、新能源、生物技术为核心引擎",
}

# 朱格拉周期（设备投资周期，8-10年）
# 上轮高点约2017-2018年（中国设备投资高峰）
# 本轮预计2025-2027年触底回升
JUGLAR_CYCLES = [
    {"start": 2009, "peak": 2013, "trough": 2016},   # 四万亿刺激后周期
    {"start": 2016, "peak": 2018, "trough": 2020},   # 供给侧改革周期
    {"start": 2020, "peak": 2022, "trough": 2025},   # 疫情后周期
    {"start": 2025, "peak": 2028, "trough": 2031},   # 当前周期（预测）
]

# 基钦周期（库存周期，3-4年）
# 中国库存周期约3.5年
KITCHIN_CYCLES = [
    {"start": 2016, "peak": 2017, "trough": 2019},
    {"start": 2019, "peak": 2021, "trough": 2023},   # 疫情干扰
    {"start": 2023, "peak": 2024, "trough": 2025},   # 当前周期
    {"start": 2025, "peak": 2026, "trough": 2027},   # 预测
]


# ---------------------------------------------------------------------------
# 核心类
# ---------------------------------------------------------------------------

class CyclePhaseEvaluator:
    """周期阶段评估器"""

    def __init__(self):
        pass

    def evaluate_kondratiev(self) -> CyclePhase:
        """评估康波周期"""
        return CyclePhase(
            cycle_name="康德拉季耶夫长波",
            cycle_type="kondratiev",
            period_years=55,
            current_phase=KONDRATIEV_2026["current_phase"],
            phase_progress=KONDRATIEV_2026["phase_progress"],
            direction=KONDRATIEV_2026["direction"],
            confidence=KONDRATIEV_2026["confidence"],
            description=KONDRATIEV_2026["description"],
        )

    def evaluate_juglar(self, year: int = 2026) -> CyclePhase:
        """评估朱格拉周期（设备投资周期）"""
        # 找到当前所处周期
        current_cycle = None
        for cycle in JUGLAR_CYCLES:
            if cycle["start"] <= year <= cycle["trough"]:
                current_cycle = cycle
                break

        if current_cycle is None:
            # 默认最新周期
            current_cycle = JUGLAR_CYCLES[-1]

        # 判断阶段
        total = current_cycle["trough"] - current_cycle["start"]
        elapsed = year - current_cycle["start"]
        progress = elapsed / total if total > 0 else 0

        if progress < 0.3:
            phase = "复苏期"
            direction = "up"
            desc = "设备投资开始回暖，资本开支逐步恢复"
        elif progress < 0.6:
            phase = "繁荣期"
            direction = "up"
            desc = "设备投资加速，产能扩张"
        elif progress < 0.8:
            phase = "衰退期"
            direction = "down"
            desc = "设备投资见顶回落，产能过剩"
        else:
            phase = "萧条期"
            direction = "down"
            desc = "设备投资收缩，去产能"

        # 2025-2027年处于朱格拉周期触底回升阶段
        if 2025 <= year <= 2027:
            phase = "复苏期"
            direction = "up"
            desc = "设备投资触底回升，新一轮资本开支周期启动"
            progress = (year - 2025) / 6  # 预计2025-2031为完整周期

        return CyclePhase(
            cycle_name="朱格拉周期（设备投资）",
            cycle_type="juglar",
            period_years=9,
            current_phase=phase,
            phase_progress=progress,
            direction=direction,
            confidence="medium",
            description=desc,
        )

    def evaluate_kitchin(self, year: int = 2026) -> CyclePhase:
        """评估基钦周期（库存周期）"""
        current_cycle = None
        for cycle in KITCHIN_CYCLES:
            if cycle["start"] <= year <= cycle["trough"]:
                current_cycle = cycle
                break

        if current_cycle is None:
            current_cycle = KITCHIN_CYCLES[-1]

        total = current_cycle["trough"] - current_cycle["start"]
        elapsed = year - current_cycle["start"]
        progress = elapsed / total if total > 0 else 0

        # 2025-2027年库存周期
        if 2025 <= year <= 2027:
            phase = "补库存"
            direction = "up"
            desc = "企业开始补库存，库存周期上行"
            progress = (year - 2025) / 3

        return CyclePhase(
            cycle_name="基钦周期（库存）",
            cycle_type="kitchin",
            period_years=3,
            current_phase=phase,
            phase_progress=progress,
            direction=direction,
            confidence="medium",
            description=desc,
        )

    def evaluate_kuznets(self, year: int = 2026) -> CyclePhase:
        """评估库兹涅茨周期（房地产周期，15-25年）"""
        # 中国房地产周期约20年
        # 上轮起点1998（房改），高点2009-2010，低点2015-2016
        # 本轮起点2016（棚改），高点2021，预计低点2026-2027

        if 2025 <= year <= 2027:
            phase = "触底期"
            direction = "flat"
            progress = (year - 2025) / 3
            desc = "房地产周期触底，政策托底，市场寻找新平衡"
        elif year > 2027:
            phase = "复苏期"
            direction = "up"
            progress = min(1.0, (year - 2027) / 5)
            desc = "房地产周期逐步回暖，新模式确立"
        else:
            phase = "衰退期"
            direction = "down"
            progress = 0.8
            desc = "房地产周期下行"

        return CyclePhase(
            cycle_name="库兹涅茨周期（房地产）",
            cycle_type="kuznets",
            period_years=20,
            current_phase=phase,
            phase_progress=progress,
            direction=direction,
            confidence="low",  # 房地产周期受政策影响大
            description=desc,
        )

    def calculate_resonance(self, phases: List[CyclePhase]) -> ResonanceResult:
        """计算周期共振强度"""
        up_cycles = [p for p in phases if p.direction == "up"]
        down_cycles = [p for p in phases if p.direction == "down"]
        flat_cycles = [p for p in phases if p.direction == "flat"]

        up_count = len(up_cycles)
        down_count = len(down_cycles)
        total = len(phases)

        # 共振评分：同向周期越多，共振越强
        if up_count >= 3:
            strength = "强共振"
            score = 80 + up_count * 5
            position = "高仓位"
            pos_range = (0.60, 0.80)
            risk = "中等"
            notes = "多周期同向上行，趋势明确，可积极进攻"
        elif up_count == 2:
            strength = "中共振"
            score = 60 + up_count * 5
            position = "中仓位"
            pos_range = (0.40, 0.60)
            risk = "中等"
            notes = "两周期同向，趋势较明确，可适度进攻"
        elif up_count == 1:
            strength = "弱共振"
            score = 30 + up_count * 5
            position = "低仓位"
            pos_range = (0.20, 0.40)
            risk = "中高"
            notes = "仅一周期明确上行，其他周期方向不明，需谨慎"
        else:
            strength = "无共振"
            score = 10
            position = "极低仓位"
            pos_range = (0.00, 0.20)
            risk = "高"
            notes = "周期方向混乱或全部下行，建议空仓或极低仓位"

        aligned = [p.cycle_name for p in up_cycles]
        opposed = [p.cycle_name for p in down_cycles]

        return ResonanceResult(
            resonance_strength=strength,
            resonance_score=min(100, score),
            aligned_cycles=aligned,
            opposed_cycles=opposed,
            recommended_position=position,
            position_range=pos_range,
            risk_level=risk,
            notes=notes,
        )

    def evaluate_all(self, year: int = 2026) -> Tuple[List[CyclePhase], ResonanceResult]:
        """评估所有周期"""
        phases = [
            self.evaluate_kondratiev(),
            self.evaluate_juglar(year),
            self.evaluate_kitchin(year),
            self.evaluate_kuznets(year),
        ]
        resonance = self.calculate_resonance(phases)
        return phases, resonance


# ---------------------------------------------------------------------------
# 报告生成
# ---------------------------------------------------------------------------

def generate_resonance_report(phases: List[CyclePhase], resonance: ResonanceResult) -> str:
    """生成周期共振报告"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    lines = [
        f"# 周期共振分析报告",
        f"",
        f"**生成时间**: {now}",
        f"",
        "---",
        "",
        "## 一、多周期嵌套评估",
        "",
        "| 周期 | 类型 | 长度 | 当前阶段 | 进度 | 方向 | 置信度 | 描述 |",
        "|------|------|------|----------|------|------|--------|------|",
    ]

    for p in phases:
        icon = "📈" if p.direction == "up" else ("📉" if p.direction == "down" else "➡️")
        lines.append(
            f"| {p.cycle_name} | {p.cycle_type} | {p.period_years}年 | {p.current_phase} | "
            f"{p.phase_progress:.0%} | {icon} {p.direction} | {p.confidence} | {p.description} |"
        )

    lines.extend([
        "",
        "## 二、周期共振分析",
        "",
        f"| 维度 | 内容 |",
        f"|------|------|",
        f"| 共振强度 | **{resonance.resonance_strength}** |",
        f"| 共振评分 | {resonance.resonance_score}/100 |",
        f"| 同向周期 | {', '.join(resonance.aligned_cycles) if resonance.aligned_cycles else '无'} |",
        f"| 反向周期 | {', '.join(resonance.opposed_cycles) if resonance.opposed_cycles else '无'} |",
        f"| 建议仓位 | **{resonance.recommended_position}** |",
        f"| 仓位区间 | {resonance.position_range[0]:.0%} - {resonance.position_range[1]:.0%} |",
        f"| 风险等级 | {resonance.risk_level} |",
        f"",
        "### 投资建议",
        "",
        f"{resonance.notes}",
        "",
        "## 三、四周期嵌套框架",
        "",
        "```",
        "康波周期定位（战略层，50-60年）",
        "    ↓",
        "库兹涅茨周期判断（房地产周期，15-25年）",
        "    ↓",
        "朱格拉周期判断（设备投资周期，8-10年）",
        "    ↓",
        "基钦周期择时（库存周期，3-4年）",
        "```",
        "",
        "## 四、2026年具体判断",
        "",
        "| 周期 | 阶段 | 投资含义 |",
        "|------|------|----------|",
        "| 康波（50-60年） | 复苏期起点 | 长期布局窗口，AI/新能源为核心 |",
        "| 库兹涅茨（20年） | 触底期 | 房地产寻底，政策托底，耐心等待 |",
        "| 朱格拉（9年） | 复苏期 | 设备投资回升，制造业景气上行 |",
        "| 基钦（3年） | 补库存 | 库存周期上行，短期利好周期股 |",
        "",
        "### 综合判断",
        "",
        "- **康波复苏** + **朱格拉复苏** + **基钦上行** = 三周期同向（2.5个周期上行）",
        "- **库兹涅茨触底** = 房地产拖累，但政策对冲",
        "- **共振结论**：**中共振偏强**，建议**中高仓位**（50-70%）",
        "- **核心策略**：左侧布局成长，工业金属+AI成长为主线",
        "",
        "---",
        "",
        "*本报告基于周期理论研究，仅供参考，不构成投资建议。*",
        "",
    ])

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="周期阶段评估系统")
    parser.add_argument("--report", action="store_true", help="生成共振分析报告")
    parser.add_argument("--resonance", action="store_true", help="显示共振结果")
    parser.add_argument("--year", type=int, default=2026, help="指定年份")
    args = parser.parse_args()

    evaluator = CyclePhaseEvaluator()
    phases, resonance = evaluator.evaluate_all(args.year)

    if args.report:
        report = generate_resonance_report(phases, resonance)
        report_path = REPORTS_DIR / f"cycle_resonance_report_{datetime.now().strftime('%Y%m%d')}.md"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"报告已保存: {report_path}")
        print("\n报告预览（前1500字符）：")
        print(report[:1500])
    elif args.resonance:
        print(f"周期共振分析 ({args.year}年)")
        print("=" * 50)
        print(f"共振强度: {resonance.resonance_strength}")
        print(f"共振评分: {resonance.resonance_score}/100")
        print(f"建议仓位: {resonance.recommended_position} ({resonance.position_range[0]:.0%}-{resonance.position_range[1]:.0%})")
        print(f"风险等级: {resonance.risk_level}")
        print(f"\n同向周期: {', '.join(resonance.aligned_cycles)}")
        print(f"反向周期: {', '.join(resonance.opposed_cycles)}")
        print(f"\n{resonance.notes}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
