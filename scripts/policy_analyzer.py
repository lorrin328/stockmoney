#!/usr/bin/env python3
"""
政策与宏观环境分析系统 - 结合中国政策大势与国际环境

分析维度：
1. 十五五规划六大产业方向
2. 大宗商品趋势（铜/黄金/原油）
3. 美联储货币政策（降息/缩表）
4. 地缘政治与中美博弈
5. 综合政策评分与投资映射

使用：
    python scripts/policy_analyzer.py --report
    python scripts/policy_analyzer.py --summary

作者：Claude Code
日期：2026-05-01
"""

import argparse
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# 路径配置
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).parent.parent
REPORTS_DIR = BASE_DIR / "reports"
DATA_DIR = BASE_DIR / "data"

REPORTS_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# 数据模型
# ---------------------------------------------------------------------------

@dataclass
class PolicyFactor:
    """单个政策因子"""
    name: str
    category: str
    impact: str  # positive / negative / neutral
    impact_score: float  # -10 to +10
    confidence: str  # high / medium / low
    description: str
    key_events: List[str]
    affected_sectors: List[str]


@dataclass
class PolicyAnalysis:
    """完整政策分析结果"""
    overall_policy_score: float  # -100 to +100
    overall_trend: str  # favorable / neutral / unfavorable
    domestic_policy_score: float
    international_env_score: float
    monetary_policy_score: float
    commodity_score: float
    factors: List[PolicyFactor]
    sector_recommendations: Dict[str, Dict]
    commodity_recommendations: Dict[str, Dict]
    risk_warnings: List[str]
    opportunities: List[str]
    next_review_date: str


# ---------------------------------------------------------------------------
# 政策数据库（基于2026年5月最新研究）
# ---------------------------------------------------------------------------

# 十五五规划六大产业
FIFTEENTH_FYP_INDUSTRIES = {
    "未来产业": {
        "quantum": {"name": "量子科技", "priority": "前瞻布局", "maturity": "早期", "investment_horizon": "5-10年"},
        "biomanufacturing": {"name": "生物制造", "priority": "前瞻布局", "maturity": "早期", "investment_horizon": "3-7年"},
        "hydrogen": {"name": "氢能与核聚变", "priority": "前瞻布局", "maturity": "早期", "investment_horizon": "5-15年"},
        "bci": {"name": "脑机接口", "priority": "前瞻布局", "maturity": "极早期", "investment_horizon": "10年+"},
        "embodied_ai": {"name": "具身智能", "priority": "前瞻布局", "maturity": "早期", "investment_horizon": "3-5年"},
        "6g": {"name": "6G通信", "priority": "前瞻布局", "maturity": "研发中", "investment_horizon": "5-10年"},
    },
    "新兴支柱产业": {
        "ic": {"name": "集成电路", "priority": "重点打造", "maturity": "成长期", "investment_horizon": "2-5年"},
        "aerospace": {"name": "航空航天", "priority": "重点打造", "maturity": "成长期", "investment_horizon": "3-5年"},
        "biomedicine": {"name": "生物医药", "priority": "重点打造", "maturity": "成长期", "investment_horizon": "2-5年"},
        "energy_storage": {"name": "新型储能", "priority": "重点打造", "maturity": "快速成长期", "investment_horizon": "2-4年"},
        "low_altitude": {"name": "低空经济", "priority": "重点打造", "maturity": "导入期", "investment_horizon": "3-5年"},
        "robot": {"name": "智能机器人", "priority": "重点打造", "maturity": "成长期", "investment_horizon": "2-4年"},
    }
}

