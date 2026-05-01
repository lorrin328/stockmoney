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
        "current_price": 4630,  # USD/oz, 2026年5月1日
        "price_unit": "美元/盎司",
        "trend": "up",
        "year_target": 5000,
        "long_term_target": 6300,  # 摩根大通2026年底目标
        "drivers": [
            "央行持续购金（去美元化主线）",
            "地缘政治避险需求（5月美伊海上封锁升级）",
            "美元体系松动+鲍威尔5/15卸任的政策真空",
            "通胀压力支撑（油价飙升）",
        ],
        "risks": [
            "美联储维持高利率（4/29 FOMC 8:4分歧维持3.5%-3.75%）",
            "美元走强（沃什偏鹰）",
            "地缘风险阶段性消退（停火协议）",
        ],
        "policy_score": 8,
    },
    "crude_oil": {
        "name": "原油",
        "current_price": 113,  # USD/barrel, Brent，2026年5月1日
        "price_unit": "美元/桶",
        "trend": "up",
        "year_target": 100,  # 标普上调至100美元
        "long_term_target": 75,
        "drivers": [
            "美伊海上封锁（4/29特朗普表态）",
            "霍尔木兹海峡持续封锁（2/28起）",
            "阿联酋5/1退出OPEC+，产油国阵营分化",
            "OPEC+实际增产能力受限",
        ],
        "risks": [
            "美伊达成协议→油价回落",
            "全球需求衰退",
            "新能源替代加速",
            "5月后封锁缓解可能",
        ],
        "policy_score": 4,  # 上调：地缘溢价持续，对油气板块构成支撑
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

# 美联储政策数据（2026年5月1日，基于4月29日FOMC会议结果）
FED_POLICY = {
    "current_rate": "3.50%-3.75%",
    "rate_status": "维持不变（连续第三次，4/29 FOMC 8:4分歧维持）",
    "last_change": "2025年12月",
    "next_meeting": "2026年6月16-17日（沃什首次主席会议）",
    "2026_cuts_expected": 0,  # 市场已逆转预期，开始消化2027年加息可能
    "market_pricing_cuts": 0,  # 货币市场几乎放弃今年降息押注
    "qt_status": "已暂停",
    "qt_policy": "维持充足准备金",
    "balance_sheet": "平稳运行阶段",
    "inflation_target": "2%",
    "current_inflation": "3.3%（CPI），核心PCE 2.7%，油价飙升后预计上行",
    "oil_impact": "中东海上封锁推升油价至Brent 113美元，PCE或升至3.5-3.8%",
    "chairman_change": "鲍威尔5月15日卸任，Kevin Warsh（沃什）已获参议院银行委员会通过提名",
    "chairman_stance": "沃什倾向'缩表+降息'双线并行，但通胀压力下空间有限",
    "dissent": "1992年以来分歧最高（4位委员投反对票，含Miran支持降息）",
    "may_2026_signal": "若沃什释放鸽派信号，可改善流动性预期；若维持鹰派，外围压力延续",
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
        """分析大宗商品政策环境（2026年5月1日更新）"""
        return PolicyFactor(
            name="大宗商品供需格局",
            category="商品市场",
            impact="positive",
            impact_score=7,  # 上调：油价飙升+黄金创新高+实物资产主线明确
            confidence="high",
            description="资源股内部呈递进节奏：贵金属→铜铝→化工/能源接力。5/1黄金4630美元创新高，Brent油价113美元/桶。投资风格从'虚拟经济'切换至'实物资产'主导的涨价逻辑",
            key_events=[
                "黄金5/1突破4630美元/盎司，白银破75美元/盎司",
                "Brent原油5/1破113美元/桶（特朗普海上封锁言论）",
                "WTI原油破109美元/桶",
                "铜：全球铜矿/硫酸紧缺，冶炼厂检修",
                "化工链景气：磷化工/染料/农药/聚氨酯/合成橡胶",
                "美国潜在铜关税（2027年）",
                "2025年12月以来化工/石油板块累计涨约30%",
                "有色龙头（紫金/洛阳钼业/中铝）估值已较高",
            ],
            affected_sectors=[
                "黄金ETF(518880)（超配）", "有色金属ETF(512400)（油气煤化工接力）",
                "能源", "化工链",
            ],
        )

    def analyze_geopolitics(self) -> PolicyFactor:
        """分析地缘政治影响（2026年5月1日更新）"""
        return PolicyFactor(
            name="地缘政治与中美博弈",
            category="国际环境",
            impact="negative",
            impact_score=-7,  # 风险升级：5月美伊海上封锁+OPEC分裂+台海窗口
            confidence="high",
            description="美伊冲突升级至海上封锁阶段，霍尔木兹海峡持续封闭推升油价至Brent 113美元/桶；阿联酋5/1退出OPEC+加剧产油国阵营分化；中美关税整体休战但半导体232关税延续；台海仍是2026年高风险窗口。地缘溢价持续支撑黄金/油气，但压制成本敏感板块",
            key_events=[
                "2026/2/28 美以联合空袭伊朗，伊朗封锁霍尔木兹海峡",
                "2026/4/29 特朗普表态对伊朗实施海上封锁，油价跳涨6%+",
                "2026/5/1 阿联酋宣布退出OPEC和OPEC+，产油国阵营分化",
                "2026/5/1 中国对所有非洲建交国实施零关税（多元化战略）",
                "2026/2/20 美最高法院裁定IEEPA关税无授权（6:3）",
                "2026/2/24 白宫改用第122条对全球加征10%关税",
                "2026/1/15 半导体232关税生效（高性能AI芯片+25%）",
                "2025年中美吉隆坡共识：91%关税取消、24%关税停一年",
                "2026年1月美国对委内瑞拉发起军事行动控制马杜罗",
                "2026年被多方视为台海高风险窗口期",
                "日本部署12式反舰导弹增程型（射程1000km+），覆盖台海",
            ],
            affected_sectors=[
                "黄金ETF(518880)（避险）", "有色金属ETF(512400)（油气煤化工接力）",
                "芯片ETF(159995)（国产替代）", "军工", "恒生科技(513130)（地缘承压）",
            ],
        )

    def analyze_domestic_economy(self) -> PolicyFactor:
        """分析国内经济基本面（2026年5月1日更新，含4/28政治局会议）"""
        return PolicyFactor(
            name="国内经济复苏与改革",
            category="国内经济",
            impact="positive",
            impact_score=7,  # 上调：Q1超预期+政治局"信心建设战"+业绩压制消退
            confidence="high",
            description="2026年Q1 GDP同比5.0%超预期，环比+1.3%；4/28政治局会议首次将'稳定+增强资本市场信心'置于战略高度，定性为'信心建设战'；'十五五'开局之年六张网投资超7万亿；货币政策延续'适度宽松'，财政赤字率4%",
            key_events=[
                "2026/4/28 中央政治局会议：'稳定和增强资本市场信心'(首次升级提法)",
                "政治局会议新增'保持人民币汇率基本稳定'，删去'加大逆周期跨周期调节'",
                "Q1 GDP 334,193亿元，同比+5.0%，环比+1.3%（超预期）",
                "Q1内需贡献率84.7%，同比提高近30个百分点",
                "高技术制造业Q1+12.5%，3D打印+54%、锂电+40.8%、机器人+33.2%",
                "新三样出口高速增长，电动汽车出口+77.5%",
                "房地产-0.1%（降幅大幅收窄），建筑业-3.8%",
                "CPI+0.9%，核心CPI+1.2%（通胀温和回升）",
                "财政政策：赤字率4%，一般公共预算支出首超30万亿",
                "超长期特别国债1.3万亿+地方专项债4.4万亿",
                "六张网投资超7万亿（水网/电网/算力网/通信网/管网/物流网）",
                "全面实施'人工智能+'行动，发展智能经济新形态",
                "4/24 A股交易规则系统性优化",
                "4/10 创业板改革落地，下一步落实落细",
                "中央财政1000亿支持财政金融协同促内需",
                "'两重'建设+'两新'政策接续实施",
            ],
            affected_sectors=[
                "沪深300ETF(510300)", "中证A500ETF(560610)", "证券ETF(512880)（资本市场改革）",
                "芯片/AI/创新药/机器人（AI+行动+新质生产力）",
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
        """获取行业推荐（5月1日更新：业绩真空+信心建设战+实物资产主线）"""
        return {
            "核心推荐": {
                "芯片/半导体": {
                    "etfs": ["159995"],
                    "reason": "十五五集成电路新兴支柱+国产替代加速；一季报预增（强一+650%）",
                    "policy_score": 9,
                    "risk": "美国出口管制+高景气高估值高拥挤",
                },
                "AI/机器人": {
                    "etfs": ["562500", "159819"],
                    "reason": "具身智能列为未来产业+'人工智能+'行动+AI算力需求爆发",
                    "policy_score": 9,
                    "risk": "估值偏高+一季报短期承压",
                },
                "创新药/医疗器械": {
                    "etfs": ["159992", "159898"],
                    "reason": "生物医药新兴支柱+一季报亮眼（海思科+1000%）+出海兑现",
                    "policy_score": 8,
                    "risk": "研发周期长",
                },
                "黄金/避险资产": {
                    "etfs": ["518880"],
                    "reason": "5/1黄金破4630美元创新高+地缘升级（美伊海上封锁）+鲍威尔卸任真空",
                    "policy_score": 9,
                    "risk": "停火协议→风险阶段性消退",
                },
                "有色/资源股": {
                    "etfs": ["512400"],
                    "reason": "实物资产主线接力（贵金属→铜铝→化工/能源）+油价飙升推升涨价逻辑",
                    "policy_score": 8,
                    "risk": "美元走强+需求放缓",
                },
                "新能源": {
                    "etfs": ["159857", "159755"],
                    "reason": "新型储能列为支柱+新型电力系统+光伏度电成本下降82%",
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
            },
            "机会关注": {
                "证券": {
                    "etfs": ["512880"],
                    "reason": "政治局'信心建设战'+创业板改革+A股交易规则优化",
                    "policy_score": 7,
                    "risk": "市场波动",
                },
                "硬科技/科创": {
                    "etfs": ["588000", "515880"],
                    "reason": "硬科技+国产替代+'人工智能+'行动",
                    "policy_score": 8,
                    "risk": "估值高+中美科技博弈",
                },
                "恒生科技": {
                    "etfs": ["513130"],
                    "reason": "港股估值洼地，沃什上任若鸽派可改善流动性预期",
                    "policy_score": 5,
                    "risk": "中美关系、港股流动性、地缘风险首当其冲",
                },
            },
        }

    def get_commodity_recommendations(self) -> Dict[str, Dict]:
        """获取商品推荐（5月1日更新）"""
        return {
            "铜": {
                "trend": "看涨",
                "policy_score": 7,
                "action": "高配",
                "reason": "铜矿紧缺+新能源需求+关税预期+美元承压",
                "price_target": "11,400美元/吨（年内）",
            },
            "黄金": {
                "trend": "看涨",
                "policy_score": 9,
                "action": "超配",
                "reason": "央行购金+地缘避险+美元体系松动+鲍威尔卸任政策真空",
                "price_target": "5,000美元（年内）/ 6,300美元（2026年底，摩根大通）",
            },
            "原油": {
                "trend": "高位震荡偏强",
                "policy_score": 5,
                "action": "中配",
                "reason": "5月美伊海上封锁+霍尔木兹封锁+OPEC分裂；油气煤化工接力上行",
                "price_target": "Brent 100-120美元/桶（5月）",
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
            "美伊冲突升级至海上封锁（4/29），霍尔木兹海峡持续封锁，油价飙升输入性通胀",
            "阿联酋5/1退出OPEC+，产油国阵营分化，能源供给预期更复杂",
            "中美贸易战高压持续，半导体232关税延续+小额免税取消+转口封堵",
            "台海地缘政治风险上升，2026年被视为高风险窗口",
            "美联储4/29 FOMC 8:4分歧维持高利率，市场已逆转预期至2027年加息",
            "鲍威尔5/15卸任过渡期，沃什接任的政策不确定性",
            "高估值科技板块（AI/芯片）拥挤交易回吐风险",
            "房地产仍在负增长（-0.1%），底部确认时间不确定",
            "部分新兴产业产能过剩（光伏/锂/电池）",
            "CPI仅0.9%，通缩阴影未完全消除",
        ]

        opportunities = [
            "4/28政治局会议'稳定+增强资本市场信心'，战略层级升级（信心建设战）",
            "Q1 GDP 5.0%超预期，业绩报告压制消退，进入业绩真空期",
            "近5年五一节后开门红概率80%+（历史规律）",
            "'十五五'六张网投资超7万亿+创投引导基金撬动万亿",
            "全面实施'人工智能+'行动，发展智能经济新形态",
            "投资风格从'虚拟经济'切换至'实物资产'主导的涨价逻辑",
            "黄金牛市仍在延续（4630美元创新高，目标6300美元）",
            "国产替代加速（半导体/工业软件/高端装备）",
            "AI应用进入盈利兑现期，具身智能列为未来产业",
            "科技体制改革：职务科技成果赋权+首台套补贴30-50%",
            "储能突破临界点，新型储能列为新兴支柱产业",
            "财政政策积极（赤字率4%+特别国债1.3万亿），基建托底",
            "中国对所有非洲建交国零关税（5/1生效），多元化市场打开",
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
        "基于政策分析，对策略引擎的输出修正（5月1日更新）：",
        "",
        "| 维度 | 基准判断 | 政策修正 | 最终建议 |",
        "|------|----------|----------|----------|",
        "| 周期阶段 | 复苏期 | 政治局信心建设战 | **复苏期（节后红五月）** |",
        "| 仓位建议 | 50-70% | 业绩真空+信心建设 | **60-75%** |",
        "| 核心赛道 | AI+新能源 | 实物资产主线+硬科技 | **黄金+有色+芯片+创新药+机器人** |",
        "| 黄金配置 | 10-15% | 地缘升级+美联储真空 | **15-20%（超配）** |",
        "| 有色/资源 | 5% | 实物资产接力主线 | **7-8%** |",
        "| 港股配置 | 中性 | 沃什接任不确定性 | **谨慎中性** |",
        "| 4%定投法 | 启用 | 节后高开震荡概率高 | **启用（节后首日观察后再定投）** |",
        "| 现金留存 | 10% | 突发地缘缓冲 | **10-15%** |",
        "",
        "### 节后开市操作纪律（5月6日起）",
        "",
        "1. **首日不追涨**：观察前30分钟成交量与板块轮动方向",
        "2. **不杀跌**：若假期外盘大跌，等待恐慌释放后分批吸纳",
        "3. **关键观察**：黄金/原油/有色是否延续涨势 → 决定实物资产主线力度",
        "4. **触发再操作信号**：",
        "   - 美伊达成停火 → 减黄金、加出口链",
        "   - 油价破125美元 → 增配油气煤炭",
        "   - 沃什释放鸽派信号 → 加仓成长板块",
        "   - 上证创年内新高且放量 → 启动盈利分层止盈",
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
