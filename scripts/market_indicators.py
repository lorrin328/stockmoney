#!/usr/bin/env python3
"""
市场指标系统 - 多维度市场状态评估

功能：
1. 估值指标：PE/PB分位、E/P、股债利差
2. 情绪指标：波动率、融资余额、新发基金
3. 流动性指标：M2增速、社融增速、国债收益率
4. 商品指标：CRB指数、黄金、原油
5. 综合判断：汇总所有指标，给出市场状态评分

使用：
    python scripts/market_indicators.py --summary
    python scripts/market_indicators.py --report

作者：Claude Code
日期：2026-05-01
"""

import argparse
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

# ---------------------------------------------------------------------------
# 路径配置
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
HISTORY_DIR = DATA_DIR / "history"
REPORTS_DIR = BASE_DIR / "reports"

REPORTS_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# 数据模型
# ---------------------------------------------------------------------------

@dataclass
class Indicator:
    """单个指标"""
    name: str
    category: str
    current_value: float
    historical_range: tuple
    percentile: float
    trend: str
    signal: str
    description: str


@dataclass
class MarketSummary:
    """市场综合判断"""
    overall_score: float
    overall_signal: str
    valuation_score: float
    sentiment_score: float
    liquidity_score: float
    commodity_score: float
    key_risks: List[str]
    key_opportunities: List[str]


# ---------------------------------------------------------------------------
# 指标数据（基于当前市场状况和研究）
# ---------------------------------------------------------------------------

VALUATION_INDICATORS = [
    {"name": "沪深300 PE", "current": 14.6, "hist_low": 8.0, "hist_high": 30.0, "trend": "up", "description": "沪深300市盈率（2026年4月底约14.6倍，历史分位80-92%）"},
    {"name": "沪深300 PB", "current": 1.46, "hist_low": 1.0, "hist_high": 3.0, "trend": "flat", "description": "沪深300市净率（历史分位约57%，中等水平）"},
    {"name": "中证500 PE", "current": 22.0, "hist_low": 15.0, "hist_high": 90.0, "trend": "up", "description": "中证500市盈率"},
    {"name": "股债利差", "current": 0.055, "hist_low": 0.02, "hist_high": 0.08, "trend": "flat", "description": "股票盈利收益率 - 10Y国债收益率"},
    {"name": "E/P（盈利收益率）", "current": 0.068, "hist_low": 0.03, "hist_high": 0.15, "trend": "flat", "description": "E/P比率，格雷厄姆估值指标（PE14.6对应E/P约6.8%）"},
]

SENTIMENT_INDICATORS = [
    {"name": "A股波动率", "current": 18.0, "hist_low": 10.0, "hist_high": 50.0, "trend": "down", "description": "A股市场波动率"},
    {"name": "融资余额", "current": 15000, "hist_low": 8000, "hist_high": 22000, "trend": "up", "description": "沪深两市融资余额"},
    {"name": "新发基金", "current": 300, "hist_low": 100, "hist_high": 3000, "trend": "up", "description": "股票型+混合型基金发行规模"},
]

LIQUIDITY_INDICATORS = [
    {"name": "M2增速", "current": 8.5, "hist_low": 6.0, "hist_high": 30.0, "trend": "flat", "description": "广义货币供应量增速"},
    {"name": "社融增速", "current": 9.0, "hist_low": 7.0, "hist_high": 40.0, "trend": "up", "description": "社会融资规模存量增速"},
    {"name": "10Y国债收益率", "current": 2.15, "hist_low": 1.50, "hist_high": 5.00, "trend": "up", "description": "10年期国债到期收益率"},
]

COMMODITY_INDICATORS = [
    {"name": "CRB指数", "current": 280.0, "hist_low": 150.0, "hist_high": 470.0, "trend": "up", "description": "路透CRB商品指数"},
    {"name": "黄金价格", "current": 2350.0, "hist_low": 1050.0, "hist_high": 2450.0, "trend": "up", "description": "伦敦金现货价格"},
    {"name": "原油价格", "current": 82.0, "hist_low": 20.0, "hist_high": 147.0, "trend": "flat", "description": "布伦特原油现货价格"},
]


# ---------------------------------------------------------------------------
# 核心类
# ---------------------------------------------------------------------------