# 大宗商品数据（2026年5月）
COMMODITY_DATA = {
    "copper": {
        "name": "铜",
        "current_price": 11700,  # USD/ton, LME
        "price_unit": "美元/吨",
        "trend": "up",
        "year_target": 11400,
        "long_term_target": 15000,
        "drivers": [
            "铜矿/硫酸供应紧缺",
            "冶炼厂4-5月集中检修",
            "新能源用铜需求爆发（电动车/电网）",
            "美国潜在铜关税（2027年）",
        ],
        "risks": [
            "中东局势恶化冲击供应链",
            "美联储高利率压制金融属性",
            "关税政策不确定性",
        ],
        "policy_score": 7,
    },
    "gold": {
        "name": "黄金",
        "current_price": 4328,  # USD/oz
        "price_unit": "美元/盎司",
        "trend": "up",
        "year_target": 4900,
        "long_term_target": 5000,
        "drivers": [
            "央行持续购金",
            "地缘政治避险需求",
            "中东战争不确定性",
            "通胀压力支撑",
        ],
        "risks": [
            "美联储维持高利率",
            "美元走强",
            "地缘风险消退",
        ],
        "policy_score": 8,
    },
    "crude_oil": {
        "name": "原油",
        "current_price": 86,  # USD/barrel, Brent
        "price_unit": "美元/桶",
        "trend": "volatile",
        "year_target": 86,
        "long_term_target": 75,
        "drivers": [
            "中东霍尔木兹海峡封锁",
            "OPEC+减产支撑",
            "全球能源需求回暖",
        ],
        "risks": [
            "5月后霍尔木兹封锁解除（基准假设）",
            "供应过剩担忧",
            "新能源替代加速",
        ],
        "policy_score": 3,
    },
    "lithium": {
        "name": "锂",
        "current_price": None,
        "price_unit": "元/吨",
        "trend": "bottoming",
        "year_target": None,
        "long_term_target": None,
        "drivers": [
            "储能需求爆发",
            "固态电池技术突破",
            "新能源车渗透率提升",
        ],
        "risks": [
            "产能过剩",
            "价格低迷",
            "技术路线变化",
        ],
        "policy_score": 5,
    },
    "aluminum": {
        "name": "铝",
        "current_price": None,
        "price_unit": "美元/吨",
        "trend": "up",
        "year_target": None,
        "long_term_target": None,
        "drivers": [
            "轻量化需求（新能源车）",
            "光伏支架用铝",
            "电力成本支撑",
        ],
        "risks": [
            "产能释放",
            "电力成本波动",
        ],
        "policy_score": 6,
    },
}

# 美联储政策数据（2026年5月，基于4月29日FOMC会议）
FED_POLICY = {
    "current_rate": "3.50%-3.75%",
    "rate_status": "维持不变（连续第三次）",
    "last_change": "2025年12月",
    "next_meeting": "2026年6月16-17日（沃什首次主席会议）",
    "2026_cuts_expected": 0,  # 市场大幅下调预期，全年可能不降息
    "market_pricing_cuts": 0,  # 市场定价仅剩约3%概率
    "qt_status": "已暂停",
    "qt_policy": "维持充足准备金",
    "balance_sheet": "平稳运行阶段",
    "inflation_target": "2%",
    "current_inflation": "3.3%（CPI），核心PCE 2.7%",
    "oil_impact": "中东局势导致能源价格飙升，PCE或升至3.5-3.8%",
    "chairman_change": "2026年4月29日鲍威尔卸任，Kevin Warsh（沃什）接任",
    "chairman_stance": "沃什更重视价格稳定，偏鹰派",
    "dissent": "1992年以来 dissent 最多的一次会议（4位票委分歧）",
}

# 国内货币政策（2026年4月）
PBOC_POLICY = {
    "lpr_1y": "3.0%",
    "lpr_5y": "3.5%",
    "rrr": "约7.0%",
    "policy_stance": "适度宽松",
    "last_change": "2025年5月（下调10bp），连续11个月不变",
    "rate_outlook": "2026年预计1-2次降息（10-20bp），1-2次降准（约50bp），节奏小步慢跑",
    "structural_tools": [
        "科技创新再贷款额度提升至1.2万亿",
        "结构性工具利率下调25bp至1.25%",
        "支持服务消费、养老、科技创新、小微",
    ],
    "key_measures": [
        "择机降准降息（一季度为观察窗口）",
        "结构性货币政策工具精准发力",
        "强化政策利率引导，完善市场化利率传导",
    ],
    "constraints": [
        "银行净息差1.42%历史低位",
        "实体融资成本已降至3.55%历史低位",
        "汇率稳定考量",
        "信贷需求偏弱",
    ],
}


