#!/usr/bin/env python3
"""
ETF多维度甄选系统

基于5大维度对候选ETF进行量化评分，输出最优投资组合：
1. 周期定位匹配度（康波复苏期受益程度）
2. 十五五政策匹配度（与国家重点产业契合度）
3. 地缘政治韧性（中美脱钩/台海风险下的抗压能力）
4. 市场估值合理性（PE/PB分位、E/P等）
5. 盈利景气度（行业增长预期、业绩确定性）

用法:
    python scripts/etf_selector.py --evaluate       # 评估候选池
    python scripts/etf_selector.py --select         # 筛选最优组合
    python scripts/etf_selector.py --compare        # 对比新旧组合

作者: Claude Code
日期: 2026-05-01
"""

import argparse
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

BASE_DIR = Path(__file__).parent.parent
REPORTS_DIR = BASE_DIR / "reports"
DATA_DIR = BASE_DIR / "data"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# 数据模型
# ---------------------------------------------------------------------------

@dataclass
class ETFScore:
    """单只ETF评分结果"""
    code: str
    name: str
    # 五大维度得分 (0-10)
    cycle_score: float          # 周期定位匹配度
    policy_score: float         # 十五五政策匹配度
    geo_score: float            # 地缘政治韧性
    valuation_score: float      # 估值合理性
    earnings_score: float       # 盈利景气度
    # 综合
    total_score: float
    tier: str                   # core / major / minor / exclude
    target_pct: float
    rationale: str


# ---------------------------------------------------------------------------
# 候选ETF池（含现有持仓 + 备选）
# ---------------------------------------------------------------------------