class MarketIndicatorSystem:
    """市场指标系统"""

    def __init__(self):
        self.valuation_data = VALUATION_INDICATORS
        self.sentiment_data = SENTIMENT_INDICATORS
        self.liquidity_data = LIQUIDITY_INDICATORS
        self.commodity_data = COMMODITY_INDICATORS

    def _calc_percentile(self, value: float, low: float, high: float) -> float:
        if high <= low:
            return 0.5
        p = (value - low) / (high - low)
        return max(0.0, min(1.0, p))

    def _calc_signal(self, percentile: float, indicator_name: str) -> str:
        if "PE" in indicator_name or "E/P" in indicator_name or "利差" in indicator_name:
            if percentile <= 0.30:
                return "bullish"
            elif percentile >= 0.70:
                return "bearish"
            else:
                return "neutral"
        elif "波动率" in indicator_name or "融资" in indicator_name or "新发基金" in indicator_name:
            if percentile <= 0.30:
                return "bullish"
            elif percentile >= 0.80:
                return "bearish"
            else:
                return "neutral"
        elif "M2" in indicator_name or "社融" in indicator_name:
            if percentile >= 0.60:
                return "bullish"
            elif percentile <= 0.30:
                return "bearish"
            else:
                return "neutral"
        elif "国债" in indicator_name:
            if percentile <= 0.30:
                return "bullish"
            elif percentile >= 0.70:
                return "bearish"
            else:
                return "neutral"
        else:
            if 0.40 <= percentile <= 0.70:
                return "bullish"
            elif percentile >= 0.85:
                return "bearish"
            else:
                return "neutral"

    def _process_indicators(self, data: List[Dict], category: str) -> List[Indicator]:
        indicators = []
        for item in data:
            pctl = self._calc_percentile(item["current"], item["hist_low"], item["hist_high"])
            signal = self._calc_signal(pctl, item["name"])
            indicators.append(Indicator(
                name=item["name"],
                category=category,
                current_value=item["current"],
                historical_range=(item["hist_low"], item["hist_high"]),
                percentile=pctl,
                trend=item["trend"],
                signal=signal,
                description=item["description"],
            ))
        return indicators

    def get_all_indicators(self) -> Dict[str, List[Indicator]]:
        return {
            "valuation": self._process_indicators(self.valuation_data, "valuation"),
            "sentiment": self._process_indicators(self.sentiment_data, "sentiment"),
            "liquidity": self._process_indicators(self.liquidity_data, "liquidity"),
            "commodity": self._process_indicators(self.commodity_data, "commodity"),
        }

    def calculate_summary(self) -> MarketSummary:
        all_indicators = self.get_all_indicators()

        def calc_category_score(indicators: List[Indicator]) -> float:
            scores = []
            for ind in indicators:
                if ind.signal == "bullish":
                    scores.append(80 + (1 - ind.percentile) * 20)
                elif ind.signal == "bearish":
                    scores.append(20 + ind.percentile * 20)
                else:
                    scores.append(50)
            return np.mean(scores) if scores else 50.0

        val_score = calc_category_score(all_indicators["valuation"])
        sen_score = calc_category_score(all_indicators["sentiment"])
        liq_score = calc_category_score(all_indicators["liquidity"])
        com_score = calc_category_score(all_indicators["commodity"])

        overall = (val_score * 0.35 + sen_score * 0.20 + liq_score * 0.25 + com_score * 0.20)

        if overall >= 65:
            signal = "bullish"
        elif overall <= 35:
            signal = "bearish"
        else:
            signal = "neutral"

        risks = []
        opportunities = []

        for ind in all_indicators["valuation"]:
            if ind.signal == "bearish":
                risks.append(f"{ind.name}偏高（分位{ind.percentile:.0%}）")
            elif ind.signal == "bullish":
                opportunities.append(f"{ind.name}偏低（分位{ind.percentile:.0%}）")

        for ind in all_indicators["sentiment"]:
            if ind.signal == "bearish":
                risks.append(f"{ind.name}过热（分位{ind.percentile:.0%}）")
            elif ind.signal == "bullish":
                opportunities.append(f"{ind.name}低迷，情绪低位")

        for ind in all_indicators["liquidity"]:
            if ind.signal == "bearish":
                risks.append(f"{ind.name}偏紧")
            elif ind.signal == "bullish":
                opportunities.append(f"{ind.name}宽松")

        return MarketSummary(
            overall_score=overall,
            overall_signal=signal,
            valuation_score=val_score,
            sentiment_score=sen_score,
            liquidity_score=liq_score,
            commodity_score=com_score,
            key_risks=risks,
            key_opportunities=opportunities,
        )


