#!/usr/bin/env python3
"""
Investment Monitor - 轻量版投资组合监控与信号生成系统

功能：
1. 拉取持仓标的实时行情（东方财富API）
2. 读取本地历史缓存，计算价格分位（2年）
3. 检查阈值触发条件，生成买卖信号
4. 检查仓位偏离度，生成再平衡信号
5. 输出每日信号报告（Markdown）

数据源：
- A股ETF实时：东方财富 push2 API
- 历史数据：本地 CSV 缓存（data/history/），支持 akshare 补充导入

使用：
    python scripts/investment_monitor.py

历史数据初始化（网络正常时）：
    python scripts/investment_monitor.py --init-history

作者：Claude Code
日期：2026-04-27
"""

import argparse
import json
import random
import time
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import requests

# ---------------------------------------------------------------------------
# 路径配置
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
HISTORY_DIR = DATA_DIR / "history"
CONFIG_PATH = DATA_DIR / "portfolio_config.json"
SIGNALS_DIR = DATA_DIR / "signals"

HISTORY_DIR.mkdir(parents=True, exist_ok=True)
SIGNALS_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# 标的默认配置
# ---------------------------------------------------------------------------

DEFAULT_HOLDINGS = [
    # 宽基底仓
    {"code": "510300", "name": "沪深300ETF", "target_pct": 11.1, "type": "a_etf",
     "rules": [{"kind": "price_percentile", "window": 500, "low": 0.20, "high": 0.80}]},
    {"code": "560610", "name": "中证A500ETF", "target_pct": 11.1, "type": "a_etf",
     "rules": [{"kind": "price_percentile", "window": 500, "low": 0.20, "high": 0.80}]},
    {"code": "513130", "name": "恒生科技ETF", "target_pct": 11.1, "type": "a_etf",
     "rules": [{"kind": "price_percentile", "window": 500, "low": 0.20, "high": 0.80}]},
    # 核心进攻
    {"code": "159857", "name": "光伏ETF", "target_pct": 8.9, "type": "a_etf",
     "rules": [{"kind": "price_percentile", "window": 500, "low": 0.15, "high": 0.85}]},
    {"code": "159755", "name": "电池ETF", "target_pct": 6.7, "type": "a_etf",
     "rules": [{"kind": "price_percentile", "window": 500, "low": 0.15, "high": 0.85}]},
    {"code": "159992", "name": "创新药ETF", "target_pct": 8.9, "type": "a_etf",
     "rules": [{"kind": "price_threshold", "low": 0.80, "high": 1.50}]},
    {"code": "159898", "name": "医疗器械ETF", "target_pct": 5.6, "type": "a_etf",
     "rules": [{"kind": "price_percentile", "window": 500, "low": 0.20, "high": 0.80}]},
    {"code": "562500", "name": "机器人ETF", "target_pct": 5.6, "type": "a_etf",
     "rules": [{"kind": "price_percentile", "window": 500, "low": 0.20, "high": 0.80}]},
    {"code": "159611", "name": "电力ETF", "target_pct": 4.4, "type": "a_etf",
     "rules": [{"kind": "price_percentile", "window": 500, "low": 0.20, "high": 0.80}]},
    {"code": "159995", "name": "芯片ETF", "target_pct": 4.4, "type": "a_etf",
     "rules": [{"kind": "price_percentile", "window": 500, "low": 0.20, "high": 0.80}]},
    # 卫星配置
    {"code": "512890", "name": "红利低波ETF", "target_pct": 8.9, "type": "a_etf",
     "rules": [{"kind": "price_percentile", "window": 500, "low": 0.20, "high": 0.80}]},
    {"code": "512800", "name": "银行ETF", "target_pct": 5.6, "type": "a_etf",
     "rules": [{"kind": "price_percentile", "window": 500, "low": 0.15, "high": 0.80}]},
    {"code": "518880", "name": "黄金ETF", "target_pct": 4.4, "type": "a_etf",
     "rules": [{"kind": "price_percentile", "window": 500, "low": 0.20, "high": 0.80}]},
    {"code": "512880", "name": "证券ETF", "target_pct": 3.3, "type": "a_etf",
     "rules": [{"kind": "price_percentile", "window": 500, "low": 0.15, "high": 0.80}]},
]

PORTFOLIO_RULES = {
    "rebalance_threshold": 0.10,
    "take_profit_pct": 0.50,
    "class_rebalance": 0.05,
}