CANDIDATE_ETFS = {
    # =========================================================================
    # 宽基指数 (6只)
    # =========================================================================
    "510300": {
        "name": "沪深300ETF", "category": "宽基", "exposure": "大盘蓝筹",
        "pe_ttm": 14.6, "pb": 1.46, "pe_percentile": 0.86, "pb_percentile": 0.57, "ep_ratio": 0.068,
    },
    "560610": {
        "name": "中证A500ETF", "category": "宽基", "exposure": "中大盘均衡",
        "pe_ttm": 15.2, "pb": 1.52, "pe_percentile": 0.75, "pb_percentile": 0.50, "ep_ratio": 0.066,
    },
    "510050": {
        "name": "上证50ETF", "category": "宽基", "exposure": "超大盘蓝筹",
        "pe_ttm": 11.5, "pb": 1.25, "pe_percentile": 0.70, "pb_percentile": 0.55, "ep_ratio": 0.087,
    },
    "510500": {
        "name": "中证500ETF", "category": "宽基", "exposure": "中盘成长",
        "pe_ttm": 22.0, "pb": 1.75, "pe_percentile": 0.09, "pb_percentile": 0.10, "ep_ratio": 0.045,
    },
    "159915": {
        "name": "创业板ETF", "category": "宽基", "exposure": "创业板龙头",
        "pe_ttm": 32.0, "pb": 4.5, "pe_percentile": 0.15, "pb_percentile": 0.20, "ep_ratio": 0.031,
    },
    "512100": {
        "name": "中证1000ETF", "category": "宽基", "exposure": "小盘成长",
        "pe_ttm": 35.0, "pb": 2.2, "pe_percentile": 0.30, "pb_percentile": 0.35, "ep_ratio": 0.029,
    },

    # =========================================================================
    # 港股/QDII (5只)
    # =========================================================================
    "513130": {
        "name": "恒生科技ETF", "category": "港股", "exposure": "港股科技龙头",
        "pe_ttm": 22.0, "pb": 2.1, "pe_percentile": 0.35, "pb_percentile": 0.20, "ep_ratio": 0.045,
    },
    "513100": {
        "name": "纳斯达克100ETF", "category": "QDII", "exposure": "美股科技巨头",
        "pe_ttm": 28.0, "pb": 8.0, "pe_percentile": 0.80, "pb_percentile": 0.85, "ep_ratio": 0.036,
    },
    "513500": {
        "name": "标普500ETF", "category": "QDII", "exposure": "美股大盘",
        "pe_ttm": 24.0, "pb": 4.8, "pe_percentile": 0.85, "pb_percentile": 0.88, "ep_ratio": 0.042,
    },
    "513520": {
        "name": "日经225ETF", "category": "QDII", "exposure": "日本大盘股",
        "pe_ttm": 18.0, "pb": 1.8, "pe_percentile": 0.60, "pb_percentile": 0.55, "ep_ratio": 0.056,
    },
    "159941": {
        "name": "纳斯达克ETF", "category": "QDII", "exposure": "纳斯达克100（规模最大）",
        "pe_ttm": 28.0, "pb": 8.0, "pe_percentile": 0.80, "pb_percentile": 0.85, "ep_ratio": 0.036,
    },

    # =========================================================================
    # 科技 (8只)
    # =========================================================================
    "159995": {
        "name": "芯片ETF", "category": "科技", "exposure": "半导体全产业链",
        "pe_ttm": 85.0, "pb": 4.0, "pe_percentile": 0.70, "pb_percentile": 0.50, "ep_ratio": 0.012,
    },
    "515880": {
        "name": "科技ETF", "category": "科技", "exposure": "泛科技（电子/计算机/通信）",
        "pe_ttm": 55.0, "pb": 3.5, "pe_percentile": 0.65, "pb_percentile": 0.50, "ep_ratio": 0.018,
    },
    "588000": {
        "name": "科创50ETF", "category": "科技", "exposure": "科创板龙头（硬科技）",
        "pe_ttm": 75.0, "pb": 4.2, "pe_percentile": 0.55, "pb_percentile": 0.30, "ep_ratio": 0.013,
    },
    "159819": {
        "name": "人工智能ETF", "category": "科技", "exposure": "AI产业链（算力/算法/应用）",
        "pe_ttm": 60.0, "pb": 3.8, "pe_percentile": 0.70, "pb_percentile": 0.60, "ep_ratio": 0.017,
    },
    "515050": {
        "name": "5GETF", "category": "科技", "exposure": "5G通信产业链",
        "pe_ttm": 30.0, "pb": 2.5, "pe_percentile": 0.40, "pb_percentile": 0.35, "ep_ratio": 0.033,
    },
    "516510": {
        "name": "云计算ETF", "category": "科技", "exposure": "云计算/大数据",
        "pe_ttm": 50.0, "pb": 3.5, "pe_percentile": 0.55, "pb_percentile": 0.50, "ep_ratio": 0.020,
    },
    "159869": {
        "name": "游戏ETF", "category": "科技", "exposure": "游戏/元宇宙",
        "pe_ttm": 22.0, "pb": 2.2, "pe_percentile": 0.45, "pb_percentile": 0.40, "ep_ratio": 0.045,
    },
    "515230": {
        "name": "软件ETF", "category": "科技", "exposure": "软件/信创",
        "pe_ttm": 55.0, "pb": 3.8, "pe_percentile": 0.50, "pb_percentile": 0.45, "ep_ratio": 0.018,
    },

    # =========================================================================
    # 新能源 (5只)
    # =========================================================================
    "159857": {
        "name": "光伏ETF", "category": "新能源", "exposure": "光伏产业链",
        "pe_ttm": 18.0, "pb": 1.8, "pe_percentile": 0.15, "pb_percentile": 0.25, "ep_ratio": 0.056,
    },
    "159755": {
        "name": "电池ETF", "category": "新能源", "exposure": "锂电池产业链",
        "pe_ttm": 25.0, "pb": 2.2, "pe_percentile": 0.20, "pb_percentile": 0.15, "ep_ratio": 0.040,
    },
    "515030": {
        "name": "新能源车ETF", "category": "新能源", "exposure": "整车+零部件",
        "pe_ttm": 22.0, "pb": 2.0, "pe_percentile": 0.20, "pb_percentile": 0.15, "ep_ratio": 0.045,
    },
    "159790": {
        "name": "碳中和ETF", "category": "新能源", "exposure": "碳中和全产业链",
        "pe_ttm": 20.0, "pb": 2.0, "pe_percentile": 0.20, "pb_percentile": 0.20, "ep_ratio": 0.050,
    },
    "516160": {
        "name": "新能源ETF", "category": "新能源", "exposure": "新能源综合",
        "pe_ttm": 20.0, "pb": 2.1, "pe_percentile": 0.18, "pb_percentile": 0.22, "ep_ratio": 0.050,
    },

    # =========================================================================
    # 医药 (4只)
    # =========================================================================
    "159992": {
        "name": "创新药ETF", "category": "医药", "exposure": "创新药研发",
        "pe_ttm": None, "pb": 3.5, "pe_percentile": None, "pb_percentile": 0.30, "ep_ratio": None,
    },
    "159898": {
        "name": "医疗器械ETF", "category": "医药", "exposure": "高端医疗器械",
        "pe_ttm": 28.0, "pb": 3.8, "pe_percentile": 0.25, "pb_percentile": 0.20, "ep_ratio": 0.036,
    },
    "159647": {
        "name": "中药ETF", "category": "医药", "exposure": "中药/品牌中药",
        "pe_ttm": 18.0, "pb": 2.8, "pe_percentile": 0.20, "pb_percentile": 0.20, "ep_ratio": 0.056,
    },
    "512170": {
        "name": "医疗ETF", "category": "医药", "exposure": "医疗服务+器械+药房",
        "pe_ttm": 30.0, "pb": 4.2, "pe_percentile": 0.15, "pb_percentile": 0.15, "ep_ratio": 0.033,
    },

    # =========================================================================
    # 高端制造/军工 (4只)
    # =========================================================================
    "562500": {
        "name": "机器人ETF", "category": "高端制造", "exposure": "工业机器人+人形机器人",
        "pe_ttm": 45.0, "pb": 3.2, "pe_percentile": 0.60, "pb_percentile": 0.55, "ep_ratio": 0.022,
    },
    "512660": {
        "name": "军工ETF", "category": "军工", "exposure": "军工全产业链",
        "pe_ttm": 45.0, "pb": 3.0, "pe_percentile": 0.25, "pb_percentile": 0.30, "ep_ratio": 0.022,
    },
    "512710": {
        "name": "军工龙头ETF", "category": "军工", "exposure": "军工核心标的",
        "pe_ttm": 40.0, "pb": 2.8, "pe_percentile": 0.20, "pb_percentile": 0.25, "ep_ratio": 0.025,
    },
    "159638": {
        "name": "高端装备ETF", "category": "高端制造", "exposure": "高端装备/工业母机",
        "pe_ttm": 35.0, "pb": 2.5, "pe_percentile": 0.35, "pb_percentile": 0.40, "ep_ratio": 0.029,
    },

    # =========================================================================
    # 金融 (3只)
    # =========================================================================
    "512800": {
        "name": "银行ETF", "category": "金融", "exposure": "上市银行",
        "pe_ttm": 5.5, "pb": 0.55, "pe_percentile": 0.30, "pb_percentile": 0.15, "ep_ratio": 0.182,
    },
    "512880": {
        "name": "证券ETF", "category": "金融", "exposure": "券商股",
        "pe_ttm": 18.0, "pb": 1.3, "pe_percentile": 0.40, "pb_percentile": 0.20, "ep_ratio": 0.056,
    },
    "512070": {
        "name": "证券保险ETF", "category": "金融", "exposure": "券商+保险",
        "pe_ttm": 15.0, "pb": 1.4, "pe_percentile": 0.35, "pb_percentile": 0.25, "ep_ratio": 0.067,
    },

    # =========================================================================
    # 消费 (5只)
    # =========================================================================
    "512690": {
        "name": "酒ETF", "category": "消费", "exposure": "白酒龙头",
        "pe_ttm": 20.0, "pb": 5.5, "pe_percentile": 0.25, "pb_percentile": 0.35, "ep_ratio": 0.050,
    },
    "159928": {
        "name": "消费ETF", "category": "消费", "exposure": "主要消费龙头",
        "pe_ttm": 25.0, "pb": 5.0, "pe_percentile": 0.35, "pb_percentile": 0.40, "ep_ratio": 0.040,
    },
    "515170": {
        "name": "食品饮料ETF", "category": "消费", "exposure": "食品饮料",
        "pe_ttm": 28.0, "pb": 6.5, "pe_percentile": 0.40, "pb_percentile": 0.50, "ep_ratio": 0.036,
    },
    "159996": {
        "name": "家电ETF", "category": "消费", "exposure": "家电龙头",
        "pe_ttm": 14.0, "pb": 2.5, "pe_percentile": 0.30, "pb_percentile": 0.35, "ep_ratio": 0.071,
    },
    "159825": {
        "name": "农业ETF", "category": "消费", "exposure": "农林牧渔",
        "pe_ttm": 22.0, "pb": 2.8, "pe_percentile": 0.25, "pb_percentile": 0.20, "ep_ratio": 0.045,
    },

    # =========================================================================
    # 周期/商品 (6只)
    # =========================================================================
    "518880": {
        "name": "黄金ETF", "category": "商品", "exposure": "现货黄金",
        "pe_ttm": None, "pb": None, "pe_percentile": None, "pb_percentile": None, "ep_ratio": None,
    },
    "512400": {
        "name": "有色金属ETF", "category": "商品", "exposure": "铜铝锌锂等工业金属",
        "pe_ttm": 20.0, "pb": 2.0, "pe_percentile": 0.30, "pb_percentile": 0.40, "ep_ratio": 0.050,
    },
    "515220": {
        "name": "煤炭ETF", "category": "周期", "exposure": "煤炭开采",
        "pe_ttm": 8.0, "pb": 1.1, "pe_percentile": 0.55, "pb_percentile": 0.50, "ep_ratio": 0.125,
    },
    "516780": {
        "name": "稀土ETF", "category": "周期", "exposure": "稀土永磁材料",
        "pe_ttm": 35.0, "pb": 3.5, "pe_percentile": 0.35, "pb_percentile": 0.30, "ep_ratio": 0.029,
    },
    "159870": {
        "name": "化工ETF", "category": "周期", "exposure": "化工龙头",
        "pe_ttm": 15.0, "pb": 1.8, "pe_percentile": 0.30, "pb_percentile": 0.25, "ep_ratio": 0.067,
    },
    "159930": {
        "name": "能源ETF", "category": "周期", "exposure": "能源（油气煤）",
        "pe_ttm": 10.0, "pb": 1.2, "pe_percentile": 0.50, "pb_percentile": 0.45, "ep_ratio": 0.100,
    },

    # =========================================================================
    # 防御/红利 (2只)
    # =========================================================================
    "512890": {
        "name": "红利低波ETF", "category": "防御", "exposure": "高股息低波动股票",
        "pe_ttm": 7.0, "pb": 0.75, "pe_percentile": 0.55, "pb_percentile": 0.45, "ep_ratio": 0.143,
    },
    "511010": {
        "name": "国债ETF", "category": "债券", "exposure": "10年期国债",
        "pe_ttm": None, "pb": None, "pe_percentile": None, "pb_percentile": None, "ep_ratio": None,
    },

    # =========================================================================
    # 基建/公用 (4只)
    # =========================================================================
    "159611": {
        "name": "电力ETF", "category": "公用事业", "exposure": "电力运营商",
        "pe_ttm": 16.0, "pb": 1.4, "pe_percentile": 0.40, "pb_percentile": 0.35, "ep_ratio": 0.063,
    },
    "516950": {
        "name": "基建ETF", "category": "基建", "exposure": "基建工程",
        "pe_ttm": 10.0, "pb": 0.85, "pe_percentile": 0.25, "pb_percentile": 0.20, "ep_ratio": 0.100,
    },
    "159745": {
        "name": "建材ETF", "category": "基建", "exposure": "建筑材料",
        "pe_ttm": 14.0, "pb": 1.3, "pe_percentile": 0.20, "pb_percentile": 0.15, "ep_ratio": 0.071,
    },
    "512200": {
        "name": "房地产ETF", "category": "房地产", "exposure": "房地产开发",
        "pe_ttm": 12.0, "pb": 0.8, "pe_percentile": 0.45, "pb_percentile": 0.35, "ep_ratio": 0.083,
    },

    # =========================================================================
    # 传媒/其他 (4只)
    # =========================================================================
    "512980": {
        "name": "传媒ETF", "category": "传媒", "exposure": "传媒/影视/广告",
        "pe_ttm": 25.0, "pb": 2.2, "pe_percentile": 0.35, "pb_percentile": 0.40, "ep_ratio": 0.040,
    },
    "159766": {
        "name": "旅游ETF", "category": "消费", "exposure": "旅游/酒店/免税",
        "pe_ttm": 30.0, "pb": 3.0, "pe_percentile": 0.25, "pb_percentile": 0.20, "ep_ratio": 0.033,
    },
    "511380": {
        "name": "可转债ETF", "category": "债券", "exposure": "可转换债券",
        "pe_ttm": None, "pb": None, "pe_percentile": None, "pb_percentile": None, "ep_ratio": None,
    },
    "513050": {
        "name": "中概互联ETF", "category": "港股", "exposure": "海外中国互联网",
        "pe_ttm": 18.0, "pb": 2.0, "pe_percentile": 0.20, "pb_percentile": 0.15, "ep_ratio": 0.056,
    },
}


