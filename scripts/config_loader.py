#!/usr/bin/env python3
"""
Configuration loader — loads model_params.json with typed accessors.

Each script imports the section it needs instead of maintaining its own
hardcoded constants.  Edit data/model_params.json to update the model;
the code stays unchanged.

Usage:
    from config_loader import load_config

    cfg = load_config()
    cycles = cfg.kondratiev_cycles()
    candidates = cfg.etf_candidates()
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

BASE_DIR = Path(__file__).parent.parent
CONFIG_PATH = BASE_DIR / "data" / "model_params.json"

# Cache — loaded once per process
_config: Optional["ModelConfig"] = None


# ---------------------------------------------------------------------------
# Typed config accessor
# ---------------------------------------------------------------------------

@dataclass
class ModelConfig:
    _raw: Dict[str, Any]

    # -- kondratiev_model ------------------------------------------------
    def kondratiev_cycles(self) -> List[Dict]:
        return self._raw.get("kondratiev", {}).get("cycles", [])

    def kondratiev_phase_descriptions(self) -> Dict:
        return self._raw.get("kondratiev", {}).get("phase_descriptions", {})

    def kondratiev_investment_themes(self) -> Dict:
        return self._raw.get("kondratiev", {}).get("investment_themes_2026", {})

    # -- cycle_phase_evaluator -------------------------------------------
    def cycle_kondratiev_2026(self) -> Dict:
        return self._raw.get("cycle_phase", {}).get("kondratiev_2026", {})

    def cycle_juglar_cycles(self) -> List[Dict]:
        return self._raw.get("cycle_phase", {}).get("juglar_cycles", [])

    def cycle_kitchin_cycles(self) -> List[Dict]:
        return self._raw.get("cycle_phase", {}).get("kitchin_cycles", [])

    # -- asset_allocator ------------------------------------------------
    def asset_phase_matrix(self) -> Dict:
        return self._raw.get("asset_allocation", {}).get("phase_matrix", {})

    def asset_etf_map(self) -> Dict:
        return self._raw.get("asset_allocation", {}).get("etf_asset_map", {})

    def asset_default_portfolio(self) -> Dict[str, float]:
        return self._raw.get("asset_allocation", {}).get("default_portfolio", {})

    # -- market_indicators ----------------------------------------------
    def market_valuation(self) -> List[Dict]:
        return self._raw.get("market_indicators", {}).get("valuation", [])

    def market_sentiment(self) -> List[Dict]:
        return self._raw.get("market_indicators", {}).get("sentiment", [])

    def market_liquidity(self) -> List[Dict]:
        return self._raw.get("market_indicators", {}).get("liquidity", [])

    def market_commodity(self) -> List[Dict]:
        return self._raw.get("market_indicators", {}).get("commodity", [])

    # -- policy_analyzer ------------------------------------------------
    def policy_fyp_industries(self) -> Dict:
        return self._raw.get("policy", {}).get("fifteenth_fyp_industries", {})

    def policy_commodities(self) -> Dict:
        return self._raw.get("policy", {}).get("commodities", {})

    def policy_fed(self) -> Dict:
        return self._raw.get("policy", {}).get("fed_policy", {})

    def policy_pboc(self) -> Dict:
        return self._raw.get("policy", {}).get("pboc_policy", {})

    # -- etf_selector ---------------------------------------------------
    def etf_weights(self) -> Dict[str, float]:
        return self._raw.get("etf_selector", {}).get("weights", {})

    def etf_candidates(self) -> Dict:
        return self._raw.get("etf_selector", {}).get("candidates", {})

    def etf_scoring(self) -> Dict:
        return self._raw.get("etf_selector", {}).get("scoring", {})

    def etf_dynamic_weights(self) -> Dict:
        return self._raw.get("etf_selector", {}).get("dynamic_weights", {})


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def load_config(reload: bool = False) -> ModelConfig:
    """Load model_params.json, caching the result. Pass reload=True to force re-read."""
    global _config
    if _config is not None and not reload:
        return _config

    if not CONFIG_PATH.exists():
        raise FileNotFoundError(
            f"Config file not found: {CONFIG_PATH}\n"
            "Run from the project root or ensure data/model_params.json exists."
        )

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        raw = json.load(f)

    _config = ModelConfig(raw)
    return _config


def reload_config() -> ModelConfig:
    """Force reload from disk."""
    return load_config(reload=True)
