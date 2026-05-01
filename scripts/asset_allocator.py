#!/usr/bin/env python3
"""
资产配置决策系统 - 基于康波周期的资产类别与ETF映射

功能：
1. 根据周期阶段确定资产类别权重
2. 将资产类别映射到具体ETF标的
3. 计算目标仓位与当前仓位的偏离度
4. 生成再平衡建议

使用：
    python scripts/asset_allocator.py --allocation
    python scripts/asset_allocator.py --report

作者：Claude Code
日期：2026-05-01
"""

import argparse
import json
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

# ---------------------------------------------------------------------------
# 路径配置
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
CONFIG_PATH = DATA_DIR / "portfolio_config.json"
REPORTS_DIR = BASE_DIR / "reports"

REPORTS_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# 数据模型
# ---------------------------------------------------------------------------

@dataclass
class AssetClassWeight:
    """单个资产类别权重"""
    asset_class: str
    class_cn: str
    weight_min: float
    weight_max: float
    weight_mid: float
    reason: str


@dataclass
class ETFAllocation:
    """ETF具体配置"""
    code: str
    name: str
    asset_class: str
    target_weight: float
    current_weight: float
    deviation: float
    action: str
    reason: str


@dataclass
class AllocationPlan:
    """完整资产配置方案"""
    phase: str
    phase_cn: str
    overall_position: float
    position_range: Tuple[float, float]
    asset_weights: List[AssetClassWeight]
    etf_allocations: List[ETFAllocation]
    rebalance_needed: bool
    key_notes: List[str]


# ---------------------------------------------------------------------------
# 资产配置矩阵（康波四阶段 × 资产类别）
# ---------------------------------------------------------------------------

# 资产类别定义
ASSET_CLASSES = {
    "stock": {"name": "股票", "sub_types": ["a_large", "a_mid", "hk_tech", "growth"]},
    "bond": {"name": "债券", "sub_types": ["gov_bond", "credit_bond"]},
    "commodity": {"name": "大宗商品", "sub_types": ["industrial_metal", "energy"]},
    "gold": {"name": "黄金", "sub_types": ["gold"]},
    "cash": {"name": "现金", "sub_types": ["cash"]},
    "defensive": {"name": "防御", "sub_types": ["dividend", "bank"]},
}

# 四阶段资产配置矩阵（min, mid, max）
PHASE_ALLOCATION_MATRIX = {
    "繁荣期": {
        "stock": (0.40, 0.50, 0.60, "超配权益，享受泡沫"),
        "bond": (0.10, 0.15, 0.20, "低配债券，利率上行"),
        "commodity": (0.15, 0.20, 0.25, "超配商品，通胀驱动"),
        "gold": (0.05, 0.08, 0.10, "低配黄金"),
        "cash": (0.05, 0.07, 0.10, "保持流动性"),
        "defensive": (0.05, 0.08, 0.10, "适度防御"),
    },
    "衰退期": {
        "stock": (0.20, 0.25, 0.35, "逐步减仓，保留核心"),
        "bond": (0.30, 0.35, 0.40, "增配债券，避险"),
        "commodity": (0.10, 0.15, 0.20, "阶段性超配"),
        "gold": (0.10, 0.12, 0.15, "开始建仓"),
        "cash": (0.10, 0.13, 0.20, "保持流动性"),
        "defensive": (0.10, 0.15, 0.20, "防御为主"),
    },
    "萧条期": {
        "stock": (0.10, 0.15, 0.20, "低配权益"),
        "bond": (0.30, 0.35, 0.40, "标配/超配债券"),
        "commodity": (0.05, 0.10, 0.15, "低配商品"),
        "gold": (0.15, 0.20, 0.25, "超配黄金避险"),
        "cash": (0.20, 0.25, 0.30, "现金为王"),
        "defensive": (0.10, 0.15, 0.20, "防御优先"),
    },
    "复苏期": {
        "stock": (0.30, 0.40, 0.50, "逐步加仓→超配"),
        "bond": (0.15, 0.20, 0.25, "逐步减仓"),
        "commodity": (0.20, 0.25, 0.35, "超配商品"),
        "gold": (0.10, 0.12, 0.15, "逐步减仓"),
        "cash": (0.05, 0.08, 0.10, "低配现金"),
        "defensive": (0.05, 0.08, 0.10, "适度防御"),
    },
}