# ---------------------------------------------------------------------------
# 评分引擎
# ---------------------------------------------------------------------------

def _load_config():
    try:
        from config_loader import load_config
        return load_config()
    except Exception:
        return None


class ETFSelector:
    """ETF多维度甄选器"""

    DEFAULT_WEIGHTS = {
        "cycle": 0.20, "policy": 0.25, "geo": 0.20,
        "valuation": 0.20, "earnings": 0.15,
    }

    def __init__(self):
        cfg = _load_config()
        if cfg:
            self.WEIGHTS = cfg.etf_weights()
            # Merge: config provides real PE/PB data, code provides full candidate pool
            config_candidates = cfg.etf_candidates()
            # Start with all code-defined candidates, then overlay config data
            self.candidates = dict(CANDIDATE_ETFS)
            for code, info in config_candidates.items():
                if code in self.candidates:
                    # Overlay live valuation data from config onto code defaults
                    for key in ("pe_ttm", "pb", "pe_percentile", "pb_percentile", "ep_ratio"):
                        if key in info and info[key] is not None:
                            self.candidates[code][key] = info[key]
            self._scoring = cfg.etf_scoring()
            self._from_config = True
        else:
            self.WEIGHTS = self.DEFAULT_WEIGHTS
            self.candidates = CANDIDATE_ETFS
            self._scoring = {}
            self._from_config = False
        self._apply_live_valuations()

    def _apply_live_valuations(self):
        """Fetch live index PE/PB and merge into candidates."""
        try:
            from valuation_fetcher import fetch_index_valuations, apply_valuations_to_candidates
            valuations = fetch_index_valuations()
            if valuations:
                self.candidates = apply_valuations_to_candidates(self.candidates, valuations)
        except Exception:
            pass  # network unavailable — use config data as-is

    def score_cycle(self, code: str, info: dict) -> float:
        """周期定位匹配度：康波复苏期哪些赛道最受益"""
        # Always use the full code-level map (config provides overrides, code provides base)
        scoring = self._scoring
        if scoring:
            cycle_map = scoring.get("cycle", {})
            overrides = scoring.get("cycle_overrides", {})
        else:
            cycle_map = {}
            overrides = {}

        # Fallback to hardcoded maps for categories/codes not in config
        _default_cycle_map = {
            "宽基": 6.0, "港股": 5.0, "新能源": 7.5, "医药": 7.0,
            "高端制造": 8.5, "公用事业": 5.5, "科技": 9.0, "防御": 4.5,
            "金融": 5.0, "商品": 7.5, "消费": 5.5, "QDII": 4.0,
            "军工": 6.0, "周期": 7.5, "传媒": 5.0, "房地产": 4.0,
            "债券": 4.0, "基建": 6.0,
        }
        _default_overrides = {
            "159995": 9.5, "562500": 9.0, "518880": 8.5, "512400": 7.5,
            "159992": 8.0, "159819": 9.0, "588000": 9.0,
            "515220": 8.0, "159930": 8.0, "516950": 6.5, "159790": 7.5,
            "512660": 6.5, "512710": 6.5, "515050": 8.0, "516510": 8.0,
            "515230": 8.5, "159647": 6.5, "159638": 8.0,
        }
        for k, v in _default_cycle_map.items():
            cycle_map.setdefault(k, v)
        for k, v in _default_overrides.items():
            overrides.setdefault(k, v)

        base = overrides.get(code, cycle_map.get(info["category"], 5.0))
        return min(10.0, base)

    def score_policy(self, code: str, info: dict) -> float:
        """十五五政策匹配度"""
        scoring = self._scoring
        if scoring:
            policy_map = scoring.get("policy", {})
        else:
            policy_map = {}
        _default_policy_map = {
            "510300": 6.5, "560610": 7.0, "510050": 6.0, "510500": 6.5,
            "159915": 7.0, "512100": 6.5,
            "513130": 4.5, "513100": 3.0, "513500": 3.0, "513520": 3.5,
            "159941": 3.0, "513050": 4.0,
            "159857": 7.5, "159755": 6.5, "515030": 7.0, "159790": 8.0, "516160": 7.0,
            "159992": 9.0, "159898": 8.5, "159647": 7.5, "512170": 8.0,
            "159995": 9.5, "515880": 8.0, "588000": 8.5, "159819": 8.5,
            "515050": 7.0, "516510": 7.5, "159869": 5.5, "515230": 8.0,
            "562500": 9.0, "159638": 8.0, "512660": 6.5, "512710": 6.5,
            "512800": 5.0, "512880": 7.0, "512070": 6.0,
            "512690": 4.5, "159928": 5.0, "515170": 5.0, "159996": 5.5, "159825": 5.5,
            "159766": 5.0,
            "518880": 7.5, "512400": 8.0, "515220": 6.5, "516780": 7.0,
            "159870": 7.0, "159930": 7.5,
            "512890": 6.0, "511010": 4.0, "511380": 4.5,
            "159611": 6.5, "516950": 7.0, "159745": 6.0, "512200": 4.0,
            "512980": 4.5,
        }
        for k, v in _default_policy_map.items():
            policy_map.setdefault(k, v)
        return policy_map.get(code, 5.0)

    def score_geo(self, code: str, info: dict) -> float:
        """地缘政治韧性"""
        scoring = self._scoring
        if scoring:
            geo_map = scoring.get("geo", {})
        else:
            geo_map = {}
        _default_geo_map = {
            "510300": 6.0, "560610": 6.5, "510050": 5.5, "510500": 6.0,
            "159915": 6.5, "512100": 6.0,
            "513130": 3.0, "513100": 2.0, "513500": 2.5, "513520": 3.5,
            "159941": 2.0, "513050": 2.5,
            "159857": 7.0, "159755": 6.5, "515030": 6.0, "159790": 7.5, "516160": 7.0,
            "159992": 7.5, "159898": 8.0, "159647": 7.0, "512170": 7.5,
            "159995": 8.5, "515880": 7.0, "588000": 8.0, "159819": 7.0,
            "515050": 6.5, "516510": 6.5, "159869": 5.5, "515230": 8.0,
            "562500": 7.5, "159638": 7.5, "512660": 8.5, "512710": 8.5,
            "512800": 6.5, "512880": 6.0, "512070": 6.0,
            "512690": 5.5, "159928": 5.5, "515170": 5.0, "159996": 5.5, "159825": 6.5,
            "159766": 5.5,
            "518880": 9.5, "512400": 7.5, "515220": 7.0, "516780": 7.5,
            "159870": 6.5, "159930": 7.5,
            "512890": 7.5, "511010": 5.0, "511380": 5.0,
            "159611": 7.5, "516950": 7.0, "159745": 6.0, "512200": 5.0,
            "512980": 5.0,
        }
        for k, v in _default_geo_map.items():
            geo_map.setdefault(k, v)
        return geo_map.get(code, 5.0)

    def score_valuation(self, code: str, info: dict) -> float:
        """估值合理性：PE/PB分位越低越合理，但需结合E/P"""
        p = info
        scores = []

        # PE分位评分（越低越好）
        if p["pe_percentile"] is not None:
            if p["pe_percentile"] <= 0.20:
                scores.append(9.0)
            elif p["pe_percentile"] <= 0.40:
                scores.append(7.5)
            elif p["pe_percentile"] <= 0.60:
                scores.append(6.0)
            elif p["pe_percentile"] <= 0.80:
                scores.append(4.0)
            else:
                scores.append(2.0)

        # PB分位评分（越低越好）
        if p["pb_percentile"] is not None:
            if p["pb_percentile"] <= 0.20:
                scores.append(9.0)
            elif p["pb_percentile"] <= 0.40:
                scores.append(7.0)
            elif p["pb_percentile"] <= 0.60:
                scores.append(5.5)
            elif p["pb_percentile"] <= 0.80:
                scores.append(4.0)
            else:
                scores.append(2.5)

        # E/P评分（格雷厄姆指标，越高越好）
        if p["ep_ratio"] is not None:
            if p["ep_ratio"] >= 0.10:
                scores.append(9.0)
            elif p["ep_ratio"] >= 0.07:
                scores.append(7.0)
            elif p["ep_ratio"] >= 0.05:
                scores.append(5.0)
            elif p["ep_ratio"] >= 0.03:
                scores.append(3.5)
            else:
                scores.append(2.0)

        # 黄金无PE/PB，用避险需求溢价评分
        if code == "518880":
            scores = [7.5]  # 地缘风险下估值逻辑不同

        # 创新药多亏损，用政策/管线估值
        if code == "159992":
            scores = [6.5]

        # 债券类ETF无PE/PB，用利率周期逻辑
        if code in ("511010", "511380"):
            scores = [5.0]  # 复苏期债券中性偏低

        return sum(scores) / len(scores) if scores else 5.0

    def score_earnings(self, code: str, info: dict) -> float:
        """盈利景气度"""
        scoring = self._scoring
        if scoring:
            earnings_map = scoring.get("earnings", {})
        else:
            earnings_map = {}
        _default_earnings_map = {
            "510300": 5.5, "560610": 6.0, "510050": 5.0, "510500": 5.5,
            "159915": 6.0, "512100": 5.5,
            "513130": 6.5, "513100": 6.5, "513500": 6.0, "513520": 5.5,
            "159941": 6.5, "513050": 5.5,
            "159857": 4.5, "159755": 4.0, "515030": 5.5, "159790": 5.5, "516160": 5.0,
            "159992": 7.5, "159898": 6.5, "159647": 6.0, "512170": 6.0,
            "159995": 7.5, "515880": 7.5, "588000": 6.5, "159819": 7.5,
            "515050": 5.5, "516510": 6.0, "159869": 5.5, "515230": 7.0,
            "562500": 7.0, "159638": 6.0, "512660": 5.5, "512710": 5.5,
            "512800": 5.0, "512880": 6.0, "512070": 5.5,
            "512690": 4.5, "159928": 4.5, "515170": 4.5, "159996": 5.5, "159825": 5.0,
            "159766": 4.0,
            "518880": 7.0, "512400": 7.0, "515220": 7.5, "516780": 5.5,
            "159870": 6.5, "159930": 7.5,
            "512890": 6.0, "511010": 3.0, "511380": 4.0,
            "159611": 6.0, "516950": 5.5, "159745": 5.0, "512200": 3.5,
            "512980": 4.5,
        }
        for k, v in _default_earnings_map.items():
            earnings_map.setdefault(k, v)
        return earnings_map.get(code, 5.0)

    def evaluate_all(self) -> List[ETFScore]:
        """评估所有候选ETF"""
        results = []
        for code, info in self.candidates.items():
            c = self.score_cycle(code, info)
            p = self.score_policy(code, info)
            g = self.score_geo(code, info)
            v = self.score_valuation(code, info)
            e = self.score_earnings(code, info)

            total = (c * self.WEIGHTS["cycle"] +
                     p * self.WEIGHTS["policy"] +
                     g * self.WEIGHTS["geo"] +
                     v * self.WEIGHTS["valuation"] +
                     e * self.WEIGHTS["earnings"])

            # 分级
            if total >= 8.0:
                tier = "core"
            elif total >= 6.8:
                tier = "major"
            elif total >= 5.5:
                tier = "minor"
            else:
                tier = "exclude"

            # 权重映射
            weight_map = {"core": 10.0, "major": 7.0, "minor": 4.0, "exclude": 0.0}
            target = weight_map[tier]

            # 生成理由
            reasons = []
            if p >= 8.5:
                reasons.append("十五五核心产业")
            if g >= 8.0:
                reasons.append("地缘韧性极强")
            if v >= 7.5:
                reasons.append("估值合理")
            if e >= 7.0:
                reasons.append("景气上行")
            if c >= 8.5:
                reasons.append("康波核心赛道")
            rationale = "；".join(reasons) if reasons else "综合评分中等"

            results.append(ETFScore(
                code=code, name=info["name"],
                cycle_score=c, policy_score=p, geo_score=g,
                valuation_score=v, earnings_score=e,
                total_score=total, tier=tier, target_pct=target,
                rationale=rationale,
            ))

        return sorted(results, key=lambda x: x.total_score, reverse=True)

    # 组合约束：某些类别必须至少保留1只
    MANDATORY_CATEGORIES = {
        "宽基": 1,    # 必须至少1只宽基
        "防御": 1,    # 必须至少1只防御
    }

    def select_portfolio(self, total_pct: float = 100.0, max_holdings: int = 14) -> List[ETFScore]:
        """筛选最优组合（带约束）"""
        scores = self.evaluate_all()

        # 按tier分组
        tiers = {"core": [], "major": [], "minor": [], "exclude": []}
        for s in scores:
            tiers[s.tier].append(s)

        selected = []
        selected_codes = set()
        remaining = total_pct

        # 阶段1：选core和major（前N名）
        candidates = tiers["core"] + tiers["major"]
        for s in candidates:
            if len(selected) >= max_holdings or remaining <= 0:
                break
            selected.append(s)
            selected_codes.add(s.code)
            remaining -= s.target_pct

        # 阶段2：检查约束，如有缺失强制替换最低分非强制类别标的
        mandatory_cats = set(self.MANDATORY_CATEGORIES.keys())
        for cat, min_count in self.MANDATORY_CATEGORIES.items():
            current_count = sum(1 for s in selected if self.candidates[s.code]["category"] == cat)
            if current_count < min_count:
                need = min_count - current_count
                # Find best ETF in this category not yet selected
                missing = [s for s in scores
                          if self.candidates[s.code]["category"] == cat
                          and s.code not in selected_codes]
                missing.sort(key=lambda x: x.total_score, reverse=True)
                for s in missing[:need]:
                    if len(selected) >= max_holdings:
                        # Remove lowest-scoring non-mandatory ETF to make room
                        removable = [(i, x) for i, x in enumerate(selected)
                                     if self.candidates[x.code]["category"] not in mandatory_cats]
                        if removable:
                            worst_idx, _ = min(removable, key=lambda t: t[1].total_score)
                            removed = selected.pop(worst_idx)
                            selected_codes.discard(removed.code)
                            remaining += removed.target_pct
                        else:
                            # All are mandatory — replace the lowest scorer
                            worst = min(selected, key=lambda x: x.total_score)
                            selected.remove(worst)
                            selected_codes.discard(worst.code)
                            remaining += worst.target_pct
                    selected.append(s)
                    selected_codes.add(s.code)
                    remaining -= s.target_pct

        # 阶段3：用minor补足到max_holdings或remaining耗尽
        for s in tiers["minor"]:
            if len(selected) >= max_holdings or remaining <= 0:
                break
            if s.code in selected_codes:
                continue
            selected.append(s)
            selected_codes.add(s.code)
            remaining -= s.target_pct

        # 阶段4：差异化权重分配
        # core/major按总分排序给予阶梯权重
        selected.sort(key=lambda x: x.total_score, reverse=True)

        # 权重阶梯：前6名给较高权重，后几名给较低权重
        n = len(selected)
        weights = []
        for i, s in enumerate(selected):
            if i < 3:           # TOP3
                w = 10.0
            elif i < 6:         # 4-6名
                w = 8.0
            elif i < 9:         # 7-9名
                w = 6.0
            elif i < 12:        # 10-12名
                w = 5.0
            else:               # 其余
                w = 4.0
            # 5月1日特殊处理：地缘风险升级下提高实物资产配置
            if s.code == "518880":  # 黄金：5月美伊海上封锁+鲍威尔卸任真空
                w = max(w, 12.0)
            elif s.code == "512400":  # 有色金属：实物资产接力主线
                w = max(w, 7.0)
            # 5月1日：盈利景气欠佳的标的小幅降权
            elif s.code in ("159755", "515030"):  # 电池/新能源车：盈利偏弱
                w = min(w, 4.0)
            weights.append(w)

        # 归一化
        total_w = sum(weights)
        for i, s in enumerate(selected):
            s.target_pct = round(weights[i] / total_w * 100, 1)

        # 微调确保总和=100%
        diff = 100.0 - sum(s.target_pct for s in selected)
        if diff != 0 and selected:
            selected[0].target_pct = round(selected[0].target_pct + diff, 1)

        return selected


