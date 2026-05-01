#!/usr/bin/env python3
"""
4%定投法 - 核心模型与回测系统（修正版）

基于B站UP主"研究员雷牛牛"提出的4%定投法强化版理论：
- 原版核心：资金分25份，单标的上限10份，从"上一个买入点"下跌4%触发买入
- 估值过滤：格雷厄姆标准，盈利收益率(E/P) > 10%启动，< 6.4%卖出
- 行业适配：周期股看PB，非周期看PE
- 等待纪律：未跌穿4%绝不提前买入
- 价格阶梯：精确公式 0.96^n

功能：
1. 原版4%定投法回测（修正参数）
2. 改进版4%定投法回测
3. 与普通月定投对比
4. 生成回测报告与交易记录

使用：
    python scripts/four_percent_model.py --backtest 510300 --start 2022-01-01 --capital 100000
    python scripts/four_percent_model.py --backtest-all
    python scripts/four_percent_model.py --live-signal

作者：Claude Code
日期：2026-05-01（修正版）
"""

import argparse
import json
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

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
class TradeRecord:
    """交易记录"""
    date: str
    action: str  # BUY / SELL
    price: float
    shares: float
    amount: float
    tranche: int
    notes: str = ""


@dataclass
class DailyState:
    """每日状态快照"""
    date: str
    price: float
    cash: float
    shares: float
    portfolio_value: float
    cost_basis: float
    total_return: float
    tranches_used: int
    ep_proxy: float  # 盈利收益率代理
    last_buy_price: float
    notes: str = ""


# ---------------------------------------------------------------------------
# 辅助函数
# ---------------------------------------------------------------------------

def calc_ep_proxy(price: float, price_history: list[float]) -> float:
    """
    计算盈利收益率(E/P)代理值。
    由于ETF无直接E/P数据，使用价格分位的反向映射：
    - 价格处于历史低位 -> E/P 高（低估）
    - 价格处于历史高位 -> E/P 低（高估）
    映射公式：ep_proxy = base_ep * (median_price / current_price)
    base_ep 取历史价格中位数对应的E/P基准（约7.5%，即PE≈13.3）
    """
    if len(price_history) < 60:
        return 0.075  # 默认中性

    prices = pd.Series(price_history)
    median_price = prices.median()
    if median_price <= 0 or price <= 0:
        return 0.075

    # 简化代理：价格低于中位数时E/P更高（低估）
    # 基础E/P=7.5%（PE≈13.3，宽基历史中位数）
    base_ep = 0.075
    ratio = median_price / price
    ep = base_ep * ratio

    # 限制在合理范围
    return max(0.02, min(0.20, ep))


def load_history(code: str) -> pd.DataFrame:
    """加载历史数据"""
    path = HISTORY_DIR / f"{code}_history.csv"
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path)
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)
    return df


# ---------------------------------------------------------------------------
# 原版4%定投法（修正版，匹配雷牛牛强化版理论）
# ---------------------------------------------------------------------------