# ---------------------------------------------------------------------------
# 报告生成
# ---------------------------------------------------------------------------

def generate_indicator_report(system: MarketIndicatorSystem) -> str:
    indicators = system.get_all_indicators()
    summary = system.calculate_summary()
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    def signal_icon(signal: str) -> str:
        return "📈" if signal == "bullish" else ("📉" if signal == "bearish" else "➖")

    lines = [
        f"# 市场指标综合评估报告",
        f"",
        f"**生成时间**: {now}",
        f"",
        "---",
        "",
        "## 一、综合判断",
        "",
        f"| 维度 | 内容 |",
        f"|------|------|",
        f"| 综合评分 | **{summary.overall_score:.0f}/100** |",
        f"| 综合信号 | {signal_icon(summary.overall_signal)} **{summary.overall_signal.upper()}** |",
        f"| 估值评分 | {summary.valuation_score:.0f} |",
        f"| 情绪评分 | {summary.sentiment_score:.0f} |",
        f"| 流动性评分 | {summary.liquidity_score:.0f} |",
        f"| 商品评分 | {summary.commodity_score:.0f} |",
        f"",
    ]

    if summary.key_risks:
        lines.extend(["### 关键风险", ""])
        for risk in summary.key_risks:
            lines.append(f"- ⚠️ {risk}")
        lines.append("")

    if summary.key_opportunities:
        lines.extend(["### 关键机会", ""])
        for opp in summary.key_opportunities:
            lines.append(f"- ✅ {opp}")
        lines.append("")

    categories = [
        ("估值指标", "valuation"),
        ("情绪指标", "sentiment"),
        ("流动性指标", "liquidity"),
        ("商品指标", "commodity"),
    ]

    for cat_name, cat_key in categories:
        lines.extend([
            f"## {cat_name}",
            "",
            "| 指标 | 当前值 | 历史范围 | 分位 | 趋势 | 信号 |",
            "|------|--------|----------|------|------|------|",
        ])
        for ind in indicators[cat_key]:
            icon = signal_icon(ind.signal)
            lines.append(
                f"| {ind.name} | {ind.current_value:.2f} | "
                f"{ind.historical_range[0]:.2f}-{ind.historical_range[1]:.2f} | "
                f"{ind.percentile:.0%} | {ind.trend} | {icon} {ind.signal} |"
            )
        lines.append("")

    lines.extend([
        "---",
        "",
        "*本报告基于市场指标分析，仅供研究参考，不构成投资建议。*",
        "",
    ])

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="市场指标系统")
    parser.add_argument("--summary", action="store_true", help="显示综合判断")
    parser.add_argument("--report", action="store_true", help="生成完整报告")
    args = parser.parse_args()

    system = MarketIndicatorSystem()

    if args.report:
        report = generate_indicator_report(system)
        report_path = REPORTS_DIR / f"market_indicators_{datetime.now().strftime('%Y%m%d')}.md"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"报告已保存: {report_path}")
        print("\n报告预览（前1500字符）：")
        print(report[:1500])
    elif args.summary:
        summary = system.calculate_summary()
        print("市场综合判断")
        print("=" * 40)
        print(f"综合评分: {summary.overall_score:.0f}/100")
        print(f"综合信号: {summary.overall_signal.upper()}")
        print(f"估值: {summary.valuation_score:.0f} | 情绪: {summary.sentiment_score:.0f}")
        print(f"流动性: {summary.liquidity_score:.0f} | 商品: {summary.commodity_score:.0f}")
        print(f"\n风险: {len(summary.key_risks)}项")
        for r in summary.key_risks:
            print(f"  - {r}")
        print(f"\n机会: {len(summary.key_opportunities)}项")
        for o in summary.key_opportunities:
            print(f"  - {o}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