# ---------------------------------------------------------------------------
# 报告生成
# ---------------------------------------------------------------------------

def generate_evaluation_report(selector: ETFSelector) -> str:
    """生成评估报告"""
    scores = selector.evaluate_all()
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    lines = [
        f"# ETF多维度甄选评估报告",
        f"",
        f"**生成时间**: {now}",
        f"**评估池规模**: {len(scores)}只ETF",
        f"**评分维度**: 周期定位(20%) + 十五五政策(25%) + 地缘韧性(20%) + 估值合理性(20%) + 盈利景气(15%)",
        f"",
        "---",
        "",
        "## 一、候选ETF全评分",
        "",
        "| 排名 | 代码 | 名称 | 周期 | 政策 | 地缘 | 估值 | 盈利 | **总分** | 分级 |",
        "|------|------|------|------|------|------|------|------|----------|------|",
    ]

    for i, s in enumerate(scores, 1):
        lines.append(
            f"| {i} | {s.code} | {s.name} | {s.cycle_score:.1f} | {s.policy_score:.1f} | "
            f"{s.geo_score:.1f} | {s.valuation_score:.1f} | {s.earnings_score:.1f} | "
            f"**{s.total_score:.2f}** | {s.tier} |"
        )

    lines.extend([
        "",
        "---",
        "",
        "## 二、分级说明",
        "",
        "| 分级 | 分数区间 | 配置权重 | 说明 |",
        "|------|----------|----------|------|",
        "| core | 8.0+ | 10% | 康波核心+十五五核心+地缘韧性极强 |",
        "| major | 6.8-8.0 | 7% | 政策受益显著或估值极具吸引力 |",
        "| minor | 5.5-6.8 | 4% | 防御配置或特定场景受益 |",
        "| exclude | <5.5 | 0% | 评分过低，不纳入组合 |",
        "",
    ])

    return "\n".join(lines)