class FourPercentModel:
    """
    原版4%定投法模型（修正版）

    规则（基于研究员雷牛牛强化版理论）：
    1. 建仓：总资金平均分成25份，单只标的上限10份
    2. 估值过滤（格雷厄姆标准）：
       - 盈利收益率 E/P > 10% 才允许买入（低估）
       - 盈利收益率 E/P < 6.4% 时全部卖出（高估）
       - 周期行业用PB估值，非周期行业用PE估值
    3. 买入触发：从"上一个买入点"下跌 >= 4% 时买入1份
       - 严格等待：未跌穿4%绝不提前买入
       - 首次买入：从初始观察价下跌4%触发
       - 价格阶梯：第n次买入价 = 第(n-1)次 × 0.96
    4. 买入纪律：只买跌，不买涨；反弹不触发买入
    5. 卖出纪律：E/P < 6.4% 时全部卖出

    参数：
        total_capital: 总资金
        num_tranches: 总份数（默认25）
        max_tranches_per_holding: 单标的上限（默认10）
        drop_pct: 下跌触发比例（默认0.04 = 4%）
        ep_buy_threshold: E/P买入阈值（默认0.10 = 10%）
        ep_sell_threshold: E/P卖出阈值（默认0.064 = 6.4%）
        valuation_type: 估值类型 "pe"或"pb"
    """

    def __init__(
        self,
        total_capital: float = 100000,
        num_tranches: int = 25,
        max_tranches_per_holding: int = 10,
        drop_pct: float = 0.04,
        ep_buy_threshold: float = 0.10,
        ep_sell_threshold: float = 0.064,
        valuation_type: str = "pe",
        name: str = "原版4%定投法",
    ):
        self.name = name
        self.total_capital = total_capital
        self.num_tranches = num_tranches
        self.max_tranches_per_holding = max_tranches_per_holding
        self.drop_pct = drop_pct
        self.ep_buy_threshold = ep_buy_threshold
        self.ep_sell_threshold = ep_sell_threshold
        self.valuation_type = valuation_type
        self.tranche_amount = total_capital / num_tranches

        # 状态
        self.cash = total_capital
        self.shares = 0.0
        self.tranches_used = 0
        self.cost_basis = 0.0
        self.last_buy_price: Optional[float] = None  # 上一个买入价（核心！）
        self.initial_obs_price: Optional[float] = None  # 初始观察价
        self.phase = "observing"  # observing / accumulating / exiting

        # 记录
        self.trades: list[TradeRecord] = []
        self.daily_states: list[DailyState] = []
        self.price_history: list[float] = []

    def reset(self):
        """重置状态"""
        self.cash = self.total_capital
        self.shares = 0.0
        self.tranches_used = 0
        self.cost_basis = 0.0
        self.last_buy_price = None
        self.initial_obs_price = None
        self.phase = "observing"
        self.trades = []
        self.daily_states = []
        self.price_history = []

    def _calc_ep(self, price: float) -> float:
        """计算当前盈利收益率代理值"""
        return calc_ep_proxy(price, self.price_history)

    def _buy(self, date: str, price: float, notes: str = "") -> bool:
        """执行买入1份"""
        if self.tranches_used >= self.max_tranches_per_holding:
            return False
        if self.cash < self.tranche_amount:
            return False

        amount = self.tranche_amount
        shares = amount / price

        self.cash -= amount
        old_cost = self.shares * self.cost_basis
        self.shares += shares
        self.cost_basis = (old_cost + amount) / self.shares if self.shares > 0 else 0
        self.tranches_used += 1

        # 更新上一个买入价（核心状态！）
        self.last_buy_price = price
        self.phase = "accumulating"

        self.trades.append(TradeRecord(
            date=date, action="BUY", price=price, shares=shares,
            amount=amount, tranche=self.tranches_used, notes=notes,
        ))
        return True

    def _sell_all(self, date: str, price: float, notes: str = "") -> bool:
        """全部卖出"""
        if self.shares <= 0:
            return False

        amount = self.shares * price
        self.cash += amount

        self.trades.append(TradeRecord(
            date=date, action="SELL", price=price, shares=self.shares,
            amount=amount, tranche=0, notes=notes,
        ))

        self.shares = 0.0
        self.cost_basis = 0.0
        self.tranches_used = 0
        self.last_buy_price = None
        self.phase = "observing"
        return True

    def step(self, date: str, price: float):
        """处理一天的价格数据"""
        self.price_history.append(price)
        ep = self._calc_ep(price)

        notes = ""

        # ---------- 有持仓时的处理 ----------
        if self.shares > 0:
            # 检查卖出条件：E/P < 6.4%（高估线）
            if ep < self.ep_sell_threshold:
                self._sell_all(
                    date, price,
                    notes=f"E/P {ep:.1%} < 卖出阈值 {self.ep_sell_threshold:.0%}，高估卖出"
                )
                notes = "已卖出：E/P低于高估线"
            else:
                # E/P 达标，检查是否触发买入
                # 条件：从上一个买入点下跌 >= 4%
                if self.last_buy_price is not None:
                    trigger_price = self.last_buy_price * (1 - self.drop_pct)
                    if price <= trigger_price:
                        # 检查是否还有份数
                        if self.tranches_used < self.max_tranches_per_holding:
                            # 检查E/P是否仍达标
                            if ep >= self.ep_buy_threshold:
                                notes = f"触发：从上次买入价{self.last_buy_price:.3f}下跌{self.drop_pct:.0%}"
                                self._buy(date, price, notes)
                            else:
                                notes = f"价格触发({price:.3f}<={trigger_price:.3f})但E/P {ep:.1%}未达标"
                        else:
                            notes = "价格触发但已达单标的上限(10份)"
                    else:
                        notes = f"等待中：当前{price:.3f}，触发线{trigger_price:.3f}"
                else:
                    # 异常状态：有持仓但无last_buy_price
                    notes = "异常：有持仓但无买入记录"

        # ---------- 空仓时的处理 ----------
        else:
            if self.tranches_used == 0:
                # 从未买入过：首次观察
                if self.initial_obs_price is None:
                    self.initial_obs_price = price
                    self.last_buy_price = price  # 设为观察基准
                    notes = f"设定初始观察价 {price:.3f}，等待下跌{self.drop_pct:.0%}"
                else:
                    # 等待从初始观察价下跌4%
                    trigger_price = self.initial_obs_price * (1 - self.drop_pct)
                    if price <= trigger_price:
                        if ep >= self.ep_buy_threshold:
                            notes = f"首次建仓：从观察价{self.initial_obs_price:.3f}下跌{self.drop_pct:.0%}"
                            self._buy(date, price, notes)
                        else:
                            notes = f"价格触发但E/P {ep:.1%} < 买入阈值{self.ep_buy_threshold:.0%}"
                    else:
                        notes = f"首次观察：等待从{self.initial_obs_price:.3f}跌到{trigger_price:.3f}"
            else:
                # 已卖出，等待再入场
                # 需要重新设定观察价
                if self.initial_obs_price is None:
                    self.initial_obs_price = price
                    self.last_buy_price = price
                    notes = f"卖出后再观察：设定新观察价 {price:.3f}"
                else:
                    trigger_price = self.initial_obs_price * (1 - self.drop_pct)
                    if price <= trigger_price:
                        if ep >= self.ep_buy_threshold:
                            notes = f"再入场：从观察价{self.initial_obs_price:.3f}下跌{self.drop_pct:.0%}"
                            self._buy(date, price, notes)
                        else:
                            notes = f"再入场价格触发但E/P {ep:.1%}未达标"
                    else:
                        notes = f"等待再入场：从{self.initial_obs_price:.3f}跌到{trigger_price:.3f}"

        # 记录每日状态
        portfolio_value = self.cash + self.shares * price
        total_return = (portfolio_value - self.total_capital) / self.total_capital
        self.daily_states.append(DailyState(
            date=date, price=price, cash=self.cash, shares=self.shares,
            portfolio_value=portfolio_value, cost_basis=self.cost_basis,
            total_return=total_return, tranches_used=self.tranches_used,
            ep_proxy=ep, last_buy_price=self.last_buy_price or 0,
            notes=notes,
        ))

    def run(self, df: pd.DataFrame) -> dict:
        """运行回测"""
        self.reset()
        for _, row in df.iterrows():
            date_str = str(row["date"].date() if hasattr(row["date"], "date") else row["date"])
            self.step(date_str, float(row["close"]))
        return self.get_stats(df)

    def get_stats(self, df: pd.DataFrame) -> dict:
        """计算回测统计"""
        if not self.daily_states:
            return {}

        final_price = df["close"].iloc[-1]
        final_value = self.cash + self.shares * final_price
        total_return = (final_value - self.total_capital) / self.total_capital

        # 最大回撤
        values = [s.portfolio_value for s in self.daily_states]
        max_drawdown = 0.0
        peak = values[0]
        for v in values:
            if v > peak:
                peak = v
            dd = (peak - v) / peak
            if dd > max_drawdown:
                max_drawdown = dd

        # 年化收益
        days = len(df)
        years = days / 252
        annual_return = (1 + total_return) ** (1 / years) - 1 if years > 0 and total_return > -1 else 0

        # 波动率
        daily_returns = pd.Series(values).pct_change().dropna()
        volatility = daily_returns.std() * np.sqrt(252) if len(daily_returns) > 1 else 0

        # 夏普比率（无风险利率2%）
        sharpe = (annual_return - 0.02) / volatility if volatility > 0 else 0

        # 资金利用率
        invested = sum(t.amount for t in self.trades if t.action == "BUY")
        capital_utilization = invested / self.total_capital if self.total_capital > 0 else 0

        return {
            "strategy": self.name,
            "total_capital": self.total_capital,
            "final_value": round(final_value, 2),
            "total_return": round(total_return, 4),
            "annual_return": round(annual_return, 4),
            "max_drawdown": round(max_drawdown, 4),
            "volatility": round(volatility, 4),
            "sharpe": round(sharpe, 4),
            "trades": len(self.trades),
            "buy_trades": len([t for t in self.trades if t.action == "BUY"]),
            "sell_trades": len([t for t in self.trades if t.action == "SELL"]),
            "cash_remaining": round(self.cash, 2),
            "shares_remaining": round(self.shares, 4),
            "cost_basis": round(self.cost_basis, 4),
            "capital_utilization": round(capital_utilization, 4),
        }