# 东方财富市场前缀映射
EM_SECID_MAP = {
    "510300": "1.510300", "560610": "1.560610", "513130": "1.513130",
    "159857": "0.159857", "159755": "0.159755", "159992": "0.159992",
    "159898": "0.159898", "562500": "1.562500", "159611": "0.159611",
    "159995": "0.159995", "512890": "1.512890", "512800": "1.512800",
    "518880": "1.518880", "512880": "1.512880",
}

# ---------------------------------------------------------------------------
# 数据获取：实时行情
# ---------------------------------------------------------------------------

def get_eastmoney_realtime(codes: list[str]) -> dict[str, dict]:
    """通过东方财富API获取ETF实时行情"""
    secids = []
    for c in codes:
        sid = EM_SECID_MAP.get(c)
        if sid:
            secids.append(sid)
        else:
            # 默认上海市场
            secids.append(f"1.{c}")

    url = "https://push2.eastmoney.com/api/qt/ulist.np/get"
    params = {
        "fltt": "2",
        "invt": "2",
        "fields": "f2,f3,f4,f12,f14,f18,f20,f21",
        "secids": ",".join(secids),
    }
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    try:
        resp = requests.get(url, params=params, headers=headers, timeout=30)
        data = resp.json()
    except Exception as e:
        print(f"  [WARN] East Money API failed: {e}")
        return {}

    results = {}
    if not (data.get("data") and data["data"].get("diff")):
        print(f"  [WARN] East Money returned no data")
        return results

    for item in data["data"]["diff"]:
        code = str(item.get("f12", ""))
        name = item.get("f14", "")
        # f2=最新价, f3=涨跌幅(%), f4=涨跌额, f18=昨收
        price = item.get("f2", 0)
        change_pct = item.get("f3", 0)
        change_amt = item.get("f4", 0)
        prev_close = item.get("f18", 0)

        # 处理可能返回的 "-" 字符串
        try:
            price = float(price) if price != "-" else 0.0
        except (ValueError, TypeError):
            price = 0.0
        try:
            change_pct = float(change_pct) if change_pct != "-" else 0.0
        except (ValueError, TypeError):
            change_pct = 0.0
        try:
            prev_close = float(prev_close) if prev_close != "-" else 0.0
        except (ValueError, TypeError):
            prev_close = 0.0

        results[code] = {
            "code": code,
            "name": name,
            "current": price,
            "prev_close": prev_close,
            "change_pct": change_pct / 100.0 if change_pct else 0.0,
            "change_amt": change_amt,
        }

    return results


# ---------------------------------------------------------------------------
# 数据获取：历史数据（本地缓存 + akshare补充）
# ---------------------------------------------------------------------------

def get_history_path(code: str) -> Path:
    return HISTORY_DIR / f"{code}_history.csv"


def load_history_cache(code: str) -> pd.DataFrame:
    """从本地CSV加载历史数据"""
    path = get_history_path(code)
    if not path.exists():
        return pd.DataFrame()
    try:
        df = pd.read_csv(path)
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"])
            df = df.sort_values("date").reset_index(drop=True)
        return df
    except Exception as e:
        print(f"  [WARN] Failed to load history for {code}: {e}")
        return pd.DataFrame()


def save_history_cache(code: str, df: pd.DataFrame):
    """保存历史数据到本地CSV"""
    path = get_history_path(code)
    df.to_csv(path, index=False)


def update_history_with_today(code: str, price: float, date_str: str = None):
    """将今日价格追加到历史缓存"""
    if date_str is None:
        date_str = datetime.now().strftime("%Y-%m-%d")

    df = load_history_cache(code)
    if df.empty:
        # 创建新记录
        df = pd.DataFrame([{"date": date_str, "close": price}])
    else:
        # 检查是否已有今日记录
        if "date" in df.columns:
            today = pd.to_datetime(date_str)
            if pd.to_datetime(df["date"].iloc[-1]).date() == today.date():
                # 更新今日记录
                df.loc[df.index[-1], "close"] = price
            else:
                # 追加新记录
                new_row = pd.DataFrame([{"date": date_str, "close": price}])
                df = pd.concat([df, new_row], ignore_index=True)
        else:
            new_row = pd.DataFrame([{"date": date_str, "close": price}])
            df = pd.concat([df, new_row], ignore_index=True)

    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)
    save_history_cache(code, df)
    return df