# ETF 到资产类别的映射
ETF_ASSET_MAP = {
    # 股票类
    "510300": {"asset": "stock", "sub": "a_large", "weight_factor": 1.0, "name": "沪深300ETF"},
    "560610": {"asset": "stock", "sub": "a_mid", "weight_factor": 1.0, "name": "中证A500ETF"},
    "513130": {"asset": "stock", "sub": "hk_tech", "weight_factor": 1.0, "name": "恒生科技ETF"},
    "159857": {"asset": "commodity", "sub": "energy", "weight_factor": 1.0, "name": "光伏ETF"},
    "159755": {"asset": "commodity", "sub": "energy", "weight_factor": 0.7, "name": "电池ETF"},
    "159992": {"asset": "stock", "sub": "growth", "weight_factor": 1.0, "name": "创新药ETF"},
    "159898": {"asset": "stock", "sub": "growth", "weight_factor": 0.7, "name": "医疗器械ETF"},
    "562500": {"asset": "stock", "sub": "growth", "weight_factor": 0.7, "name": "机器人ETF"},
    "159611": {"asset": "stock", "sub": "defensive", "weight_factor": 0.7, "name": "电力ETF"},
    "159995": {"asset": "stock", "sub": "growth", "weight_factor": 0.7, "name": "芯片ETF"},
    # 防御类
    "512890": {"asset": "defensive", "sub": "dividend", "weight_factor": 1.0, "name": "红利低波ETF"},
    "512800": {"asset": "defensive", "sub": "bank", "weight_factor": 0.7, "name": "银行ETF"},
    # 黄金
    "518880": {"asset": "gold", "sub": "gold", "weight_factor": 1.0, "name": "黄金ETF"},
    # 证券（顺周期，归类为股票）
    "512880": {"asset": "stock", "sub": "a_large", "weight_factor": 0.5, "name": "证券ETF"},
}

# 当前组合默认配置（90万组合）
DEFAULT_PORTFOLIO = {
    "510300": 11.1, "560610": 11.1, "513130": 11.1,
    "159857": 8.9, "159755": 6.7, "159992": 8.9,
    "159898": 5.6, "562500": 5.6, "159611": 4.4,
    "159995": 4.4, "512890": 8.9, "512800": 5.6,
    "518880": 4.4, "512880": 3.3,
}


# ---------------------------------------------------------------------------
# 核心类
# ---------------------------------------------------------------------------