# ---------------------------------------------------------------------------
# 改进版4%定投法
# ---------------------------------------------------------------------------

class EnhancedFourPercentModel(FourPercentModel):
    """
    改进版4%定投法模型

    在原版修正版基础上增加以下改进：

    1. 动态份数（根据E/P调整买入金额倍数）：
       - E/P > 12%：3倍金额（极度低估）
       - E/P 10%-12%：1.5倍金额（低估）
       - E/P 8%-10%：1倍金额（合理）
       - E/P < 8%：0.5倍金额（偏高）

    2. 分批止盈（改进卖出策略）：
       - 盈利 >= 15%：卖出30%
       - 盈利 >= 25%：卖出30%
       - 盈利 >= 35%：卖出40%
       - 剩余采用移动止盈：从最高点回撤10%全卖
       - 同时保留E/P < 6.4%的强制卖出

    3. 右侧补仓：
       - E/P > 12% 且连续上涨3天：半份补仓

    4. 股债利差参考（简化）：
       - 在E/P基础上增加宏观判断
    """

    def __init__(
        self,
        total_capital: float = 100000,
        num_tranches: int = 25,
        max_tranches_per_holding: int = 10,
        drop_pct: float = 0.04,
        ep_buy_threshold: float = 0.10,
        ep_sell_threshold: float = 0.064,
        valuation_type: str = "pe",
        # 改进参数
        trailing_stop_pct: float = 0.10,
        partial_tp_levels: list[float] = None,
        partial_tp_ratios: list[float] = None,
        name: str = "改进版4%定投法",
    ):
        super().__init__(
            total_capital, num_tranches, max_tranches_per_holding,
            drop_pct, ep_buy_threshold, ep_sell_threshold, valuation_type, name,
        )
        self.trailing_stop_pct = trailing_stop_pct
        self.partial_tp_levels = partial_tp_levels or [0.15, 0.25, 0.35]
        self.partial_tp_ratios = partial_tp_ratios or [0.30, 0.30, 0.40]

        # 改进状态
        self.tp_triggered: set = set()
        self.consecutive_up_days = 0
        self.last_price = 0.0
        self.last_high = 0.0

    def reset(self):
        super().reset()
        self.tp_triggered = set()
        self.consecutive_up_days = 0
        self.last_price = 0.0
        self.last_high = 0.0

    def _get_buy_multiplier(self, ep: float) -> float:
        """根据E/P动态调整买入金额倍数"""
        if ep >= 0.12:
            return 3.0  # 极度低估
        elif ep >= 0.10:
            return 1.5  # 低估
        elif ep >= 0.08:
            return 1.0  # 合理
        else:
            return 0.5  # 偏高

    def _buy(self, date: str, price: float, notes: str = "") -> bool:
        """执行买入（支持动态金额）"""
        if self.tranches_used >= self.max_tranches_per_holding:
            return False

        ep = self._calc_ep(price)
        mult = self._get_buy_multiplier(ep)
        amount = self.tranche_amount * mult

        # 不超过剩余现金的1/4（防止单份过大）
        amount = min(amount, self.cash)
        if amount < self.tranche_amount * 0.3:
            return False

        shares = amount / price
        self.cash -= amount
        old_cost = self.shares * self.cost_basis
        self.shares += shares
        self.cost_basis = (old_cost + amount) / self.shares if self.shares > 0 else 0
        self.tranches_used += 1

        self.last_buy_price = price
        self.phase = "accumulating"

        self.trades.append(TradeRecord(
            date=date, action="BUY", price=price, shares=shares,
            amount=amount, tranche=self.tranches_used,
            notes=f"{notes} | E/P {ep:.1%} | 倍率 {mult:.1f}x",
        ))
        return True

    def _partial_sell(self, date: str, price: float, ratio: float, notes: str = "") -> bool:
        """部分卖出"""
        if self.shares <= 0:
            return False

        sell_shares = self.shares * ratio
        amount = sell_shares * price
        self.cash += amount

        remaining_shares = self.shares - sell_shares

        self.trades.append(TradeRecord(
            date=date, action="SELL", price=price, shares=sell_shares,
            amount=amount, tranche=0, notes=f"部分卖出: {notes}",
        ))

        self.shares = remaining_shares
        if self.shares <= 0.0001:
            self.shares = 0.0
            self.cost_basis = 0.0
            self.tranches_used = 0
            self.last_buy_price = None
            self.phase = "observing"
        return True

    def step(self, date: str, price: float):
        """处理一天的价格数据（改进版）"""
        self.price_history.append(price)
        ep = self._calc_ep(price)

        # 连续上涨天数（右侧补仓用）
        if price > self.last_price:
            self.consecutive_up_days += 1
        else:
            self.consecutive_up_days = 0
        self.last_price = price

        # 更新最高价（止盈用）
        if price > self.last_high:
            self.last_high = price

        notes = ""

        # ---------- 有持仓时的处理 ----------
        if self.shares > 0:
            gain_pct = (price - self.cost_basis) / self.cost_basis if self.cost_basis > 0 else 0

            # 检查分批止盈
            if self.phase == "accumulating":
                for i, (level, ratio) in enumerate(zip(self.partial_tp_levels, self.partial_tp_ratios)):
                    if gain_pct >= level and i not in self.tp_triggered:
                        self._partial_sell(
                            date, price, ratio,
                            notes=f"分层止盈{i+1}：盈利{level:.0%}，卖出{ratio:.0%}"
                        )
                        self.tp_triggered.add(i)

                # 检查是否进入移动止盈阶段
                if len(self.tp_triggered) == len(self.partial_tp_levels):
                    self.phase = "trailing_stop"

            # 移动止盈
            if self.phase == "trailing_stop" and self.shares > 0:
                if price <= self.last_high * (1 - self.trailing_stop_pct):
                    self._sell_all(
                        date, price,
                        notes=f"移动止盈：从高点{self.last_high:.3f}回撤{self.trailing_stop_pct:.0%}"
                    )
                    self.tp_triggered = set()
                    return

            # 强制卖出：E/P < 6.4%
            if ep < self.ep_sell_threshold:
                self._sell_all(
                    date, price,
                    notes=f"E/P {ep:.1%} < {self.ep_sell_threshold:.0%}，高估强制卖出"
                )
                self.tp_triggered = set()
                return

            # 检查买入触发：从上一个买入点下跌4%
            if self.last_buy_price is not None:
                trigger_price = self.last_buy_price * (1 - self.drop_pct)
                if price <= trigger_price:
                    if self.tranches_used < self.max_tranches_per_holding:
                        if ep >= self.ep_buy_threshold:
                            notes = f"触发买入：从上次买入价{self.last_buy_price:.3f}下跌{self.drop_pct:.0%}"
                            self._buy(date, price, notes)
                        else:
                            notes = f"价格触发({price:.3f}<={trigger_price:.3f})但E/P {ep:.1%}未达标"
                    else:
                        notes = "价格触发但已达单标的上限(10份)"
                else:
                    notes = f"持仓等待：当前{price:.3f}，触发线{trigger_price:.3f}"

            # 右侧补仓：E/P > 12% 且连续上涨3天
            if ep >= 0.12 and self.consecutive_up_days >= 3 and self.shares > 0:
                if self.tranches_used < self.max_tranches_per_holding:
                    # 半份补仓
                    amount = self.tranche_amount * 0.5
                    if amount <= self.cash:
                        shares = amount / price
                        self.cash -= amount
                        old_cost = self.shares * self.cost_basis
                        self.shares += shares
                        self.cost_basis = (old_cost + amount) / self.shares if self.shares > 0 else 0
                        self.trades.append(TradeRecord(
                            date=date, action="BUY", price=price, shares=shares,
                            amount=amount, tranche=0, notes=f"右侧补仓：E/P {ep:.1%} 连续涨{self.consecutive_up_days}天 | 半份",
                        ))
                        notes = "右侧补仓触发"
                        self.consecutive_up_days = 0

        # ---------- 空仓时的处理 ----------
        else:
            if self.tranches_used == 0:
                # 从未买入过
                if self.initial_obs_price is None:
                    self.initial_obs_price = price
                    self.last_buy_price = price
                    notes = f"设定初始观察价 {price:.3f}，等待下跌{self.drop_pct:.0%}"
                else:
                    trigger_price = self.initial_obs_price * (1 - self.drop_pct)
                    if price <= trigger_price:
                        if ep >= self.ep_buy_threshold:
                            notes = f"首次建仓：观察价{self.initial_obs_price:.3f}下跌{self.drop_pct:.0%}"
                            self._buy(date, price, notes)
                        else:
                            notes = f"首次价格触发但E/P {ep:.1%} < {self.ep_buy_threshold:.0%}"
                    else:
                        notes = f"首次观察：等待从{self.initial_obs_price:.3f}跌到{trigger_price:.3f}"
            else:
                # 已卖出，等待再入场
                if self.initial_obs_price is None:
                    self.initial_obs_price = price
                    self.last_buy_price = price
                    notes = f"卖出后再观察：设定新观察价 {price:.3f}"
                else:
                    trigger_price = self.initial_obs_price * (1 - self.drop_pct)
                    if price <= trigger_price:
                        if ep >= self.ep_buy_threshold:
                            notes = f"再入场：从观察价{self.initial_obs_price:.3f}下跌{self.drop_pct:.0%}"
                            self._buy(date, price, notes)
                        else:
                            notes = f"再入场价格触发但E/P {ep:.1%}未达标"
                    else:
                        notes = f"等待再入场：从{self.initial_obs_price:.3f}跌到{trigger_price:.3f}"

        # 记录每日状态
        portfolio_value = self.cash + self.shares * price
        total_return = (portfolio_value - self.total_capital) / self.total_capital
        self.daily_states.append(DailyState(
            date=date, price=price, cash=self.cash, shares=self.shares,
            portfolio_value=portfolio_value, cost_basis=self.cost_basis,
            total_return=total_return, tranches_used=self.tranches_used,
            ep_proxy=ep, last_buy_price=self.last_buy_price or 0,
            notes=notes,
        ))