def fetch_history_akshare(code: str, days: int = 500) -> pd.DataFrame:
    """尝试用 akshare 获取历史数据，失败则返回空DataFrame"""
    try:
        import akshare as ak
    except ImportError:
        return pd.DataFrame()

    end_date = datetime.now()
    start_date = end_date - timedelta(days=days + 90)

    try:
        # 短暂延迟避免反爬
        time.sleep(random.uniform(0.3, 1.0))
        df = ak.fund_etf_hist_em(
            symbol=code,
            period="daily",
            start_date=start_date.strftime("%Y%m%d"),
            end_date=end_date.strftime("%Y%m%d"),
            adjust="qfq",
        )
        if df is None or df.empty:
            return pd.DataFrame()

        # 统一列名
        col_map = {}
        for c in df.columns:
            if "日期" in c:
                col_map[c] = "date"
            elif "收盘" in c or "最新价" in c:
                col_map[c] = "close"
        if col_map:
            df = df.rename(columns=col_map)
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"])
            df = df.sort_values("date").reset_index(drop=True)
        return df[["date", "close"]]
    except Exception:
        return pd.DataFrame()


def init_all_history(holdings: list[dict], force: bool = False):
    """初始化所有标的的历史数据（从akshare获取）"""
    print("正在初始化历史数据缓存...")
    for h in holdings:
        code = h["code"]
        path = get_history_path(code)
        if path.exists() and not force:
            df = load_history_cache(code)
            print(f"  {code} {h['name']}: 已缓存 {len(df)} 条，跳过")
            continue

        print(f"  {code} {h['name']}: 正在获取...", end=" ")
        df = fetch_history_akshare(code, days=500)
        if not df.empty:
            save_history_cache(code, df)
            print(f"OK ({len(df)}条)")
        else:
            print("失败")


# ---------------------------------------------------------------------------
# 信号计算
# ---------------------------------------------------------------------------

def calc_price_percentile(df: pd.DataFrame, window: int = 500) -> float:
    if df.empty or "close" not in df.columns or len(df) < 60:
        return -1.0
    recent = df.tail(window)
    if len(recent) < 60:
        return -1.0
    current = recent["close"].iloc[-1]
    low = recent["close"].min()
    high = recent["close"].max()
    if high <= low:
        return 0.5
    return (current - low) / (high - low)


def calc_ep_proxy(current_price: float, history: pd.DataFrame) -> float:
    """
    计算盈利收益率(E/P)代理值。
    使用价格分位反向映射：价格低位->高E/P（低估），价格高位->低E/P（高估）。
    基础E/P=7.5%（宽基历史中位数PE≈13.3）。
    """
    if history.empty or "close" not in history.columns or len(history) < 60:
        return 0.075
    prices = history["close"]
    median_price = prices.median()
    if median_price <= 0 or current_price <= 0:
        return 0.075
    base_ep = 0.075
    ep = base_ep * (median_price / current_price)
    return max(0.02, min(0.20, ep))