# ---------------------------------------------------------------------------
# 核心分析类
# ---------------------------------------------------------------------------

class PolicyAnalyzer:
    """政策与宏观环境分析器"""

    def __init__(self):
        self.fyp_industries = FIFTEENTH_FYP_INDUSTRIES
        self.commodities = COMMODITY_DATA
        self.fed = FED_POLICY
        self.pbc = PBOC_POLICY

    def analyze_fifteenth_fyp(self) -> PolicyFactor:
        """分析十五五规划政策影响"""
        return PolicyFactor(
            name="十五五规划产业导向",
            category="国内政策",
            impact="positive",
            impact_score=8,
            confidence="high",
            description="十五五规划（2026-2030）明确六大未来产业+六大新兴支柱产业，总投资超10万亿",
            key_events=[
                "2026年3月两会通过十五五规划纲要",
                "28项引领新质生产力发展重大工程",
                "集成电路、生物医药、航空航天定位新兴支柱产业",
                "量子科技、具身智能、脑机接口定位未来产业",
            ],
            affected_sectors=[
                "芯片ETF(159995)", "创新药ETF(159992)", "医疗器械ETF(159898)",
                "机器人ETF(562500)", "光伏ETF(159857)", "电池ETF(159755)",
            ],
        )

    def analyze_monetary_policy(self) -> PolicyFactor:
        """分析中美货币政策差异"""
        # 中国宽松 vs 美国紧缩 = 利差压力，但美联储2026年降息预期大幅降温
        impact = "neutral"
        score = 1  # 略偏正面：美联储按兵不动减少外部波动，中国仍有宽松空间
        return PolicyFactor(
            name="中美货币政策分化",
            category="货币政策",
            impact=impact,
            impact_score=score,
            confidence="medium",
            description="中国适度宽松（全年1-2次降准降息）vs 美联储维持高利率（全年可能不降息）。利差压力仍在但外部约束减轻，结构性工具（科技创新再贷款1.2万亿）精准发力",
            key_events=[
                f"美联储维持利率{self.fed['current_rate']}不变（连续第三次）",
                f"鲍威尔卸任，沃什接任（偏鹰，重视价格稳定）",
                f"2026年降息预期大幅降温，市场定价仅剩3%概率",
                f"中国1年期LPR {self.pbc['lpr_1y']}，5年期{self.pbc['lpr_5y']}，连续11个月不变",
                f"科技创新再贷款额度提升至1.2万亿，利率下调25bp",
            ],
            affected_sectors=[
                "港股（流动性敏感）", "黄金", "高股息资产", "创新药（融资环境）",
            ],
        )

    def analyze_commodities(self) -> PolicyFactor:
        """分析大宗商品政策环境"""
        return PolicyFactor(
            name="大宗商品供需格局",
            category="商品市场",
            impact="positive",
            impact_score=6,
            confidence="medium",
            description="铜矿紧缺+黄金避险+原油地缘风险，大宗商品处于政策与供需共振期",
            key_events=[
                "铜：全球铜矿/硫酸紧缺，冶炼厂检修",
                "黄金：央行购金+地缘避险，目标4900-5000美元",
                "原油：霍尔木兹海峡封锁，基准86美元/桶",
                "美国潜在铜关税（2027年）",
            ],
            affected_sectors=[
                "工业金属", "黄金ETF(518880)", "能源",
            ],
        )

    def analyze_geopolitics(self) -> PolicyFactor:
        """分析地缘政治影响（2026年5月更新）"""
        return PolicyFactor(
            name="地缘政治与中美博弈",
            category="国际环境",
            impact="negative",
            impact_score=-6,  # 风险上升：关税升级+台海紧张
            confidence="high",
            description="中美贸易战高压持续，2026年4月钢铝铜关税升级；台海局势2026年被视为高风险窗口；日本加速军事化部署导弹覆盖台海。短期避险情绪压制风险偏好，但国产替代逻辑强化",
            key_events=[
                "2026年4月6日美国钢铝铜关税升级生效，按全部海关价值加征",
                "IEEPA被最高法院推翻（6:3），改用第122/301条继续征税",
                "美国取消中国商品小额免税（De Minimis，800美元以下）",
                "封堵墨西哥转口通道，启动原产地规则审计",
                "日本加速部署12式反舰导弹增程型（射程1000km+），覆盖台海",
                "2026年被多方视为台海高风险窗口期",
                "中东霍尔木兹海峡封锁风险，原油波动加剧",
            ],
            affected_sectors=[
                "芯片ETF(159995)（国产替代）", "军工", "黄金(518880)", "恒生科技(513130)",
            ],
        )

    def analyze_domestic_economy(self) -> PolicyFactor:
        """分析国内经济基本面（2026年Q1数据更新）"""
        return PolicyFactor(
            name="国内经济复苏与改革",
            category="国内经济",
            impact="positive",
            impact_score=6,  # 上调：Q1 GDP 5.0%，制造业强劲
            confidence="high",
            description="2026年Q1 GDP同比5.0%，环比1.3%；制造业+6.3%，信息传输软件业+10.6%；房地产降幅收窄至-0.1%；进出口+15.0%。财政政策积极（赤字率4%，支出首超30万亿）",
            key_events=[
                "Q1 GDP 334,193亿元，同比+5.0%，环比+1.3%",
                "制造业+6.3%，信息传输软件业+10.6%，金融业+6.5%",
                "房地产-0.1%（降幅大幅收窄），建筑业-3.8%",
                "进出口+15.0%（出口+11.9%，进口+19.6%）",
                "CPI+0.9%，核心CPI+1.2%（通胀温和回升）",
                "财政政策：赤字率4%，一般公共预算支出首超30万亿",
                "超长期特别国债1.3万亿+地方专项债4.4万亿",
                "增值税法2026年1月1日正式实施",
                "土地改革：第二轮土地承包到期后再延长30年整省试点",
                "科技体制改革：职务科技成果赋权、技术经理人职业资格制度",
            ],
            affected_sectors=[
                "沪深300ETF(510300)", "中证A500ETF(560610)", "银行ETF(512800)", "证券ETF(512880)",
            ],
        )

    def calculate_overall_score(self, factors: List[PolicyFactor]) -> Tuple[float, str]:
        """计算综合政策评分"""
        scores = [f.impact_score for f in factors]
        avg = sum(scores) / len(scores) if scores else 0

        # 加权：国内政策权重更高
        weights = {
            "国内政策": 1.2,
            "国内经济": 1.1,
            "货币政策": 1.0,
            "商品市场": 0.9,
            "国际环境": 0.8,
        }
        weighted = sum(f.impact_score * weights.get(f.category, 1.0) for f in factors)
        weighted_avg = weighted / sum(weights.get(f.category, 1.0) for f in factors)

        # 映射到 -100~100
        overall = weighted_avg * 10

        if overall >= 30:
            trend = "favorable"
        elif overall <= -30:
            trend = "unfavorable"
        else:
            trend = "neutral"

        return overall, trend

    def get_sector_recommendations(self) -> Dict[str, Dict]:
        """获取行业推荐"""
        return {
            "核心推荐": {
                "芯片/半导体": {
                    "etfs": ["159995"],
                    "reason": "十五五规划集成电路列为新兴支柱产业，国产替代加速",
                    "policy_score": 9,
                    "risk": "美国出口管制",
                },
                "AI/机器人": {
                    "etfs": ["562500"],
                    "reason": "具身智能列为未来产业，AI算力需求爆发",
                    "policy_score": 9,
                    "risk": "估值偏高",
                },
                "创新药/医疗器械": {
                    "etfs": ["159992", "159898"],
                    "reason": "生物医药列为新兴支柱产业，创新药支持政策",
                    "policy_score": 8,
                    "risk": "研发周期长",
                },
                "新能源": {
                    "etfs": ["159857", "159755"],
                    "reason": "新型储能列为支柱，光伏度电成本下降82%",
                    "policy_score": 7,
                    "risk": "产能过剩",
                },
            },
            "防御配置": {
                "红利低波": {
                    "etfs": ["512890"],
                    "reason": "高利率环境下股息吸引力，政策鼓励分红",
                    "policy_score": 6,
                    "risk": "利率下行时表现落后",
                },
                "银行": {
                    "etfs": ["512800"],
                    "reason": "经济复苏+净息差企稳+政策支持",
                    "policy_score": 5,
                    "risk": "房地产不良率",
                },
                "黄金": {
                    "etfs": ["518880"],
                    "reason": "地缘避险+央行购金+去美元化",
                    "policy_score": 8,
                    "risk": "美元走强",
                },
            },
            "机会关注": {
                "恒生科技": {
                    "etfs": ["513130"],
                    "reason": "港股估值洼地，美联储降息预期利好流动性",
                    "policy_score": 6,
                    "risk": "中美关系、港股流动性",
                },
                "证券": {
                    "etfs": ["512880"],
                    "reason": "牛市预期+成交量回升+政策利好",
                    "policy_score": 5,
                    "risk": "市场波动",
                },
            },
        }

    def get_commodity_recommendations(self) -> Dict[str, Dict]:
        """获取商品推荐"""
        return {
            "铜": {
                "trend": "看涨",
                "policy_score": 7,
                "action": "高配",
                "reason": "铜矿紧缺+新能源需求+关税预期",
                "price_target": "11,400美元/吨（年内）",
            },
            "黄金": {
                "trend": "看涨",
                "policy_score": 8,
                "action": "超配",
                "reason": "央行购金+地缘避险+通胀支撑",
                "price_target": "4,900-5,000美元/盎司",
            },
            "原油": {
                "trend": "高位震荡",
                "policy_score": 3,
                "action": "低配",
                "reason": "地缘风险溢价，但长期供应过剩",
                "price_target": "基准86美元/桶",
            },
            "锂": {
                "trend": "筑底",
                "policy_score": 5,
                "action": "观望",
                "reason": "储能需求爆发，但产能过剩",
                "price_target": "等待拐点信号",
            },
        }

    def run_full_analysis(self) -> PolicyAnalysis:
        """执行完整分析"""
        factors = [
            self.analyze_fifteenth_fyp(),
            self.analyze_monetary_policy(),
            self.analyze_commodities(),
            self.analyze_geopolitics(),
            self.analyze_domestic_economy(),
        ]

        overall_score, trend = self.calculate_overall_score(factors)

        # 分项评分
        domestic = sum(f.impact_score for f in factors if f.category in ("国内政策", "国内经济")) / 2
        international = sum(f.impact_score for f in factors if f.category in ("国际环境", "商品市场")) / 2
        monetary = next((f.impact_score for f in factors if f.category == "货币政策"), 0)
        commodity = next((f.impact_score for f in factors if f.category == "商品市场"), 0)

        sectors = self.get_sector_recommendations()
        commodities = self.get_commodity_recommendations()

        risks = [
            "中美贸易战高压持续，钢铝铜关税升级+小额免税取消+转口封堵",
            "台海地缘政治风险上升，2026年被视为高风险窗口",
            "美联储维持高利率，全年可能不降息，压制新兴市场流动性",
            "中东霍尔木兹海峡封锁风险，能源价格飙升推升通胀",
            "房地产仍在负增长（-0.1%），底部确认时间不确定",
            "部分新兴产业产能过剩（光伏/锂）",
            "CPI仅0.9%，通缩阴影未完全消除",
        ]

        opportunities = [
            "十五五规划六张网投资超7万亿+创投引导基金撬动万亿",
            "国产替代加速（半导体/工业软件/高端装备）",
            "AI应用进入盈利兑现期，具身智能列为未来产业",
            "科技体制改革：职务科技成果赋权+首台套补贴30-50%",
            "储能突破临界点，新型储能列为新兴支柱产业",
            "黄金避险+央行购金+去美元化长期趋势",
            "房地产降幅大幅收窄，底部或已临近",
            "财政政策积极（赤字率4%+特别国债1.3万亿），基建托底",
        ]

        # 下次评估日期：每月1日
        next_month = datetime.now().month + 1
        next_year = datetime.now().year
        if next_month > 12:
            next_month = 1
            next_year += 1
        next_review = f"{next_year}-{next_month:02d}-01"

        return PolicyAnalysis(
            overall_policy_score=overall_score,
            overall_trend=trend,
            domestic_policy_score=domestic,
            international_env_score=international,
            monetary_policy_score=monetary,
            commodity_score=commodity,
            factors=factors,
            sector_recommendations=sectors,
            commodity_recommendations=commodities,
            risk_warnings=risks,
            opportunities=opportunities,
            next_review_date=next_review,
        )