def generate_portfolio_report(selector: ETFSelector) -> str:
    """生成组合配置报告"""
    portfolio = selector.select_portfolio()
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    lines = [
        f"# ETF甄选组合配置方案",
        f"",
        f"**生成时间**: {now}",
        f"**组合规模**: {len(portfolio)}只ETF",
        f"**总仓位**: 100%",
        f"",
        "---",
        "",
        "## 推荐组合",
        "",
        "| 代码 | 名称 | 权重 | 分级 | 投资理由 |",
        "|------|------|------|------|----------|",
    ]

    for s in portfolio:
        lines.append(f"| {s.code} | {s.name} | {s.target_pct:.1f}% | {s.tier} | {s.rationale} |")

    lines.extend([
        "",
        "---",
        "",
        "## 与旧组合对比",
        "",
        "### 新增标的",
        "",
    ])

    old_codes = {"510300", "560610", "513130", "159857", "159755", "159992",
                 "159898", "562500", "159611", "159995", "512890", "512800",
                 "518880", "512880"}
    new_codes = {s.code for s in portfolio}

    added = new_codes - old_codes
    removed = old_codes - new_codes

    if added:
        for code in added:
            s = next(x for x in portfolio if x.code == code)
            lines.append(f"- **{s.code} {s.name}** ({s.target_pct:.1f}%): {s.rationale}")
    else:
        lines.append("- 无新增")

    lines.extend(["", "### 移除标的", ""])
    if removed:
        for code in removed:
            info = selector.candidates[code]
            s = next((x for x in selector.evaluate_all() if x.code == code), None)
            if s:
                lines.append(f"- **{code} {info['name']}**: 总分{s.total_score:.2f}，{s.tier}级，评分过低")
    else:
        lines.append("- 无移除")

    lines.extend([
        "",
        "---",
        "",
        "*本报告基于多维度量化评分模型生成，仅供研究参考，不构成投资建议。*",
        "",
    ])

    return "\n".join(lines)