def check_four_percent_signal(holding: dict, realtime: dict, history: pd.DataFrame,
                               positions: dict = None) -> list[dict]:
    """
    检查4%定投法触发信号（修正版，匹配雷牛牛强化版理论）

    原版核心规则：
    - 总资金分25份，单标的上限10份
    - 触发基准：从"上一个买入点"下跌4%（非"2年最低点"）
    - 估值过滤：E/P > 10%才启动，E/P < 6.4%卖出
    - 等待纪律：未跌穿4%绝不提前买入
    """
    signals = []
    code = holding["code"]
    name = holding["name"]
    current_price = realtime.get("current", 0)

    if history.empty or "close" not in history.columns or len(history) < 60:
        return signals

    # 计算E/P代理值
    ep = calc_ep_proxy(current_price, history)

    # E/P状态判断（格雷厄姆标准）
    if ep >= 0.10:
        ep_status = "低估（可买）"
        ep_color = "**"
    elif ep >= 0.064:
        ep_status = "合理"
        ep_color = ""
    else:
        ep_status = "高估（应卖）"
        ep_color = "**"

    # 价格分位（辅助参考）
    pctl = calc_price_percentile(history, 500)

    # 获取持仓信息（如果有）
    pos = positions.get(code, {}) if positions else {}
    shares = pos.get("shares", 0)
    cost = pos.get("cost", 0)
    last_buy = pos.get("last_buy_price", 0)

    if shares > 0 and last_buy > 0:
        # ---------- 有持仓 ----------
        # 检查卖出条件
        if ep < 0.064:
            signals.append({
                "code": code, "name": name, "type": "4%定投-卖出",
                "reason": f"E/P {ep:.1%} < 6.4%（高估线），建议全部卖出 | 上次买入价 {last_buy:.3f}",
                "price": current_price,
                "metric": f"E/P {ep:.1%}",
                "priority": 1,
            })
        else:
            # 检查买入触发：从上一个买入点下跌4%
            trigger_price = last_buy * 0.96
            drop_pct = (current_price - last_buy) / last_buy
            if current_price <= trigger_price:
                if ep >= 0.10:
                    signals.append({
                        "code": code, "name": name, "type": "4%定投-买入",
                        "reason": f"从上次买入价{last_buy:.3f}下跌{abs(drop_pct):.1%}≥4%，触发买入 | E/P {ep:.1%} 达标",
                        "price": current_price,
                        "metric": f"距上次买入跌幅 {drop_pct:+.1%}",
                        "priority": 1,
                    })
                else:
                    signals.append({
                        "code": code, "name": name, "type": "4%定投-等待",
                        "reason": f"价格已触发（跌{abs(drop_pct):.1%}），但E/P {ep:.1%} < 10%未达标",
                        "price": current_price,
                        "metric": f"距上次买入 {drop_pct:+.1%}",
                        "priority": 3,
                    })
            else:
                # 未触发，显示等待信息
                to_trigger = (trigger_price - current_price) / current_price if current_price > 0 else 0
                signals.append({
                    "code": code, "name": name, "type": "4%定投-等待",
                    "reason": f"持仓等待：上次买入{last_buy:.3f}，触发线{trigger_price:.3f}，还需跌{to_trigger:.1%} | E/P {ep:.1%} {ep_status}",
                    "price": current_price,
                    "metric": f"距触发线 {to_trigger:+.1%}",
                    "priority": 3,
                })
    else:
        # ---------- 空仓 ----------
        if ep >= 0.10:
            # 可以开始观察，设定当前价为观察基准
            # 需要等待从当前价下跌4%才买入
            trigger_price = current_price * 0.96
            signals.append({
                "code": code, "name": name, "type": "4%定投-观察",
                "reason": f"E/P {ep:.1%} 达标，可开始观察。设定观察价{current_price:.3f}，等待跌到{trigger_price:.3f}（-4%）买入",
                "price": current_price,
                "metric": f"E/P {ep:.1%} {ep_status}",
                "priority": 2,
            })
        else:
            signals.append({
                "code": code, "name": name, "type": "4%定投-观望",
                "reason": f"E/P {ep:.1%} < 10%，估值偏高，暂不宜开始定投",
                "price": current_price,
                "metric": f"E/P {ep:.1%} {ep_status}",
                "priority": 3,
            })

    return signals


def check_rules(holding: dict, realtime: dict, history: pd.DataFrame) -> list[dict]:
    signals = []
    code = holding["code"]
    name = holding["name"]
    current_price = realtime.get("current", 0)

    # 4%定投法信号
    signals.extend(check_four_percent_signal(holding, realtime, history))

    for rule in holding.get("rules", []):
        kind = rule["kind"]

        if kind == "price_percentile":
            window = rule.get("window", 500)
            low_thresh = rule.get("low", 0.20)
            high_thresh = rule.get("high", 0.80)
            pctl = calc_price_percentile(history, window)
            if pctl < 0:
                continue
            if pctl <= low_thresh:
                signals.append({
                    "code": code, "name": name, "type": "加仓",
                    "reason": f"2年价格分位 {pctl:.1%} <= {low_thresh:.0%}，低估",
                    "price": current_price, "metric": f"分位 {pctl:.1%}",
                    "priority": 1 if pctl <= 0.10 else 2,
                })
            elif pctl >= high_thresh:
                signals.append({
                    "code": code, "name": name, "type": "减仓",
                    "reason": f"2年价格分位 {pctl:.1%} >= {high_thresh:.0%}，高估",
                    "price": current_price, "metric": f"分位 {pctl:.1%}",
                    "priority": 2,
                })

        elif kind == "price_threshold":
            low_price = rule.get("low", 0)
            high_price = rule.get("high", 999)
            if current_price > 0 and current_price <= low_price:
                signals.append({
                    "code": code, "name": name, "type": "加仓",
                    "reason": f"净值 {current_price:.3f} <= 阈值 {low_price:.2f}",
                    "price": current_price, "metric": f"净值 {current_price:.3f}",
                    "priority": 1,
                })
            elif current_price >= high_price:
                signals.append({
                    "code": code, "name": name, "type": "减仓",
                    "reason": f"净值 {current_price:.3f} >= 阈值 {high_price:.2f}",
                    "price": current_price, "metric": f"净值 {current_price:.3f}",
                    "priority": 2,
                })

    return signals


