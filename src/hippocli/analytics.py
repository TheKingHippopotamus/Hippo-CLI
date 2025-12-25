from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import polars as pl

from .logging_config import get_logger
from .converter import read_ndjson

logger = get_logger(__name__)


def _extract_prices(insights: Dict[str, Any]) -> List[float]:
    prices = []
    series = insights.get("stock_price") if isinstance(insights, dict) else None
    if not isinstance(series, list):
        return prices
    for item in series:
        if not isinstance(item, dict):
            continue
        value = item.get("value")
        if isinstance(value, (int, float)):
            prices.append(float(value))
    return prices


def compute_price_metrics(prices: List[float], horizon_days: int = 63) -> Dict[str, Any]:
    if not prices:
        return {"error": "No price data"}
    series = pd.Series(prices[-horizon_days:])
    if series.empty:
        return {"error": "No price data in selected horizon"}

    returns = series.pct_change().dropna()
    max_price = series.max()
    min_price = series.min()
    latest = series.iloc[-1]
    max_drawdown = ((series.cummax() - series) / series.cummax()).max()

    return {
        "latest_price": latest,
        "average_price": series.mean(),
        "high": max_price,
        "low": min_price,
        "volatility_annual": float(returns.std() * (252**0.5)) if not returns.empty else None,
        "max_drawdown_pct": float(max_drawdown * 100) if max_drawdown is not None else None,
        "observations": int(len(series)),
    }


def analytics_from_ndjson(
    ndjson_path: Path, ticker: str, horizon_days: int = 63
) -> Dict[str, Any]:
    df: pl.DataFrame = read_ndjson(ndjson_path)
    recs = df.filter(pl.col("ticker") == ticker.upper())
    if recs.is_empty():
        return {"ticker": ticker.upper(), "error": "Ticker not found"}

    insights = recs.select("insights").to_dicts()[0].get("insights", {})
    prices = _extract_prices(insights)
    metrics = compute_price_metrics(prices, horizon_days=horizon_days)
    metrics["ticker"] = ticker.upper()
    metrics["generated_at"] = datetime.utcnow().isoformat()
    return metrics