class AssetAllocator:
    """资产配置决策器"""

    def __init__(self, portfolio_weights: Optional[Dict[str, float]] = None):
        self.portfolio = portfolio_weights or DEFAULT_PORTFOLIO.copy()
        self.matrix = PHASE_ALLOCATION_MATRIX
        self.etf_map = ETF_ASSET_MAP

    def get_asset_allocation(self, phase: str, resonance_strength: str = "medium") -> Dict[str, Dict]:
        """根据周期阶段获取资产类别配置"""
        phase = phase.replace("期", "") + "期" if not phase.endswith("期") else phase
        if phase not in self.matrix:
            phase = "复苏期"  # 默认复苏期

        allocation = {}
        for asset, (w_min, w_mid, w_max, reason) in self.matrix[phase].items():
            # 根据共振强度调整
            if resonance_strength == "强共振":
                weight = w_max
            elif resonance_strength == "弱共振":
                weight = w_min
            else:
                weight = w_mid

            allocation[asset] = {
                "weight": weight,
                "range": (w_min, w_max),
                "reason": reason,
            }

        return allocation

    def map_to_etfs(self, asset_allocation: Dict[str, Dict], total_capital: float = 900000) -> List[ETFAllocation]:
        """将资产类别映射到具体ETF"""
        etf_allocs = []

        # 按资产类别分组ETF
        asset_etfs = {k: [] for k in ASSET_CLASSES.keys()}
        for code, info in self.etf_map.items():
            asset = info["asset"]
            if asset in asset_etfs:
                asset_etfs[asset].append(code)

        # 计算每个ETF的目标权重
        for code, target_pct in self.portfolio.items():
            info = self.etf_map.get(code, {})
            asset = info.get("asset", "stock")
            asset_weight = asset_allocation.get(asset, {}).get("weight", 0.15)

            # 组合默认权重 × 资产类别调整因子
            # 如果资产类别权重提升，相应提升ETF权重
            base_weight = target_pct / 100.0

            etf_allocs.append(ETFAllocation(
                code=code,
                name=info.get("name", code),
                asset_class=asset,
                target_weight=base_weight,
                current_weight=0.0,
                deviation=0.0,
                action="持有",
                reason=f"{ASSET_CLASSES.get(asset, {}).get('name', asset)}配置{asset_weight:.0%}",
            ))

        return etf_allocs

    def calculate_deviation(self, etf_allocs: List[ETFAllocation],
                            current_positions: Optional[Dict[str, Dict]] = None) -> List[ETFAllocation]:
        """计算目标仓位与实际仓位的偏离度"""
        if current_positions is None:
            return etf_allocs

        total_value = sum(
            pos.get("shares", 0) * pos.get("price", 0)
            for pos in current_positions.values()
        )

        for etf in etf_allocs:
            pos = current_positions.get(etf.code, {})
            current_value = pos.get("shares", 0) * pos.get("price", 0)
            current_weight = current_value / total_value if total_value > 0 else 0

            etf.current_weight = current_weight
            etf.deviation = current_weight - etf.target_weight

            if abs(etf.deviation) >= 0.05:
                etf.action = "加仓" if etf.deviation < 0 else "减仓"
            else:
                etf.action = "持有"

        return etf_allocs

    def generate_plan(self, phase: str = "复苏期",
                      resonance: str = "medium",
                      current_positions: Optional[Dict] = None,
                      total_capital: float = 900000) -> AllocationPlan:
        """生成完整资产配置方案"""
        asset_alloc = self.get_asset_allocation(phase, resonance)
        etf_allocs = self.map_to_etfs(asset_alloc, total_capital)
        etf_allocs = self.calculate_deviation(etf_allocs, current_positions)

        rebalance_needed = any(abs(e.deviation) >= 0.05 for e in etf_allocs)

        # 构建资产权重列表
        weights = []
        for asset, data in asset_alloc.items():
            weights.append(AssetClassWeight(
                asset_class=asset,
                class_cn=ASSET_CLASSES.get(asset, {}).get("name", asset),
                weight_min=data["range"][0],
                weight_max=data["range"][1],
                weight_mid=data["weight"],
                reason=data["reason"],
            ))

        # 关键提示
        notes = []
        if phase == "复苏期":
            notes.append("复苏期策略：左侧布局成长，工业金属+AI成长为主线")
            notes.append("股票仓位可逐步提升至40-50%，债券逐步减仓")
            notes.append("关注康波核心主题：AI算力、新能源、生物技术")
        elif phase == "繁荣期":
            notes.append("繁荣期策略：享受泡沫，逐步止盈")
            notes.append("股票超配至50-60%，关注通胀受益资产")
            notes.append("设置动态止盈，牛市后期降低仓位")
        elif phase == "衰退期":
            notes.append("衰退期策略：转向防御，保留流动性")
            notes.append("增配债券和黄金，股票减仓至20-30%")
            notes.append("关注高股息、低波动资产")
        elif phase == "萧条期":
            notes.append("萧条期策略：现金为王，黄金避险")
            notes.append("股票低配10-20%，债券超配，现金保持20-30%")
            notes.append("等待周期拐点信号，为复苏期布局做准备")

        if resonance == "强共振":
            notes.append("强共振：多周期同向，趋势明确，可积极进攻")
        elif resonance == "弱共振":
            notes.append("弱共振：趋势不明，需谨慎，控制仓位")

        # 仓位区间
        total_stock = sum(w.weight_mid for w in weights if w.asset_class in ("stock", "defensive"))
        position_range = (max(0.1, total_stock - 0.1), min(0.9, total_stock + 0.1))

        return AllocationPlan(
            phase=phase,
            phase_cn=phase,
            overall_position=total_stock,
            position_range=position_range,
            asset_weights=weights,
            etf_allocations=etf_allocs,
            rebalance_needed=rebalance_needed,
            key_notes=notes,
        )

    def get_phase_adjusted_weights(self, phase: str, base_weights: Dict[str, float]) -> Dict[str, float]:
        """根据周期阶段调整基础权重"""
        asset_alloc = self.get_asset_allocation(phase)
        adjusted = {}

        for code, base_w in base_weights.items():
            info = self.etf_map.get(code, {})
            asset = info.get("asset", "stock")
            factor = asset_alloc.get(asset, {}).get("weight", 0.15) / 0.15  # 相对于中性15%的调整
            adjusted[code] = base_w * factor

        # 归一化
        total = sum(adjusted.values())
        if total > 0:
            adjusted = {k: v / total * 100 for k, v in adjusted.items()}

        return adjusted


# ---------------------------------------------------------------------------
# 报告生成
# ---------------------------------------------------------------------------