def check_portfolio_signals(holdings: list[dict], realtime_map: dict, config: dict) -> list[dict]:
    signals = []
    total_value = 0.0
    positions = config.get("positions", {})

    for h in holdings:
        code = h["code"]
        rt = realtime_map.get(code, {})
        pos = positions.get(code, {})
        shares = pos.get("shares", 0)
        price = rt.get("current", 0)
        total_value += shares * price

    if total_value <= 0:
        return signals

    for h in holdings:
        code = h["code"]
        name = h["name"]
        target_pct = h["target_pct"] / 100.0
        rt = realtime_map.get(code, {})
        pos = positions.get(code, {})
        shares = pos.get("shares", 0)
        cost = pos.get("cost", 0)
        price = rt.get("current", 0)
        value = shares * price
        actual_pct = value / total_value if total_value else 0

        # 止盈
        if cost > 0 and price > 0:
            gain_pct = (price - cost) / cost
            if gain_pct >= PORTFOLIO_RULES["take_profit_pct"]:
                signals.append({
                    "code": code, "name": name, "type": "止盈",
                    "reason": f"浮盈 {gain_pct:.1%} >= 50%",
                    "price": price, "metric": f"浮盈 {gain_pct:.1%}",
                    "priority": 1,
                })

        # 偏离度
        deviation = abs(actual_pct - target_pct)
        if deviation >= PORTFOLIO_RULES["rebalance_threshold"]:
            direction = "加仓" if actual_pct < target_pct else "减仓"
            signals.append({
                "code": code, "name": name, "type": direction,
                "reason": f"偏离 {deviation:.1%}（目标 {target_pct:.1%}，实际 {actual_pct:.1%}）",
                "price": price, "metric": f"偏离 {deviation:.1%}",
                "priority": 3,
            })

    return signals


# ---------------------------------------------------------------------------
# 配置管理
# ---------------------------------------------------------------------------

def load_or_init_config() -> dict:
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)

    config = {
        "total_capital": 900000,
        "holdings": DEFAULT_HOLDINGS,
        "positions": {},
        "created_at": datetime.now().isoformat(),
    }
    save_config(config)
    return config


def save_config(config: dict):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# 宏观周期信息（安全导入，失败则显示简化版）
# ---------------------------------------------------------------------------

def get_macro_summary() -> dict:
    """获取宏观周期摘要信息"""
    result = {
        "kondratiev_phase": "复苏期",
        "kondratiev_name": "第六轮康波（AI与新能源）",
        "juglar_phase": "复苏期",
        "kitchin_phase": "补库存",
        "resonance": "中共振偏强",
        "position": "50-70%",
        "year": 2026,
        "available": False,
    }
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from cycle_phase_evaluator import CyclePhaseEvaluator
        evaluator = CyclePhaseEvaluator()
        phases, resonance = evaluator.evaluate_all(2026)
        result["available"] = True
        result["resonance"] = resonance.resonance_strength
        result["position"] = f"{resonance.position_range[0]:.0%}-{resonance.position_range[1]:.0%}"
        for p in phases:
            if p.cycle_type == "kondratiev":
                result["kondratiev_phase"] = p.current_phase
            elif p.cycle_type == "juglar":
                result["juglar_phase"] = p.current_phase
            elif p.cycle_type == "kitchin":
                result["kitchin_phase"] = p.current_phase
    except Exception:
        pass
    return result


# ---------------------------------------------------------------------------
# 报告生成
# ---------------------------------------------------------------------------

