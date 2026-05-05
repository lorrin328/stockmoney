#!/usr/bin/env python3
"""
Index valuation data fetcher — pulls real PE/PB for major indices from East Money.

Used by etf_selector.py to replace hardcoded valuation estimates with live data.
Falls back gracefully when the network is unavailable.

Usage:
    from valuation_fetcher import fetch_index_valuations
    data = fetch_index_valuations()
    # data["000300"]["pe_ttm"] → 14.6
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import requests

BASE_DIR = Path(__file__).parent.parent
CACHE_PATH = BASE_DIR / "data" / "valuation_cache.json"
CACHE_TTL_HOURS = 6  # refresh every 6 hours


# East Money index code → our ETF/benchmark codes
INDEX_MAP = {
    "000300": {"name": "沪深300", "etf": "510300"},
    "000905": {"name": "中证500", "etf": None},
    "000688": {"name": "科创50", "etf": "588000"},
    "399006": {"name": "创业板指", "etf": None},
    "000016": {"name": "上证50", "etf": None},
    "HSTECH": {"name": "恒生科技", "etf": "513130"},
    "399967": {"name": "中证军工", "etf": None},
    "000941": {"name": "新能源", "etf": None},
    "000991": {"name": "全指医药", "etf": "159992"},
    "931079": {"name": "半导体", "etf": "159995"},
    "000922": {"name": "中证红利", "etf": "512890"},
}


def _load_cache() -> Optional[Dict]:
    if not CACHE_PATH.exists():
        return None
    try:
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        age = time.time() - data.get("_ts", 0)
        if age > CACHE_TTL_HOURS * 3600:
            return None  # expired
        return data
    except Exception:
        return None


def _save_cache(data: Dict):
    data["_ts"] = time.time()
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def fetch_index_valuations(force: bool = False) -> Dict[str, Dict]:
    """Fetch PE/PB for major A-share indices from East Money.

    Returns dict like {"000300": {"pe_ttm": 14.6, "pb": 1.46, "date": "2026-05-05"}}
    """
    # Check cache first
    if not force:
        cached = _load_cache()
        if cached:
            return {k: v for k, v in cached.items() if not k.startswith("_")}

    url = "https://push2.eastmoney.com/api/qt/ulist.np/get"
    codes = list(INDEX_MAP.keys())
    # A-share indices use 1. prefix, HSTECH is 100.
    secids = [f"1.{c}" if c != "HSTECH" else "100.HSTECH" for c in codes]

    params = {
        "fltt": "2",
        "invt": "2",
        "fields": "f2,f3,f4,f9,f12,f14,f20,f21,f23",
        "secids": ",".join(secids),
    }
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    try:
        resp = requests.get(url, params=params, headers=headers, timeout=15)
        data = resp.json()
    except Exception:
        return _load_cache() or {}

    results = {}
    if data.get("data") and data["data"].get("diff"):
        for item in data["data"]["diff"]:
            code = str(item.get("f12", ""))
            if code in INDEX_MAP:
                try:
                    pe = float(item.get("f9", -1)) if item.get("f9", "-") != "-" else -1
                except (ValueError, TypeError):
                    pe = -1
                try:
                    pb = float(item.get("f23", -1)) if item.get("f23", "-") != "-" else -1
                except (ValueError, TypeError):
                    pb = -1
                try:
                    price = float(item.get("f2", -1)) if item.get("f2", "-") != "-" else -1
                except (ValueError, TypeError):
                    price = -1

                results[code] = {
                    "name": INDEX_MAP[code]["name"],
                    "etf_code": INDEX_MAP[code]["etf"],
                    "pe_ttm": pe if pe > 0 else None,
                    "pb": pb if pb > 0 else None,
                    "price": price if price > 0 else None,
                    "date": datetime.now().strftime("%Y-%m-%d"),
                }

    if results:
        _save_cache(results)
    return results


def apply_valuations_to_candidates(candidates: Dict, valuations: Dict[str, Dict]) -> Dict:
    """Merge live index valuations into the ETF candidate data.

    Maps index PE/PB → ETF candidates where possible.
    Returns an updated candidates dict (does not mutate the original).
    """
    updated = {}
    for code, info in candidates.items():
        info = dict(info)  # shallow copy
        # Find matching index valuation
        for idx_code, val in valuations.items():
            if val.get("etf_code") == code and val.get("pe_ttm") is not None:
                info["pe_ttm"] = val["pe_ttm"]
                info["pb"] = val["pb"]
                # Recalculate E/P from real PE
                if val["pe_ttm"] and val["pe_ttm"] > 0:
                    info["ep_ratio"] = round(1.0 / val["pe_ttm"], 4)
                # Estimate percentiles (conservative default to 0.50)
                if info.get("pe_percentile") is None:
                    info["pe_percentile"] = 0.50
                if info.get("pb_percentile") is None:
                    info["pb_percentile"] = 0.50
                break
        updated[code] = info
    return updated