# ---------------------------------------------------------------------------
# 报告生成
# ---------------------------------------------------------------------------

def generate_policy_report(analysis: PolicyAnalysis) -> str:
    """生成政策分析报告"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    def impact_icon(score: float) -> str:
        if score >= 5:
            return "🟢"
        elif score >= 0:
            return "🟡"
        elif score >= -5:
            return "🟠"
        else:
            return "🔴"

    def trend_cn(trend: str) -> str:
        return {"favorable": "有利", "neutral": "中性", "unfavorable": "不利"}.get(trend, trend)

    lines = [
        f"# 政策与宏观环境分析报告",
        f"",
        f"**生成时间**: {now}",
        f"**评估周期**: 月度",
        f"**下次更新**: {analysis.next_review_date}",
        f"",
        "---",
        "",
        "## 一、综合评分",
        "",
        "| 维度 | 评分 | 判断 |",
        "|------|------|------|",
        f"| **综合政策评分** | **{analysis.overall_policy_score:+.1f}/100** | **{trend_cn(analysis.overall_trend)}** |",
        f"| 国内政策 | {impact_icon(analysis.domestic_policy_score)} {analysis.domestic_policy_score:+.1f} | {'利好' if analysis.domestic_policy_score > 0 else '利空'} |",
        f"| 国际环境 | {impact_icon(analysis.international_env_score)} {analysis.international_env_score:+.1f} | {'利好' if analysis.international_env_score > 0 else '利空'} |",
        f"| 货币政策 | {impact_icon(analysis.monetary_policy_score)} {analysis.monetary_policy_score:+.1f} | {'利好' if analysis.monetary_policy_score > 0 else '利空'} |",
        f"| 商品市场 | {impact_icon(analysis.commodity_score)} {analysis.commodity_score:+.1f} | {'利好' if analysis.commodity_score > 0 else '利空'} |",
        f"",
        "---",
        "",
        "## 二、政策因子详解",
        "",
    ]

    for factor in analysis.factors:
        lines.extend([
            f"### {impact_icon(factor.impact_score)} {factor.name}",
            f"",
            f"| 维度 | 内容 |",
            f"|------|------|",
            f"| 类别 | {factor.category} |",
            f"| 影响 | {'正面' if factor.impact == 'positive' else ('负面' if factor.impact == 'negative' else '中性')} ({factor.impact_score:+.0f}) |",
            f"| 置信度 | {factor.confidence} |",
            f"| 描述 | {factor.description} |",
            f"| 受影响标的 | {', '.join(factor.affected_sectors)} |",
            f"",
            "**关键事件**：",
            "",
        ])
        for event in factor.key_events:
            lines.append(f"- {event}")
        lines.append("")

    lines.extend([
        "---",
        "",
        "## 三、十五五规划产业投资映射",
        "",
        "### 3.1 六大未来产业（前瞻布局）",
        "",
        "| 产业 | 成熟度 | 投资周期 | 相关标的 |",
        "|------|--------|----------|----------|",
    ])
    for key, info in FIFTEENTH_FYP_INDUSTRIES["未来产业"].items():
        etf_map = {
            "quantum": "量子计算ETF（待上市）",
            "biomanufacturing": "创新药ETF(159992)",
            "hydrogen": "氢能/新能源",
            "bci": "脑机接口（一级市场）",
            "embodied_ai": "机器人ETF(562500)",
            "6g": "通信ETF",
        }
        lines.append(f"| {info['name']} | {info['maturity']} | {info['investment_horizon']} | {etf_map.get(key, '-')} |")

    lines.extend([
        "",
        "### 3.2 六大新兴支柱产业（重点打造）",
        "",
        "| 产业 | 成熟度 | 投资周期 | 相关标的 | 配置建议 |",
        "|------|--------|----------|----------|----------|",
    ])
    for key, info in FIFTEENTH_FYP_INDUSTRIES["新兴支柱产业"].items():
        etf_map = {
            "ic": "芯片ETF(159995)",
            "aerospace": "军工ETF",
            "biomedicine": "创新药ETF(159992) + 医疗器械ETF(159898)",
            "energy_storage": "电池ETF(159755)",
            "low_altitude": "低空经济ETF（待上市）",
            "robot": "机器人ETF(562500)",
        }
        cfg = {"ic": "核心仓位", "biomedicine": "重点配置", "energy_storage": "重点配置",
               "robot": "精选配置", "aerospace": "观察", "low_altitude": "观察"}
        lines.append(f"| {info['name']} | {info['maturity']} | {info['investment_horizon']} | {etf_map.get(key, '-')} | {cfg.get(key, '关注')} |")

    lines.extend([
        "",
        "---",
        "",
        "## 四、大宗商品分析",
        "",
        "### 4.1 美联储货币政策",
        "",
        "| 指标 | 当前值 | 说明 |",
        "|------|--------|------|",
        f"| 联邦基金利率 | {FED_POLICY['current_rate']} | 维持不变 |",
        f"| 缩表状态 | {FED_POLICY['qt_status']} | {FED_POLICY['qt_policy']} |",
        f"| 2026年预期降息 | {FED_POLICY['2026_cuts_expected']}次 | 官方预测 |",
        f"| 下次会议 | {FED_POLICY['next_meeting']} | 更新点阵图 |",
        f"| 美联储主席 | 5月换届 | 候选人偏鸽 |",
        f"| 当前通胀 | {FED_POLICY['current_inflation']} | 高于2%目标 |",
        "",
        "### 4.2 中国货币政策",
        "",
        "| 指标 | 当前值 | 说明 |",
        "|------|--------|------|",
        f"| 1年期LPR | {PBOC_POLICY['lpr_1y']} | 政策利率锚 |",
        f"| 5年期LPR | {PBOC_POLICY['lpr_5y']} | 房贷利率基准 |",
        f"| 存款准备金率 | {PBOC_POLICY['rrr']} | 仍有下调空间 |",
        f"| 政策立场 | {PBOC_POLICY['policy_stance']} | 支持实体经济 |",
        "",
        "### 4.3 商品配置建议",
        "",
        "| 商品 | 趋势 | 政策评分 | 建议 | 目标价 | 核心逻辑 |",
        "|------|------|----------|------|--------|----------|",
    ])

    for name, data in analysis.commodity_recommendations.items():
        lines.append(
            f"| {name} | {data['trend']} | {data['policy_score']} | {data['action']} | "
            f"{data['price_target']} | {data['reason']} |"
        )

    lines.extend([
        "",
        "---",
        "",
        "## 五、行业配置建议（结合政策面）",
        "",
    ])

    for category, sectors in analysis.sector_recommendations.items():
        lines.extend([
            f"### 5.{list(analysis.sector_recommendations.keys()).index(category) + 1} {category}",
            "",
            "| 行业 | ETF | 政策评分 | 核心逻辑 | 风险 |",
            "|------|-----|----------|----------|------|",
        ])
        for name, info in sectors.items():
            etfs = ", ".join(info['etfs'])
            lines.append(
                f"| {name} | {etfs} | {info['policy_score']} | {info['reason']} | {info['risk']} |"
            )
        lines.append("")

    lines.extend([
        "---",
        "",
        "## 六、风险与机会",
        "",
        "### 6.1 主要风险 ⚠️",
        "",
    ])
    for risk in analysis.risk_warnings:
        lines.append(f"- {risk}")

    lines.extend([
        "",
        "### 6.2 主要机会 ✅",
        "",
    ])
    for opp in analysis.opportunities:
        lines.append(f"- {opp}")

    lines.extend([
        "",
        "---",
        "",
        "## 七、策略引擎整合建议",
        "",
        "基于政策分析，对策略引擎的输出修正：",
        "",
        "| 维度 | 基准判断 | 政策修正 | 最终建议 |",
        "|------|----------|----------|----------|",
        "| 周期阶段 | 复苏期 | 政策强力支撑 | **复苏期（加速）** |",
        "| 仓位建议 | 50-70% | 国内政策利好+1 | **60-75%** |",
        "| 核心赛道 | AI+新能源 | 增加半导体/医药 | **AI+半导体+创新药+新能源** |",
        "| 黄金配置 | 10-15% | 地缘风险+1 | **15-20%** |",
        "| 港股配置 | 中性 | 流动性预期改善 | **适度增配** |",
        "| 4%定投法 | 启用 | 震荡市特征明显 | **启用（宽基为主）** |",
        "",
        "---",
        "",
        f"*本报告基于公开政策信息与市场研究生成，评估时间：{now}，下次更新：{analysis.next_review_date}*",
        "*本报告仅供研究参考，不构成投资建议。*",
        "",
    ])

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="政策与宏观环境分析")
    parser.add_argument("--report", action="store_true", help="生成完整报告")
    parser.add_argument("--summary", action="store_true", help="显示分析摘要")
    args = parser.parse_args()

    analyzer = PolicyAnalyzer()
    analysis = analyzer.run_full_analysis()

    if args.report:
        report = generate_policy_report(analysis)
        report_path = REPORTS_DIR / f"policy_analysis_{datetime.now().strftime('%Y%m%d')}.md"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"报告已保存: {report_path}")
        print(f"\n报告预览（前2000字符）：")
        # Windows控制台编码兼容处理
        preview = report[:2000]
        for ch in ['🟢', '🟡', '🟠', '🔴', '📈', '📉', '➖', '⚠️', '✅', '↗', '↘', '➡️']:
            preview = preview.replace(ch, '')
        print(preview)
    elif args.summary:
        print("政策与宏观环境分析摘要")
        print("=" * 60)
        print(f"综合评分: {analysis.overall_policy_score:+.1f}/100 ({analysis.overall_trend})")
        print(f"国内政策: {analysis.domestic_policy_score:+.1f} | 国际环境: {analysis.international_env_score:+.1f}")
        print(f"货币政策: {analysis.monetary_policy_score:+.1f} | 商品市场: {analysis.commodity_score:+.1f}")
        print(f"\n核心推荐行业:")
        for name, info in analysis.sector_recommendations.get("核心推荐", {}).items():
            print(f"  - {name}: {info['reason'][:40]}...")
        print(f"\n商品建议:")
        for name, info in analysis.commodity_recommendations.items():
            print(f"  - {name}: {info['action']} ({info['trend']})")
        print(f"\n下次更新: {analysis.next_review_date}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