def update_portfolio_config(selector: ETFSelector):
    """更新 portfolio_config.json"""
    portfolio = selector.select_portfolio()

    config = {
        "total_capital": 900000,
        "holdings": [],
        "positions": {},
        "created_at": "2026-04-27T00:00:00",
        "last_updated": datetime.now().strftime("%Y-%m-%d"),
        "update_reason": f"ETF多维度甄选模型筛选，基于{datetime.now().strftime('%Y年%m月')}宏观研究",
        "selection_model": {
            "weights": selector.WEIGHTS,
            "evaluated_date": datetime.now().strftime("%Y-%m-%d"),
        },
    }

    for s in portfolio:
        info = selector.candidates[s.code]
        config["holdings"].append({
            "code": s.code,
            "name": s.name,
            "target_pct": s.target_pct,
            "type": "a_etf",
            "investment_rationale": s.rationale,
            "scores": {
                "cycle": s.cycle_score,
                "policy": s.policy_score,
                "geo": s.geo_score,
                "valuation": s.valuation_score,
                "earnings": s.earnings_score,
                "total": round(s.total_score, 2),
            },
            "rules": [{"kind": "price_percentile", "window": 500, "low": 0.20, "high": 0.80}],
        })

    path = DATA_DIR / "portfolio_config.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

    print(f"组合配置已更新: {path}")
    print(f"入选标的: {len(portfolio)}只")
    for s in portfolio:
        print(f"  {s.code} {s.name}: {s.target_pct:.1f}% (总分{s.total_score:.2f})")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="ETF多维度甄选系统")
    parser.add_argument("--evaluate", action="store_true", help="评估候选池并生成报告")
    parser.add_argument("--select", action="store_true", help="筛选最优组合")
    parser.add_argument("--update-config", action="store_true", help="更新portfolio_config.json")
    parser.add_argument("--compare", action="store_true", help="对比新旧组合")
    args = parser.parse_args()

    selector = ETFSelector()

    if args.evaluate:
        report = generate_evaluation_report(selector)
        path = REPORTS_DIR / f"etf_evaluation_{datetime.now().strftime('%Y%m%d')}.md"
        with open(path, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"评估报告已保存: {path}")
        # 打印前15名
        scores = selector.evaluate_all()
        print("\n评分前15名:")
        print("-" * 80)
        for i, s in enumerate(scores[:15], 1):
            print(f"{i:2d}. {s.code} {s.name:12s} 总分{s.total_score:.2f}  [{s.tier:6s}]  {s.rationale}")

    elif args.select:
        report = generate_portfolio_report(selector)
        path = REPORTS_DIR / f"etf_portfolio_{datetime.now().strftime('%Y%m%d')}.md"
        with open(path, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"组合报告已保存: {path}")
        print("\n推荐组合:")
        portfolio = selector.select_portfolio()
        for s in portfolio:
            print(f"  {s.code} {s.name}: {s.target_pct:.1f}% (总分{s.total_score:.2f})")

    elif args.update_config:
        update_portfolio_config(selector)

    elif args.compare:
        old = {"510300", "560610", "513130", "159857", "159755", "159992",
               "159898", "562500", "159611", "159995", "512890", "512800",
               "518880", "512880"}
        portfolio = selector.select_portfolio()
        new = {s.code for s in portfolio}
        print("新旧组合对比")
        print("=" * 60)
        print(f"旧组合: {sorted(old)}")
        print(f"新组合: {sorted(new)}")
        print(f"\n新增: {sorted(new - old) if new - old else '无'}")
        print(f"移除: {sorted(old - new) if old - new else '无'}")
        print(f"保留: {sorted(new & old)}")

    else:
        # 默认：评估+筛选
        scores = selector.evaluate_all()
        print("=" * 80)
        print("ETF多维度甄选结果")
        print("=" * 80)
        print(f"\n评分维度权重: 周期{selector.WEIGHTS['cycle']*100:.0f}% | "
              f"政策{selector.WEIGHTS['policy']*100:.0f}% | "
              f"地缘{selector.WEIGHTS['geo']*100:.0f}% | "
              f"估值{selector.WEIGHTS['valuation']*100:.0f}% | "
              f"盈利{selector.WEIGHTS['earnings']*100:.0f}%")
        print(f"\n候选池: {len(scores)}只ETF")
        print("\n评分前15名:")
        print("-" * 80)
        for i, s in enumerate(scores[:15], 1):
            print(f"{i:2d}. {s.code} {s.name:12s} 总分{s.total_score:.2f}  "
                  f"周期{s.cycle_score:.1f} 政策{s.policy_score:.1f} 地缘{s.geo_score:.1f} "
                  f"估值{s.valuation_score:.1f} 盈利{s.earnings_score:.1f}  [{s.tier}]")

        print("\n" + "=" * 80)
        portfolio = selector.select_portfolio()
        print(f"推荐组合 ({len(portfolio)}只):")
        print("-" * 80)
        for s in portfolio:
            print(f"  {s.code} {s.name}: {s.target_pct:.1f}% (总分{s.total_score:.2f}) - {s.rationale}")


if __name__ == "__main__":
    main()
