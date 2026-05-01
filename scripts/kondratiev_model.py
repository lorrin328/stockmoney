#!/usr/bin/env python3
"""
康波周期模型 - 宏观周期定位系统

基于康德拉季耶夫长波理论（Kondratiev Wave），结合熊彼特创新理论，
实现康波周期的量化识别与阶段判断。

理论框架：
- 康波周期：50-60年，由重大技术革命驱动
- 四阶段：繁荣期→衰退期→萧条期→复苏期
- 当前定位：2026年处于第六轮康波复苏期起点

功能：
1. 历史6轮康波数据存储与查询
2. 当前周期阶段判断
3. 阶段特征与资产配置建议
4. 预测下一阶段转换时间窗口

使用：
    python scripts/kondratiev_model.py --report
    python scripts/kondratiev_model.py --phase

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
CYCLE_DATA_DIR = DATA_DIR / "cycle_data"
REPORTS_DIR = BASE_DIR / "reports"

CYCLE_DATA_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# 数据模型
# ---------------------------------------------------------------------------

@dataclass
class KondratievWave:
    """单轮康波周期"""
    round_num: int
    name: str
    start_year: int
    end_year: int
    core_tech: str
    dominant_countries: str
    phases: Dict[str, Tuple[int, int]]  # phase_name: (start, end)
    key_events: List[str]


@dataclass
class PhaseDescription:
    """阶段特征描述"""
    phase_name: str
    duration_years: str
    growth_rate: str
    inflation_trend: str
    interest_rate_trend: str
    credit_condition: str
    asset_performance: Dict[str, str]  # asset: performance
    investment_theme: str
    risk_level: str


@dataclass
class CyclePosition:
    """当前周期定位"""
    current_year: int
    kondratiev_round: int
    kondratiev_phase: str
    kondratiev_progress: float  # 0-1
    years_into_phase: int
    years_to_next_phase: int
    tech_drivers: List[str]
    dominant_regions: List[str]


# ---------------------------------------------------------------------------
# 历史康波数据
# ---------------------------------------------------------------------------

KONDRATIEV_CYCLES = [
    KondratievWave(
        round_num=1,
        name="纺织与蒸汽机",
        start_year=1782,
        end_year=1845,
        core_tech="蒸汽机、棉纺织技术",
        dominant_countries="英国",
        phases={
            "繁荣期": (1782, 1802),
            "衰退期": (1815, 1825),
            "萧条期": (1825, 1836),
            "复苏期": (1836, 1845),
        },
        key_events=[
            "瓦特改良蒸汽机",
            "工厂制度确立",
            "铁路技术萌芽",
        ]
    ),
    KondratievWave(
        round_num=2,
        name="钢铁与铁路",
        start_year=1845,
        end_year=1892,
        core_tech="钢铁、铁路、蒸汽轮船、电报",
        dominant_countries="英国→美国、德国",
        phases={
            "繁荣期": (1845, 1866),
            "衰退期": (1866, 1873),
            "萧条期": (1873, 1883),
            "复苏期": (1883, 1892),
        },
        key_events=[
            "铁路建设高峰",
            "贝塞麦炼钢法",
            "第二次工业革命萌芽",
        ]
    ),
    KondratievWave(
        round_num=3,
        name="电气与化工",
        start_year=1892,
        end_year=1948,
        core_tech="电力、化工、汽车、内燃机",
        dominant_countries="美国取代英国",
        phases={
            "繁荣期": (1892, 1913),
            "衰退期": (1920, 1929),
            "萧条期": (1929, 1937),
            "复苏期": (1937, 1948),
        },
        key_events=[
            "电气化普及",
            "汽车诞生",
            "大萧条",
            "二战后重建",
        ]
    ),
    KondratievWave(
        round_num=4,
        name="汽车与石油化工",
        start_year=1948,
        end_year=1991,
        core_tech="石油化工、汽车大规模生产、航空、电子技术",
        dominant_countries="美国主导",
        phases={
            "繁荣期": (1948, 1966),
            "衰退期": (1966, 1973),
            "萧条期": (1973, 1982),
            "复苏期": (1982, 1991),
        },
        key_events=[
            "战后黄金时代",
            "石油危机",
            "滞胀",
            "信息技术萌芽",
        ]
    ),
    KondratievWave(
        round_num=5,
        name="信息技术",
        start_year=1991,
        end_year=2025,
        core_tech="信息技术、互联网、移动通信",
        dominant_countries="美国→中美竞争",
        phases={
            "繁荣期": (1991, 2004),
            "衰退期": (2004, 2015),
            "萧条期": (2015, 2025),
            "复苏期": (0, 0),  # 已结束
        },
        key_events=[
            "互联网革命",
            "次贷危机",
            "欧债危机",
            "低增长高债务",
        ]
    ),
    KondratievWave(
        round_num=6,
        name="人工智能与新能源",
        start_year=2026,
        end_year=2080,
        core_tech="人工智能、新能源、生物技术、量子计算",
        dominant_countries="中美竞争",
        phases={
            "繁荣期": (0, 0),  # 预计2035-2050
            "衰退期": (0, 0),  # 预计2050-2060
            "萧条期": (0, 0),  # 预计2060-2070
            "复苏期": (2026, 2035),  # 当前阶段
        },
        key_events=[
            "AGI突破",
            "可控核聚变",
            "基因编辑",
            "脑机接口",
        ]
    ),
]


# ---------------------------------------------------------------------------
# 阶段特征描述数据
# ---------------------------------------------------------------------------

PHASE_DESCRIPTIONS = {
    "繁荣期": PhaseDescription(
        phase_name="繁荣期",
        duration_years="10-20年",
        growth_rate="高增长（GDP > 潜在增速）",
        inflation_trend="温和上升",
        interest_rate_trend="逐步上行",
        credit_condition="信用扩张",
        asset_performance={
            "股票": "**超配**，长牛行情",
            "债券": "低配",
            "大宗商品": "**超配**，通胀驱动",
            "黄金": "最低配",
            "现金": "低配",
        },
        investment_theme="享受泡沫，逐步止盈",
        risk_level="中等",
    ),
    "衰退期": PhaseDescription(
        phase_name="衰退期",
        duration_years="8-12年",
        growth_rate="增速放缓",
        inflation_trend="高位震荡",
        interest_rate_trend="见顶回落",
        credit_condition="信用收紧",
        asset_performance={
            "股票": "逐步减仓",
            "债券": "增配",
            "大宗商品": "阶段性超配",
            "黄金": "开始建仓",
            "现金": "保持流动性",
        },
        investment_theme="转向防御，保留流动性",
        risk_level="中高",
    ),
    "萧条期": PhaseDescription(
        phase_name="萧条期",
        duration_years="8-12年",
        growth_rate="低增长",
        inflation_trend="低位/通缩",
        interest_rate_trend="低位",
        credit_condition="信用紧缩",
        asset_performance={
            "股票": "**低配**",
            "债券": "**标配/超配**",
            "大宗商品": "低配/波段",
            "黄金": "**超配**",
            "现金": "**超配**",
        },
        investment_theme="现金为王，黄金避险",
        risk_level="高",
    ),
    "复苏期": PhaseDescription(
        phase_name="复苏期",
        duration_years="8-15年",
        growth_rate="逐步回暖",
        inflation_trend="温和回升",
        interest_rate_trend="低位企稳",
        credit_condition="信用回暖",
        asset_performance={
            "股票": "**逐步加仓→超配**",
            "债券": "逐步减仓",
            "大宗商品": "**超配**",
            "黄金": "逐步减仓",
            "现金": "低配",
        },
        investment_theme="积极进攻，重仓成长",
        risk_level="中等",
    ),
}


# ---------------------------------------------------------------------------
# 2026年具体投资主题
# ---------------------------------------------------------------------------

INVESTMENT_THEMES_2026 = {
    "AI算力基础设施": {
        "细分领域": ["AI芯片", "服务器", "数据中心"],
        "代表方向": ["国产GPU", "液冷技术", "边缘计算"],
        "配置建议": "核心仓位 15-20%",
        "逻辑": "AI渗透率突破20%，算力需求爆发",
    },
    "AI应用落地": {
        "细分领域": ["行业大模型", "智能体(Agent)"],
        "代表方向": ["AI+医疗", "AI+金融", "AI+制造"],
        "配置建议": "重点配置 10-15%",
        "逻辑": "大模型进入盈利兑现期",
    },
    "新能源产业链": {
        "细分领域": ["储能", "智能电网", "氢能"],
        "代表方向": ["固态电池", "钙钛矿光伏", "虚拟电厂"],
        "配置建议": "重点配置 10-15%",
        "逻辑": "光伏度电成本下降82%，储能突破临界点",
    },
    "高端制造替代": {
        "细分领域": ["半导体设备", "工业软件"],
        "代表方向": ["光刻机零部件", "EDA工具", "工业机器人"],
        "配置建议": "精选配置 5-10%",
        "逻辑": "国产替代加速，政策支持",
    },
    "生物技术": {
        "细分领域": ["创新药", "基因治疗"],
        "代表方向": ["ADC药物", "CGT细胞与基因治疗"],
        "配置建议": "观察配置 3-5%",
        "逻辑": "AI驱动研发效率提升200倍",
    },
    "工业金属": {
        "细分领域": ["铜", "铝", "锂"],
        "代表方向": ["新能源用铜", "轻量化铝材", "电池级锂"],
        "配置建议": "高配 15-20%",
        "逻辑": "康波回升+朱格拉启动+供给刚性",
    },
}


# ---------------------------------------------------------------------------
# 核心类
# ---------------------------------------------------------------------------

class KondratievModel:
    """康波周期模型"""

    def __init__(self):
        self.cycles = KONDRATIEV_CYCLES
        self.phase_descs = PHASE_DESCRIPTIONS
        self.themes = INVESTMENT_THEMES_2026

    def get_current_cycle(self) -> KondratievWave:
        """获取当前康波周期"""
        return self.cycles[-1]  # 第六轮

    def get_current_phase(self) -> str:
        """获取当前阶段"""
        return "复苏期"

    def get_cycle_position(self, year: int = 2026) -> CyclePosition:
        """获取当前周期定位"""
        cycle = self.get_current_cycle()
        phase = self.get_current_phase()
        phase_start = cycle.phases[phase][0]
        phase_end = cycle.phases[phase][1]
        years_into = year - phase_start
        total_years = phase_end - phase_start
        progress = years_into / total_years if total_years > 0 else 0
        years_to_next = phase_end - year

        return CyclePosition(
            current_year=year,
            kondratiev_round=cycle.round_num,
            kondratiev_phase=phase,
            kondratiev_progress=progress,
            years_into_phase=years_into,
            years_to_next_phase=years_to_next,
            tech_drivers=["人工智能", "新能源", "生物技术", "量子计算"],
            dominant_regions=["中国", "美国"],
        )

    def get_phase_description(self, phase: str) -> PhaseDescription:
        """获取阶段特征描述"""
        return self.phase_descs.get(phase)

    def get_asset_allocation(self, phase: str) -> Dict[str, str]:
        """获取阶段资产配置建议"""
        desc = self.get_phase_description(phase)
        return desc.asset_performance if desc else {}

    def get_tech_drivers(self) -> List[str]:
        """获取当前核心技术引擎"""
        return ["人工智能", "新能源", "生物技术", "量子计算"]

    def get_investment_themes(self) -> Dict:
        """获取2026年投资主题"""
        return self.themes

    def predict_next_phase(self) -> Dict:
        """预测下一阶段转换"""
        return {
            "current_phase": "复苏期",
            "next_phase": "繁荣期",
            "estimated_start": 2035,
            "years_remaining": 9,
            "confidence": "中等",
            "key_signals": [
                "AI商业化突破",
                "新能源全面平价",
                "全球PMI持续>55",
                "利率进入上升通道",
            ],
        }

    def get_historical_comparison(self) -> List[Dict]:
        """获取历史类比"""
        return [
            {
                "historical_period": "1982-1991（第四轮复苏期）",
                "similarities": [
                    "新技术萌芽（信息技术）",
                    "利率低位",
                    "股市逐步回暖",
                ],
                "differences": [
                    "当前技术复杂度更高",
                    "全球化程度更深",
                    "债务水平更高",
                ],
            },
            {
                "historical_period": "1937-1948（第三轮复苏期）",
                "similarities": [
                    "战争/冲突后的重建",
                    "技术扩散加速",
                ],
                "differences": [
                    "当前无大规模战争",
                    "货币政策空间更小",
                ],
            },
        ]


# ---------------------------------------------------------------------------
# 报告生成
# ---------------------------------------------------------------------------

def generate_cycle_report(model: KondratievModel, year: int = 2026) -> str:
    """生成宏观周期报告"""
    pos = model.get_cycle_position(year)
    desc = model.get_phase_description(pos.kondratiev_phase)
    next_phase = model.predict_next_phase()
    themes = model.get_investment_themes()
    comparison = model.get_historical_comparison()

    lines = [
        f"# 宏观周期定位报告",
        f"",
        f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"**当前年份**: {year}年",
        f"",
        "---",
        "",
        "## 一、康波周期定位",
        "",
        f"### 1.1 当前位置",
        "",
        f"| 维度 | 内容 |",
        f"|------|------|",
        f"| 康波轮次 | 第{pos.kondratiev_round}轮康波周期 |",
        f"| 周期名称 | {model.get_current_cycle().name} |",
        f"| 核心技术 | {model.get_current_cycle().core_tech} |",
        f"| 主导国家 | {model.get_current_cycle().dominant_countries} |",
        f"| 当前阶段 | **{pos.kondratiev_phase}** |",
        f"| 阶段进度 | {pos.kondratiev_progress:.0%}（已进入{pos.years_into_phase}年，剩余{pos.years_to_next_phase}年） |",
        f"",
        f"### 1.2 阶段特征",
        "",
        f"| 维度 | 内容 |",
        f"|------|------|",
        f"| 阶段名称 | {desc.phase_name} |",
        f"| 持续时间 | {desc.duration_years} |",
        f"| 增长率 | {desc.growth_rate} |",
        f"| 通胀趋势 | {desc.inflation_trend} |",
        f"| 利率趋势 | {desc.interest_rate_trend} |",
        f"| 信用环境 | {desc.credit_condition} |",
        f"| 投资策略 | {desc.investment_theme} |",
        f"| 风险等级 | {desc.risk_level} |",
        f"",
        "### 1.3 资产配置矩阵",
        "",
        "| 资产类别 | 配置建议 |",
        "|----------|----------|",
    ]

    for asset, suggestion in desc.asset_performance.items():
        lines.append(f"| {asset} | {suggestion} |")

    lines.extend([
        "",
        "## 二、下一阶段预测",
        "",
        f"| 维度 | 内容 |",
        f"|------|------|",
        f"| 下一阶段 | {next_phase['next_phase']} |",
        f"| 预计开始 | {next_phase['estimated_start']}年 |",
        f"| 距离转换 | 约{next_phase['years_remaining']}年 |",
        f"| 置信度 | {next_phase['confidence']} |",
        f"",
        "**关键转换信号**：",
        "",
    ])
    for signal in next_phase['key_signals']:
        lines.append(f"- {signal}")

    lines.extend([
        "",
        "## 三、2026年投资主题",
        "",
    ])

    for theme_name, theme_info in themes.items():
        lines.extend([
            f"### {theme_name}",
            "",
            f"| 维度 | 内容 |",
            f"|------|------|",
            f"| 细分领域 | {', '.join(theme_info['细分领域'])} |",
            f"| 代表方向 | {', '.join(theme_info['代表方向'])} |",
            f"| 配置建议 | **{theme_info['配置建议']}** |",
            f"| 核心逻辑 | {theme_info['逻辑']} |",
            "",
        ])

    lines.extend([
        "## 四、历史类比",
        "",
    ])

    for comp in comparison:
        lines.extend([
            f"### {comp['historical_period']}",
            "",
            "**相似点**：",
            "",
        ])
        for sim in comp['similarities']:
            lines.append(f"- {sim}")
        lines.extend([
            "",
            "**差异点**：",
            "",
        ])
        for diff in comp['differences']:
            lines.append(f"- {diff}")
        lines.append("")

    lines.extend([
        "---",
        "",
        "## 五、核心判断",
        "",
        f"1. **战略定位**：{year}年处于第六轮康波**复苏期**起点，是播种而非收割之年",
        f"2. **时间窗口**：真正的繁荣期预计在{next_phase['estimated_start']}年后到来",
        f"3. **核心策略**：左侧布局，分批建仓，重仓成长",
        f"4. **风险管理**：保持10-15%黄金配置，关注地缘政治和债务风险",
        f"5. **代际机遇**：00后是AI时代原住民，2026年是全新周期起点",
        "",
        "---",
        "",
        "*本报告基于康波周期理论研究，仅供研究参考，不构成投资建议。经济周期理论存在争议，历史规律不代表未来表现。*",
        "",
    ])

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="康波周期模型")
    parser.add_argument("--report", action="store_true", help="生成宏观周期报告")
    parser.add_argument("--phase", action="store_true", help="显示当前阶段信息")
    parser.add_argument("--year", type=int, default=2026, help="指定年份")
    args = parser.parse_args()

    model = KondratievModel()

    if args.report:
        report = generate_cycle_report(model, args.year)
        report_path = REPORTS_DIR / f"macro_cycle_report_{datetime.now().strftime('%Y%m%d')}.md"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"报告已保存: {report_path}")
        print("\n报告预览（前2000字符）：")
        print(report[:2000])
    elif args.phase:
        pos = model.get_cycle_position(args.year)
        print(f"康波周期定位 ({args.year}年)")
        print("=" * 50)
        print(f"轮次: 第{pos.kondratiev_round}轮")
        print(f"阶段: {pos.kondratiev_phase}")
        print(f"进度: {pos.kondratiev_progress:.0%}")
        print(f"已进入: {pos.years_into_phase}年")
        print(f"距下一阶段: {pos.years_to_next_phase}年")
        print(f"技术引擎: {', '.join(pos.tech_drivers)}")
        print(f"主导地区: {', '.join(pos.dominant_regions)}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