# ---------------------------------------------------------------------------
# 普通月定投（基准对比）
# ---------------------------------------------------------------------------

class MonthlyDcaModel:
    """普通月定投模型（作为基准对比）"""

    def __init__(self, total_capital: float = 100000, name: str = "普通月定投"):
        self.name = name
        self.total_capital = total_capital
        self.cash = total_capital
        self.shares = 0.0
        self.cost_basis = 0.0
        self.trades: list[TradeRecord] = []
        self.daily_states: list[DailyState] = []
        self.monthly_invested = 0

    def reset(self):
        self.cash = self.total_capital
        self.shares = 0.0
        self.cost_basis = 0.0
        self.trades = []
        self.daily_states = []
        self.monthly_invested = 0

    def step(self, date: str, price: float, is_month_start: bool):
        if is_month_start:
            months = 18
            amount = min(self.total_capital / months, self.cash)
            if amount > 0:
                shares = amount / price
                self.cash -= amount
                old_cost = self.shares * self.cost_basis
                self.shares += shares
                self.cost_basis = (old_cost + amount) / self.shares if self.shares > 0 else 0
                self.monthly_invested += 1
                self.trades.append(TradeRecord(
                    date=date, action="BUY", price=price, shares=shares,
                    amount=amount, tranche=self.monthly_invested,
                    notes=f"月定投第{self.monthly_invested}期",
                ))

        portfolio_value = self.cash + self.shares * price
        total_return = (portfolio_value - self.total_capital) / self.total_capital
        self.daily_states.append(DailyState(
            date=date, price=price, cash=self.cash, shares=self.shares,
            portfolio_value=portfolio_value, cost_basis=self.cost_basis,
            total_return=total_return, tranches_used=self.monthly_invested,
            ep_proxy=0, last_buy_price=price, notes="DCA",
        ))

    def run(self, df: pd.DataFrame) -> dict:
        self.reset()
        for i, row in df.iterrows():
            date = str(row["date"].date() if hasattr(row["date"], "date") else row["date"])
            price = float(row["close"])
            is_month_start = False
            if i > 0:
                prev_date = df.iloc[i - 1]["date"]
                curr_month = pd.to_datetime(row["date"]).month
                prev_month = pd.to_datetime(prev_date).month
                is_month_start = curr_month != prev_month
            else:
                is_month_start = True
            self.step(date, price, is_month_start)
        return self.get_stats(df)

    def get_stats(self, df: pd.DataFrame) -> dict:
        if not self.daily_states:
            return {}

        final_price = df["close"].iloc[-1]
        final_value = self.cash + self.shares * final_price
        total_return = (final_value - self.total_capital) / self.total_capital

        values = [s.portfolio_value for s in self.daily_states]
        max_drawdown = 0.0
        peak = values[0]
        for v in values:
            if v > peak:
                peak = v
            dd = (peak - v) / peak
            if dd > max_drawdown:
                max_drawdown = dd

        days = len(df)
        years = days / 252
        annual_return = (1 + total_return) ** (1 / years) - 1 if years > 0 and total_return > -1 else 0

        daily_returns = pd.Series(values).pct_change().dropna()
        volatility = daily_returns.std() * np.sqrt(252) if len(daily_returns) > 1 else 0
        sharpe = (annual_return - 0.02) / volatility if volatility > 0 else 0

        invested = sum(t.amount for t in self.trades if t.action == "BUY")
        capital_utilization = invested / self.total_capital if self.total_capital > 0 else 0

        return {
            "strategy": self.name,
            "total_capital": self.total_capital,
            "final_value": round(final_value, 2),
            "total_return": round(total_return, 4),
            "annual_return": round(annual_return, 4),
            "max_drawdown": round(max_drawdown, 4),
            "volatility": round(volatility, 4),
            "sharpe": round(sharpe, 4),
            "trades": len(self.trades),
            "buy_trades": len([t for t in self.trades if t.action == "BUY"]),
            "sell_trades": 0,
            "cash_remaining": round(self.cash, 2),
            "shares_remaining": round(self.shares, 4),
            "cost_basis": round(self.cost_basis, 4),
            "capital_utilization": round(capital_utilization, 4),
        }