def generate_report(holdings, realtime_map, history_map, signals, config) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    macro = get_macro_summary()

    lines = [
        f"# 投资组合监控日报 ({now})",
        "",
        "## 一、宏观周期定位",
        "",
        "| 周期 | 当前阶段 | 投资含义 |",
        "|------|----------|----------|",
        f"| 康波（50-60年） | {macro['kondratiev_phase']} | {macro['kondratiev_name']} |",
        f"| 朱格拉（8-10年） | {macro['juglar_phase']} | 设备投资周期 |",
        f"| 基钦（3-4年） | {macro['kitchin_phase']} | 库存周期 |",
        "",
        f"**共振判断**: {macro['resonance']} | **建议仓位**: {macro['position']}",
        "",
        "---",
        "",
        "## 二、今日信号摘要",
        "",
    ]

    urgent = [s for s in signals if s["priority"] == 1]
    normal = [s for s in signals if s["priority"] == 2]
    info_sig = [s for s in signals if s["priority"] == 3]

    if urgent:
        lines.append("### 紧急信号（立即关注）")
        lines.append("")
        for s in urgent:
            lines.append(f"- **{s['type']}** | `{s['code']}` {s['name']} @ {s['price']:.3f}")
            lines.append(f"  - {s['reason']} ({s['metric']})")
        lines.append("")

    if normal:
        lines.append("### 关注信号（近期操作）")
        lines.append("")
        for s in normal:
            lines.append(f"- **{s['type']}** | `{s['code']}` {s['name']} @ {s['price']:.3f}")
            lines.append(f"  - {s['reason']} ({s['metric']})")
        lines.append("")

    if info_sig:
        lines.append("### 提示信号（跟踪观察）")
        lines.append("")
        for s in info_sig:
            lines.append(f"- **{s['type']}** | `{s['code']}` {s['name']} @ {s['price']:.3f}")
            lines.append(f"  - {s['reason']} ({s['metric']})")
        lines.append("")

    if not signals:
        lines.append("今日无触发信号，继续定投计划。")
        lines.append("")

    # 持仓概览
    lines.append("## 三、持仓概览")
    lines.append("")
    lines.append("| 标的 | 代码 | 现价 | 涨跌 | 目标仓位 | 实际仓位 | 浮盈 | 信号 |")
    lines.append("|------|------|------|------|----------|----------|------|------|")

    total_value = 0.0
    positions = config.get("positions", {})
    for h in holdings:
        rt = realtime_map.get(h["code"], {})
        pos = positions.get(h["code"], {})
        total_value += pos.get("shares", 0) * rt.get("current", 0)

    for h in holdings:
        code = h["code"]
        name = h["name"]
        rt = realtime_map.get(code, {})
        pos = positions.get(code, {})
        price = rt.get("current", 0)
        change = rt.get("change_pct", 0)
        shares = pos.get("shares", 0)
        cost = pos.get("cost", 0)
        value = shares * price
        target = h["target_pct"]
        actual = (value / total_value * 100) if total_value else 0
        gain = ((price - cost) / cost * 100) if cost > 0 else 0
        sigs = ", ".join(s["type"] for s in signals if s["code"] == code) or "无"
        lines.append(f"| {name} | {code} | {price:.3f} | {change:+.2%} | {target:.1f}% | {actual:.1f}% | {gain:+.1f}% | {sigs} |")

    lines.append("")

    # 估值分位
    lines.append("## 四、估值分位详情（2年）")
    lines.append("")
    lines.append("| 标的 | 代码 | 现价 | 2年最低 | 2年最高 | 分位 | 判断 |")
    lines.append("|------|------|------|---------|---------|------|------|")

    for h in holdings:
        code = h["code"]
        name = h["name"]
        rt = realtime_map.get(code, {})
        hist = history_map.get(code, pd.DataFrame())
        price = rt.get("current", 0)

        if not hist.empty and "close" in hist.columns:
            recent = hist.tail(500)
            low = recent["close"].min()
            high = recent["close"].max()
            pctl = calc_price_percentile(hist, 500)
            if pctl < 0:
                pctl_str = "-"
                judgment = "数据不足"
            elif pctl <= 0.15:
                judgment = "**极度低估**"
            elif pctl <= 0.30:
                judgment = "低估"
            elif pctl >= 0.85:
                judgment = "高估"
            elif pctl >= 0.70:
                judgment = "偏高"
            else:
                judgment = "合理"
                lines.append(f"| {name} | {code} | {price:.3f} | {low:.3f} | {high:.3f} | {pctl_str} | {judgment} |")
        else:
            lines.append(f"| {name} | {code} | {price:.3f} | - | - | - | 暂无数据 |")

    lines.append("")

    # 4%定投法策略板块（修正版，匹配雷牛牛强化版理论）
    lines.append("## 五、4%定投法策略建议")
    lines.append("")
    lines.append("基于B站UP主'研究员雷牛牛'提出的4%定投法**强化版**理论：")
    lines.append("")
    lines.append("| 标的 | 代码 | 现价 | E/P代理 | 估值判断 | 单标上限 | 总份数 | 状态 | 建议 |")
    lines.append("|------|------|------|---------|----------|----------|--------|------|------|")

    for h in holdings:
        code = h["code"]
        name = h["name"]
        rt = realtime_map.get(code, {})
        hist = history_map.get(code, pd.DataFrame())
        price = rt.get("current", 0)

        pos = positions.get(code, {})
        shares = pos.get("shares", 0)

        if not hist.empty and "close" in hist.columns:
            ep = calc_ep_proxy(price, hist)
            if ep >= 0.10:
                ep_status = "**低估（可买）**"
            elif ep >= 0.064:
                ep_status = "合理"
            else:
                ep_status = "**高估（应卖）**"

            # 持仓状态下的触发判断
            if shares > 0:
                last_buy = pos.get("last_buy_price", 0)
                if last_buy > 0:
                    trigger_price = last_buy * 0.96
                    if price <= trigger_price and ep >= 0.10:
                        status = "**触发买入**"
                        advice = f"从上次买入{last_buy:.3f}下跌≥4%，买入1份"
                    elif price <= trigger_price:
                        status = "触发但E/P未达标"
                        advice = f"价格触发，但E/P {ep:.1%}<10%"
                    else:
                        status = "持仓等待"
                        advice = f"上次买入{last_buy:.3f}，触发线{trigger_price:.3f}"
                else:
                    status = "持仓（无买入记录）"
                    advice = "请补充last_buy_price"
            else:
                if ep >= 0.10:
                    status = "可开始观察"
                    advice = f"设定观察价{price:.3f}，等跌4%买入"
                else:
                    status = "观望"
                    advice = f"E/P {ep:.1%}<10%，暂不宜入场"
        else:
            ep = 0
            ep_status = "数据不足"
            status = "-"
            advice = "-"

        lines.append(f"| {name} | {code} | {price:.3f} | {ep:.1%} | {ep_status} | 10份 | 25份 | {status} | {advice} |")

    lines.append("")
    lines.append("**原版核心规则**：")
    lines.append("1. **份数**：总资金分25份，单只标的上限10份（40%）")
    lines.append("2. **触发基准**：从'上一个买入点'下跌4%（非2年低点）— 反弹后需更大跌幅才能再触发")
    lines.append("3. **估值过滤**：E/P>10%才启动（格雷厄姆低估线），E/P<6.4%卖出（高估线）")
    lines.append("4. **等待纪律**：未跌穿4%绝不提前买入，只买跌不买涨")
    lines.append("5. **价格阶梯**：第n次买入价 = 第(n-1)次 × 0.96")
    lines.append("")
    lines.append("**适用场景**：")
    lines.append("- **震荡市/下跌市**：4%法表现最好，越跌越买摊薄成本")
    lines.append("- **单边上涨市**：容易踏空，大量现金闲置，可能跑输普通定投")
    lines.append("- **宽基指数**：成立>7年、回撤可控的ETF最佳")
    lines.append("")

    # 本月定投计划
    lines.append("## 六、本月定投计划")
    lines.append("")
    lines.append("根据90万18个月定投方案，本月应投入 **5万元**：")
    lines.append("")
    lines.append("| 标的 | 代码 | 常规金额 | 信号调整 | 建议金额 |")
    lines.append("|------|------|----------|----------|----------|")

    base_amounts = {
        "510300": 5500, "560610": 5500, "513130": 5500,
        "159857": 4500, "159992": 4500, "159755": 3000,
        "159898": 2500, "562500": 2500, "159611": 2500, "159995": 3000,
        "512890": 4500, "512800": 2500, "518880": 2000, "512880": 2000,
    }

    total_suggest = 0
    for h in holdings:
        code = h["code"]
        name = h["name"]
        base = base_amounts.get(code, 0)
        # 检查是否有4%触发信号或加仓信号
        fp_sigs = [s for s in signals if s["code"] == code and s["type"] in ("4%定投触发", "右侧补仓", "加仓")]
        adjust = "加倍 (+100%)" if fp_sigs else "常规"
        suggest = base * 2 if fp_sigs else base
        total_suggest += suggest
        lines.append(f"| {name} | {code} | {base:,} | {adjust} | **{suggest:,}** |")

    lines.append(f"| **合计** | | | | **{total_suggest:,}** |")
    lines.append("")

    # 数据状态说明
    no_history = [h["code"] for h in holdings if h["code"] not in history_map or history_map[h["code"]].empty]
    if no_history:
        lines.append("> **数据说明**：以下标的暂无历史缓存，估值分位无法计算。建议运行 `python scripts/investment_monitor.py --init-history` 初始化，或从券商APP导出历史净值CSV放入 `data/history/` 目录。")
        lines.append("> ")
        for c in no_history:
            h = next((x for x in holdings if x["code"] == c), None)
            if h:
                lines.append(f"> - {c} {h['name']}")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("*本报告基于历史数据自动生成，仅供投资参考，不构成具体投资建议。投资有风险，入市需谨慎。*")
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="投资组合监控")
    parser.add_argument("--init-history", action="store_true", help="初始化历史数据缓存（需akshare可用）")
    parser.add_argument("--force", action="store_true", help="强制重新获取历史数据")
    args = parser.parse_args()

    print("=" * 60)
    print("Investment Monitor - 投资组合监控")
    print(f"运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # 配置
    config = load_or_init_config()
    holdings = config.get("holdings", DEFAULT_HOLDINGS)
    print(f"\n[1/5] 已加载 {len(holdings)} 个标的")

    # 如果指定了初始化历史数据
    if args.init_history:
        init_all_history(holdings, force=args.force)
        print("\n历史数据初始化完成。")
        return

    # 实时行情
    print("\n[2/5] 获取实时行情...")
    a_codes = [h["code"] for h in holdings if h["type"] == "a_etf"]
    realtime_map = get_eastmoney_realtime(a_codes)
    print(f"  成功: {len(realtime_map)} / {len(a_codes)} 个标的")
    for code in a_codes:
        data = realtime_map.get(code)
        if data:
            print(f"    {code}: {data['current']:.3f} ({data['change_pct']:+.2%})")
        else:
            print(f"    {code}: 未获取")

    # 历史数据（本地缓存 + 更新今日价格）
    print("\n[3/5] 加载历史数据缓存...")
    history_map = {}
    for h in holdings:
        code = h["code"]
        # 先加载缓存
        df = load_history_cache(code)
        # 如果有实时价格，追加今日数据
        rt = realtime_map.get(code, {})
        price = rt.get("current", 0)
        if price > 0:
            df = update_history_with_today(code, price)
        if not df.empty:
            history_map[code] = df
            pctl = calc_price_percentile(df, 500)
            pctl_str = f"{pctl:.1%}" if pctl >= 0 else "N/A"
            print(f"    {code}: 缓存 {len(df)} 条, 分位 {pctl_str}")
        else:
            print(f"    {code}: 暂无历史数据")

    # 信号
    print("\n[4/5] 检查阈值信号...")
    all_signals = []
    for h in holdings:
        code = h["code"]
        rt = realtime_map.get(code, {})
        hist = history_map.get(code, pd.DataFrame())
        all_signals.extend(check_rules(h, rt, hist))
    all_signals.extend(check_portfolio_signals(holdings, realtime_map, config))

    # 去重排序
    seen = set()
    unique_signals = []
    for s in sorted(all_signals, key=lambda x: x["priority"]):
        key = (s["code"], s["type"], s["reason"])
        if key not in seen:
            seen.add(key)
            unique_signals.append(s)

    print(f"  共 {len(unique_signals)} 条信号:")
    for s in unique_signals:
        icon = "!!" if s["priority"] == 1 else ("! " if s["priority"] == 2 else "  ")
        print(f"    [{icon}] {s['type']:2s} {s['code']} {s['name']}: {s['reason']}")

    # 报告
    print("\n[5/5] 生成报告...")
    report = generate_report(holdings, realtime_map, history_map, unique_signals, config)
    report_path = SIGNALS_DIR / f"signal_report_{datetime.now().strftime('%Y%m%d')}.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"  已保存: {report_path}")

    # 输出预览
    print("\n" + "=" * 60)
    print("报告预览（前2500字符）:")
    print("=" * 60)
    print(report[:2500])
    if len(report) > 2500:
        print(f"\n... 完整报告共 {len(report)} 字符")

    return report_path


if __name__ == "__main__":
    main()