def generate_allocation_report(plan: AllocationPlan, total_capital: float = 900000) -> str:
    """生成资产配置报告"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    lines = [
        f"# 资产配置决策报告",
        f"",
        f"**生成时间**: {now}",
        f"**当前阶段**: {plan.phase_cn}",
        f"**总资金**: {total_capital:,.0f}元",
        f"",
        "---",
        "",
        "## 一、资产类别配置",
        "",
        "| 资产类别 | 最低 | 目标 | 最高 | 配置理由 |",
        "|----------|------|------|------|----------|",
    ]

    for w in sorted(plan.asset_weights, key=lambda x: x.weight_mid, reverse=True):
        lines.append(
            f"| {w.class_cn} | {w.weight_min:.0%} | **{w.weight_mid:.0%}** | {w.weight_max:.0%} | {w.reason} |"
        )

    lines.extend([
        "",
        f"**建议总仓位**: {plan.overall_position:.0%}（区间 {plan.position_range[0]:.0%} - {plan.position_range[1]:.0%}）",
        "",
        "## 二、ETF配置方案",
        "",
        "| ETF | 代码 | 资产类别 | 目标权重 | 当前权重 | 偏离 | 操作 | 理由 |",
        "|-----|------|----------|----------|----------|------|------|------|",
    ])

    for e in sorted(plan.etf_allocations, key=lambda x: x.target_weight, reverse=True):
        dev_icon = "↑" if e.deviation > 0.05 else ("↓" if e.deviation < -0.05 else "=")
        lines.append(
            f"| {e.name} | {e.code} | {e.asset_class} | {e.target_weight:.1%} | "
            f"{e.current_weight:.1%} | {dev_icon} {e.deviation:+.1%} | {e.action} | {e.reason} |"
        )

    lines.extend([
        "",
        f"**再平衡需求**: {'是' if plan.rebalance_needed else '否'}（偏离≥5%触发）",
        "",
        "## 三、关键提示",
        "",
    ])

    for note in plan.key_notes:
        lines.append(f"- {note}")

    lines.extend([
        "",
        "## 四、四阶段配置对比",
        "",
        "| 阶段 | 股票 | 债券 | 商品 | 黄金 | 现金 | 防御 |",
        "|------|------|------|------|------|------|------|",
    ])

    for phase in ["复苏期", "繁荣期", "衰退期", "萧条期"]:
        row = [phase]
        for ac in ["stock", "bond", "commodity", "gold", "cash", "defensive"]:
            data = PHASE_ALLOCATION_MATRIX[phase].get(ac, (0, 0, 0, ""))
            row.append(f"{data[1]:.0%}")
        lines.append("| " + " | ".join(row) + " |")

    lines.extend([
        "",
        "---",
        "",
        "*本报告基于康波周期理论生成，仅供研究参考，不构成投资建议。*",
        "",
    ])

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="资产配置决策系统")
    parser.add_argument("--allocation", action="store_true", help="显示当前阶段配置")
    parser.add_argument("--report", action="store_true", help="生成完整配置报告")
    parser.add_argument("--phase", type=str, default="复苏期", help="指定周期阶段")
    parser.add_argument("--resonance", type=str, default="medium", help="共振强度 (strong/medium/weak)")
    args = parser.parse_args()

    allocator = AssetAllocator()

    if args.report:
        plan = allocator.generate_plan(phase=args.phase, resonance=args.resonance)
        report = generate_allocation_report(plan)
        report_path = REPORTS_DIR / f"asset_allocation_{datetime.now().strftime('%Y%m%d')}.md"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"报告已保存: {report_path}")
        print("\n报告预览（前2000字符）：")
        print(report[:2000])
    elif args.allocation:
        plan = allocator.generate_plan(phase=args.phase, resonance=args.resonance)
        print(f"资产配置方案 ({args.phase})")
        print("=" * 50)
        print(f"建议总仓位: {plan.overall_position:.0%}")
        print(f"再平衡需求: {'是' if plan.rebalance_needed else '否'}")
        print("\n资产类别配置:")
        for w in sorted(plan.asset_weights, key=lambda x: x.weight_mid, reverse=True):
            print(f"  {w.class_cn}: {w.weight_mid:.0%} ({w.weight_min:.0%}-{w.weight_max:.0%})")
        print("\nETF配置:")
        for e in sorted(plan.etf_allocations, key=lambda x: x.target_weight, reverse=True):
            print(f"  {e.code} {e.name}: 目标{e.target_weight:.1%} | 当前{e.current_weight:.1%} | {e.action}")
        print("\n关键提示:")
        for note in plan.key_notes:
            print(f"  - {note}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