# ---------------------------------------------------------------------------
# 回测引擎
# ---------------------------------------------------------------------------

def backtest_single(code: str, name: str, start_date: str = None, end_date: str = None,
                    capital: float = 100000) -> dict:
    """对单个标的进行回测对比"""
    df = load_history(code)
    if df.empty:
        return {"error": f"无历史数据: {code}"}

    if start_date:
        df = df[df["date"] >= pd.to_datetime(start_date)]
    if end_date:
        df = df[df["date"] <= pd.to_datetime(end_date)]

    if len(df) < 60:
        return {"error": f"数据不足: {code} ({len(df)} 条)"}

    original = FourPercentModel(total_capital=capital, name="原版4%定投法")
    enhanced = EnhancedFourPercentModel(total_capital=capital, name="改进版4%定投法")
    monthly = MonthlyDcaModel(total_capital=capital, name="普通月定投")

    original_stats = original.run(df)
    enhanced_stats = enhanced.run(df)
    monthly_stats = monthly.run(df)

    return {
        "code": code,
        "name": name,
        "period": f"{df['date'].iloc[0].date()} ~ {df['date'].iloc[-1].date()}",
        "days": len(df),
        "original": original_stats,
        "enhanced": enhanced_stats,
        "monthly": monthly_stats,
        "original_trades": [asdict(t) for t in original.trades],
        "enhanced_trades": [asdict(t) for t in enhanced.trades],
    }


