"""
Tests for the 4% DCA model (four_percent_model.py).

Covers both FourPercentModel (original) and EnhancedFourPercentModel.

Run:  pytest tests/test_four_percent_model.py -v
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from four_percent_model import (
    FourPercentModel,
    EnhancedFourPercentModel,
    MonthlyDcaModel,
    calc_ep_proxy,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_price_history(prices: list[float]) -> pd.DataFrame:
    """Build a DataFrame from a list of prices with sequential dates."""
    dates = pd.date_range("2024-01-01", periods=len(prices), freq="B")
    return pd.DataFrame({"date": dates, "close": prices})


def _make_long_history(base_price: float = 3.0, days: int = 252) -> list[float]:
    """Generate a long-enough history so E/P proxy calc works (>60 days)."""
    rng = np.random.default_rng(42)
    prices = base_price * (1 + rng.normal(0, 0.015, days).cumsum() / 100)
    return prices.tolist()


def _prep_model(model, hist_prices: list[float]):
    """Pre-populate price_history so E/P proxy works immediately."""
    model.price_history = list(hist_prices)


# ---------------------------------------------------------------------------
# calc_ep_proxy
# ---------------------------------------------------------------------------

def test_ep_proxy_returns_default_for_short_history():
    prices = [3.0] * 30
    assert calc_ep_proxy(3.0, prices) == 0.075


def test_ep_proxy_higher_when_price_low():
    history = _make_long_history(base_price=3.0, days=200)
    ep_low = calc_ep_proxy(2.0, history)
    ep_high = calc_ep_proxy(4.0, history)
    assert ep_low > ep_high


# ---------------------------------------------------------------------------
# FourPercentModel — initial observation
# ---------------------------------------------------------------------------

class TestInitialObservation:
    def test_sets_observation_price_on_first_step(self):
        model = FourPercentModel(total_capital=100000)
        _prep_model(model, _make_long_history(base_price=3.0, days=200))
        model.step("2024-01-01", 3.0)
        assert model.initial_obs_price == 3.0
        assert model.last_buy_price == 3.0
        assert model.tranches_used == 0

    def test_no_buy_when_price_unchanged(self):
        model = FourPercentModel(total_capital=100000)
        _prep_model(model, _make_long_history(base_price=3.0, days=200))
        for _ in range(10):
            model.step("2024-01-01", 3.0)
        assert model.tranches_used == 0


# ---------------------------------------------------------------------------
# FourPercentModel — first buy trigger
# ---------------------------------------------------------------------------

class TestFirstBuy:
    def test_buys_when_price_drops_4pct_from_obs(self):
        model = FourPercentModel(total_capital=100000)
        # History median ~8.0, observe at 1.5 → E/P high
        _prep_model(model, _make_long_history(base_price=8.0, days=200))
        model.step("day1", 1.5)
        assert model.tranches_used == 0
        model.step("day2", 1.5 * 0.959)  # -4.1%, E/P >> 10%
        assert model.tranches_used == 1
        assert model.shares > 0

    def test_does_not_buy_when_drop_less_than_4pct(self):
        model = FourPercentModel(total_capital=100000)
        _prep_model(model, _make_long_history(base_price=8.0, days=200))
        model.step("day1", 1.5)
        model.step("day2", 1.5 * 0.97)  # -3%
        assert model.tranches_used == 0


# ---------------------------------------------------------------------------
# FourPercentModel — E/P filter
# ---------------------------------------------------------------------------

class TestEPFilter:
    def test_blocks_buy_when_ep_below_10pct(self):
        model = FourPercentModel(total_capital=100000)
        # History clustered near 1.0 → median ~1.0
        # Observation at 4.0 → current price >> median → E/P low
        _prep_model(model, _make_long_history(base_price=1.0, days=200))
        model.step("day1", 4.0)
        model.step("day2", 4.0 * 0.959)  # -4.1%, but E/P << 10%
        assert model.tranches_used == 0

    def test_allows_buy_when_ep_above_10pct(self):
        model = FourPercentModel(total_capital=100000)
        # History clustered near 5.0 → median ~5.0
        # Observation at 2.0 → current price << median → E/P high
        _prep_model(model, _make_long_history(base_price=5.0, days=200))
        model.step("day1", 2.0)
        model.step("day2", 2.0 * 0.959)  # -4.1%, E/P > 10%
        assert model.tranches_used == 1


# ---------------------------------------------------------------------------
# FourPercentModel — subsequent buys
# ---------------------------------------------------------------------------

class TestSubsequentBuys:
    def test_triggers_from_last_buy_price(self):
        model = FourPercentModel(total_capital=100000)
        _prep_model(model, _make_long_history(base_price=8.0, days=200))
        model.step("day1", 1.5)
        model.step("day2", 1.5 * 0.959)  # buy at ~1.439
        assert model.tranches_used == 1
        buy1_price = model.last_buy_price
        model.step("day3", buy1_price * 0.959)  # another -4.1%
        assert model.tranches_used == 2

    def test_does_not_buy_when_price_above_trigger(self):
        model = FourPercentModel(total_capital=100000)
        _prep_model(model, _make_long_history(base_price=8.0, days=200))
        model.step("day1", 1.5)
        model.step("day2", 1.5 * 0.959)  # buy
        assert model.tranches_used == 1
        buy_price = model.last_buy_price
        model.step("day3", buy_price * 0.98)  # only -2%
        assert model.tranches_used == 1


# ---------------------------------------------------------------------------
# FourPercentModel — sell
# ---------------------------------------------------------------------------

class TestSell:
    def test_sells_all_when_ep_below_6_4pct(self):
        model = FourPercentModel(total_capital=100000)
        _prep_model(model, _make_long_history(base_price=2.0, days=200))
        # Buy at low price first
        model.step("day1", 1.0)
        model.step("day2", 1.0 * 0.959)  # buy at ~0.959
        assert model.shares > 0
        # Skyrocket price → E/P << 6.4%
        model.step("day3", 15.0)
        assert model.shares == 0


# ---------------------------------------------------------------------------
# FourPercentModel — max tranches
# ---------------------------------------------------------------------------

class TestMaxTranches:
    def test_stops_buying_at_10_tranches(self):
        model = FourPercentModel(total_capital=100000)
        _prep_model(model, _make_long_history(base_price=1.5, days=200))
        price = 1.0
        model.step("init", price)
        for i in range(12):
            price = price * 0.959
            model.step(f"day{i}", price)
        assert model.tranches_used == 10


# ---------------------------------------------------------------------------
# EnhancedFourPercentModel — partial take-profit
# ---------------------------------------------------------------------------

class TestEnhancedTakeProfit:
    def test_partial_sell_at_15pct_gain(self):
        model = EnhancedFourPercentModel(total_capital=100000)
        _prep_model(model, _make_long_history(base_price=8.0, days=200))
        model.step("day1", 1.5)
        model.step("day2", 1.5 * 0.959)  # buy at ~1.439
        assert model.shares > 0
        initial_shares = model.shares
        model.step("day3", model.cost_basis * 1.155)  # +15.5%
        assert model.shares < initial_shares

    def test_trailing_stop_after_all_levels(self):
        model = EnhancedFourPercentModel(total_capital=100000)
        _prep_model(model, _make_long_history(base_price=1.0, days=200))
        model.step("day1", 0.8)
        model.step("day2", 0.8 * 0.959)  # buy
        cost = model.cost_basis
        model.step("day3", cost * 1.40)  # hit all 3 levels
        model.step("day4", cost * 1.50)  # push high
        model.step("day5", cost * 1.50 * 0.89)  # -11% from high
        assert model.shares == 0


# ---------------------------------------------------------------------------
# EnhancedFourPercentModel — dynamic multiplier
# ---------------------------------------------------------------------------

class TestDynamicMultiplier:
    def test_3x_buy_when_ep_above_12pct(self):
        model = EnhancedFourPercentModel(total_capital=100000)
        # History median ~5.0, buy at ~1.0 → E/P >> 12%
        _prep_model(model, _make_long_history(base_price=5.0, days=200))
        model.step("day1", 1.0)
        model.step("day2", 1.0 * 0.959)  # buy at ~0.959
        assert model.tranches_used == 1
        trade = model.trades[0]
        standard_tranche = 100000 / 25  # 4000
        assert trade.amount > standard_tranche * 2


# ---------------------------------------------------------------------------
# MonthlyDcaModel — baseline comparison
# ---------------------------------------------------------------------------

class TestMonthlyDca:
    def test_buys_monthly(self):
        model = MonthlyDcaModel(total_capital=120000)
        dates = pd.date_range("2024-01-01", periods=60, freq="B")
        df = pd.DataFrame({"date": dates, "close": [3.0] * 60})
        model.run(df)
        assert 2 <= model.monthly_invested <= 4


# ---------------------------------------------------------------------------
# FourPercentModel — full backtest run
# ---------------------------------------------------------------------------

class TestFullBacktest:
    def test_run_produces_valid_stats(self):
        model = FourPercentModel(total_capital=100000)
        df = _make_price_history(_make_long_history(base_price=3.0, days=252))
        stats = model.run(df)
        assert "total_return" in stats
        assert "max_drawdown" in stats
        assert stats["final_value"] > 0

    def test_three_strategies_produce_comparable_stats(self):
        df = _make_price_history(_make_long_history(base_price=3.0, days=252))
        for model_cls in [FourPercentModel, EnhancedFourPercentModel, MonthlyDcaModel]:
            stats = model_cls(total_capital=100000, name="test").run(df)
            assert stats["final_value"] > 0


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_zero_price_handled_gracefully(self):
        model = FourPercentModel(total_capital=100000)
        _prep_model(model, _make_long_history(base_price=3.0, days=200))
        # Zero price should not crash
        model.step("day", 0.0)
        assert model.tranches_used == 0

    def test_empty_history_backtest(self):
        model = FourPercentModel(total_capital=100000)
        df = pd.DataFrame({"date": [], "close": []})
        stats = model.run(df)
        assert stats == {}

    def test_cash_constraint_on_buy(self):
        model = FourPercentModel(total_capital=400, num_tranches=25)
        # 25 tranches of 16 each — buy many times
        _prep_model(model, _make_long_history(base_price=1.0, days=200))
        price = 0.5
        model.step("init", price)
        for i in range(25):
            price = price * 0.959
            model.step(f"day{i}", price)
        # Should not spend more than total capital
        total_spent = sum(t.amount for t in model.trades if t.action == "BUY")
        assert total_spent <= 400