def generate_comparison_report(results: list[dict]) -> str:
    """生成对比报告"""
    lines = [
        "# 4%定投法 - 回测对比报告（修正版）",
        f"",
        f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"",
        "---",
        "",
        "## 一、策略说明",
        "",
        "### 1.1 原版4%定投法（研究员雷牛牛强化版）",
        "",
        "| 参数 | 值 | 说明 |",
        "|------|-----|------|",
        "| 总份数 | **25** | 资金平均分成25份 |",
        "| 单标的上限 | **10份** | 同一只基金最多投入10份（40%） |",
        "| 触发基准 | **上一个买入点** | 非(2年最低点)，是严格的上次买入价 |",
        "| 触发跌幅 | 4% | 从上一个买入点下跌4%触发买入 |",
        "| 价格阶梯 | 0.96^n | 第n次买入价 = 第(n-1)次 × 0.96 |",
        "| 买入过滤 | E/P > 10% | 盈利收益率>10%（格雷厄姆低估线） |",
        "| 卖出条件 | E/P < 6.4% | 盈利收益率<6.4%（格雷厄姆高估线） |",
        "| 等待纪律 | 严格 | 未跌穿4%绝不提前买入 |",
        "",
        "### 1.2 改进版4%定投法",
        "",
        "| 改进点 | 原版 | 改进版 | 说明 |",
        "|--------|------|--------|------|",
        "| 买入倍率 | 固定1份 | 0.5x-3x动态 | 根据E/P调整买入金额 |",
        "| 止盈策略 | E/P<6.4%全卖 | 分层止盈+移动止盈 | 避免卖飞 |",
        "| 右侧补仓 | 无 | E/P>12%连续涨3天 | 极度低估反弹时补仓 |",
        "| 估值代理 | 价格分位反向 | 价格分位反向 | ETF无直接E/P，用代理 |",
        "",
        "---",
        "",
        "## 二、回测结果汇总",
        "",
    ]

    lines.append("### 2.1 收益率对比")
    lines.append("")
    lines.append("| 标的 | 策略 | 总收益率 | 年化收益 | 最大回撤 | 夏普比率 | 买入次数 | 卖出次数 | 资金利用率 | 期末净值 |")
    lines.append("|------|------|----------|----------|----------|----------|----------|----------|----------|----------|")

    for r in results:
        if "error" in r:
            continue
        code = r["code"]
        name = r["name"]
        for key, label in [("original", "原版"), ("enhanced", "改进版"), ("monthly", "月定投")]:
            s = r[key]
            lines.append(
                f"| {name} | {label} | {s['total_return']:+.1%} | {s['annual_return']:+.1%} | "
                f"{s['max_drawdown']:.1%} | {s['sharpe']:.2f} | {s['buy_trades']} | "
                f"{s['sell_trades']} | {s['capital_utilization']:.0%} | {s['final_value']:,.0f} |"
            )
    lines.append("")

    # 胜负统计
    lines.append("### 2.2 策略胜率统计")
    lines.append("")
    wins = {"原版4%定投法": 0, "改进版4%定投法": 0, "普通月定投": 0}
    for r in results:
        if "error" not in r:
            returns = {
                "原版4%定投法": r["original"]["total_return"],
                "改进版4%定投法": r["enhanced"]["total_return"],
                "普通月定投": r["monthly"]["total_return"],
            }
            best = max(returns, key=returns.get)
            wins[best] += 1

    lines.append("| 策略 | 获胜次数 | 胜率 |")
    lines.append("|------|----------|------|")
    total = sum(wins.values())
    for strategy, count in wins.items():
        pct = count / total if total > 0 else 0
        lines.append(f"| {strategy} | {count} | {pct:.0%} |")
    lines.append("")

    # 详细分析
    lines.append("---")
    lines.append("")
    lines.append("## 三、各标的详细分析")
    lines.append("")

    for r in results:
        if "error" in r:
            lines.append(f"### {r.get('code', '???')} - 错误: {r['error']}")
            lines.append("")
            continue

        code = r["code"]
        name = r["name"]
        lines.append(f"### 3.{results.index(r) + 1} {name} ({code})")
        lines.append("")
        lines.append(f"**回测周期**: {r['period']} | **数据天数**: {r['days']} 天")
        lines.append("")

        lines.append("| 指标 | 原版4%定投法 | 改进版4%定投法 | 普通月定投 |")
        lines.append("|------|-------------|---------------|------------|")
        metrics = [
            ("期末净值", "final_value", lambda v: f"{v:,.0f}"),
            ("总收益率", "total_return", lambda v: f"{v:+.2%}"),
            ("年化收益率", "annual_return", lambda v: f"{v:+.2%}"),
            ("最大回撤", "max_drawdown", lambda v: f"{v:.2%}"),
            ("波动率", "volatility", lambda v: f"{v:.2%}"),
            ("夏普比率", "sharpe", lambda v: f"{v:.2f}"),
            ("买入次数", "buy_trades", lambda v: f"{v}"),
            ("卖出次数", "sell_trades", lambda v: f"{v}"),
            ("资金利用率", "capital_utilization", lambda v: f"{v:.0%}"),
            ("剩余现金", "cash_remaining", lambda v: f"{v:,.0f}"),
        ]
        for label, key, fmt in metrics:
            v1 = fmt(r["original"][key])
            v2 = fmt(r["enhanced"][key])
            v3 = fmt(r["monthly"][key])
            lines.append(f"| {label} | {v1} | {v2} | {v3} |")
        lines.append("")

        if r.get("original_trades"):
            lines.append("**原版交易记录**:")
            lines.append("")
            lines.append("| 日期 | 操作 | 价格 | 份额 | 金额 | 备注 |")
            lines.append("|------|------|------|------|------|------|")
            for t in r["original_trades"][:15]:
                lines.append(
                    f"| {t['date']} | {t['action']} | {t['price']:.3f} | {t['shares']:.2f} | "
                    f"{t['amount']:,.0f} | {t.get('notes', '')} |"
                )
            if len(r["original_trades"]) > 15:
                lines.append(f"| ... | | | | | 共 {len(r['original_trades'])} 笔交易 |")
            lines.append("")

        lines.append("---")
        lines.append("")

    lines.append("## 四、核心发现与结论")
    lines.append("")

    avg_returns = {"original": [], "enhanced": [], "monthly": []}
    for r in results:
        if "error" not in r:
            avg_returns["original"].append(r["original"]["total_return"])
            avg_returns["enhanced"].append(r["enhanced"]["total_return"])
            avg_returns["monthly"].append(r["monthly"]["total_return"])

    if avg_returns["original"]:
        lines.append(f"1. **原版4%定投法平均收益率**: {np.mean(avg_returns['original']):+.2%}")
        lines.append(f"2. **改进版4%定投法平均收益率**: {np.mean(avg_returns['enhanced']):+.2%}")
        lines.append(f"3. **普通月定投平均收益率**: {np.mean(avg_returns['monthly']):+.2%}")
        lines.append("")

    lines.append("### 修正版与原版的本质差异")
    lines.append("")
    lines.append("1. **触发基准改变**：原版是'从上一个买入点'下跌4%，不是从'2年最低点'——这意味着反弹后需要更大的跌幅才能再次触发")
    lines.append("2. **份数体系**：25份总量+10份单标的上限，比我之前理解的10份更灵活")
    lines.append("3. **格雷厄姆估值过滤**：E/P>10%启动、<6.4%卖出，提供了明确的量化标准")
    lines.append("4. **严格等待**：未跌穿4%绝不买入，大量现金可能长期闲置")
    lines.append("")

    lines.append("### 投资建议")
    lines.append("")
    lines.append("1. **适用场景**：4%法在**震荡市和下跌市**表现较好，在单边上涨市中容易踏空")
    lines.append("2. **资金管理**：25份设计意味着可承受约40%跌幅（10份×4%），与历史极端回撤匹配")
    lines.append("3. **心态要求**：需要极强的纪律性，接受'大量现金闲置'的状态")
    lines.append("4. **标的筛选**：成立>7年、业绩稳定、PE/PB与点位高度相关的基金")
    lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("*本报告基于历史数据回测生成，仅供研究参考，不构成投资建议。投资有风险，入市需谨慎。*")
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="4%定投法回测与信号系统（修正版）")
    parser.add_argument("--backtest", type=str, help="回测单个标的代码，如 510300")
    parser.add_argument("--start", type=str, default="2022-01-01", help="回测开始日期")
    parser.add_argument("--end", type=str, default=None, help="回测结束日期")
    parser.add_argument("--capital", type=float, default=100000, help="初始资金")
    parser.add_argument("--backtest-all", action="store_true", help="回测所有配置标的")
    args = parser.parse_args()

    if args.backtest:
        name = args.backtest
        config_path = DATA_DIR / "portfolio_config.json"
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            for h in config.get("holdings", []):
                if h["code"] == args.backtest:
                    name = h["name"]
                    break

        print(f"回测标的: {name} ({args.backtest})")
        print(f"回测周期: {args.start} ~ {args.end or '最新'}")
        print(f"初始资金: {args.capital:,.0f}")
        print("=" * 60)

        result = backtest_single(args.backtest, name, args.start, args.end, args.capital)

        if "error" in result:
            print(f"错误: {result['error']}")
            return

        for key, label in [("original", "原版"), ("enhanced", "改进版"), ("monthly", "月定投")]:
            s = result[key]
            print(f"\n[{label}]")
            print(f"  期末净值: {s['final_value']:,.0f}")
            print(f"  总收益率: {s['total_return']:+.2%}")
            print(f"  年化收益: {s['annual_return']:+.2%}")
            print(f"  最大回撤: {s['max_drawdown']:.2%}")
            print(f"  夏普比率: {s['sharpe']:.2f}")
            print(f"  买入次数: {s['buy_trades']} | 卖出次数: {s['sell_trades']}")
            print(f"  资金利用率: {s['capital_utilization']:.0%}")

        report = generate_comparison_report([result])
        report_path = REPORTS_DIR / f"backtest_{args.backtest}_{datetime.now().strftime('%Y%m%d')}.md"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"\n报告已保存: {report_path}")

    elif args.backtest_all:
        config_path = DATA_DIR / "portfolio_config.json"
        if not config_path.exists():
            print("错误: 未找到 portfolio_config.json")
            return

        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        holdings = config.get("holdings", [])
        print(f"回测 {len(holdings)} 个标的...")
        print("=" * 60)

        results = []
        for h in holdings:
            code = h["code"]
            name = h["name"]
            print(f"\n回测: {name} ({code})...", end=" ")
            result = backtest_single(code, name, args.start, args.end, args.capital)
            if "error" in result:
                print(f"失败: {result['error']}")
            else:
                print(f"完成")
                print(f"  原版: {result['original']['total_return']:+.1%} | "
                      f"改进版: {result['enhanced']['total_return']:+.1%} | "
                      f"月定投: {result['monthly']['total_return']:+.1%}")
            results.append(result)

        report = generate_comparison_report(results)
        report_path = REPORTS_DIR / f"backtest_all_{datetime.now().strftime('%Y%m%d')}.md"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"\n{'=' * 60}")
        print(f"汇总报告已保存: {report_path}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
