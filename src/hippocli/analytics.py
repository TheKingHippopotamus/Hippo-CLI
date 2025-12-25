from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import polars as pl

from .logging_config import get_logger
from .converter import read_json

logger = get_logger(__name__)


def _extract_prices_from_stock_price_data(stock_price_data: List[Dict[str, Any]]) -> List[float]:
    """Extract price values from stock price insights data."""
    prices = []
    if not isinstance(stock_price_data, list):
        return prices
    for item in stock_price_data:
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


def analytics_from_json(
    json_path: Path, ticker: str, horizon_days: int = 63, stock_price_json_path: Optional[Path] = None
) -> Dict[str, Any]:
    """Calculate analytics from JSON files.
    
    Args:
        json_path: Path to company details JSON file (used for ticker validation)
        ticker: Ticker symbol
        horizon_days: Number of days to consider for metrics
        stock_price_json_path: Optional path to stock price insights JSON file.
                             If not provided, will be inferred from json_path.
    """
    # Validate ticker exists in company details
    df: pl.DataFrame = read_json(json_path)
    recs = df.filter(pl.col("ticker") == ticker.upper())
    if recs.is_empty():
        return {"ticker": ticker.upper(), "error": "Ticker not found"}

    # Determine stock price JSON path
    if stock_price_json_path is None:
        # Infer from company details path: .../AAPL/AAPL_company_details.json -> .../AAPL/AAPL_stock_price_insights.json
        ticker_upper = ticker.upper()
        stock_price_json_path = json_path.parent / f"{ticker_upper}_stock_price_insights.json"
    
    # Read stock price data
    if not stock_price_json_path.exists():
        return {"ticker": ticker.upper(), "error": f"Stock price data not found: {stock_price_json_path}"}
    
    try:
        stock_price_df = read_json(stock_price_json_path)
        if stock_price_df.is_empty():
            return {"ticker": ticker.upper(), "error": "No stock price data available"}
        
        # Extract prices from stock price data
        # Stock price data format: [{"company_id": 1, "ticker": "AAPL", "ts": ..., "value": 175.43, ...}, ...]
        prices = []
        if "value" in stock_price_df.columns:
            # Get values and sort by timestamp if available
            price_data = stock_price_df.select("value").to_series().to_list()
            prices = [float(v) for v in price_data if v is not None and isinstance(v, (int, float))]
        else:
            # Fallback: try to extract from dict format
            stock_price_records = stock_price_df.to_dicts()
            prices = _extract_prices_from_stock_price_data(stock_price_records)
        
        if not prices:
            return {"ticker": ticker.upper(), "error": "No valid price data found"}
        
        metrics = compute_price_metrics(prices, horizon_days=horizon_days)
        metrics["ticker"] = ticker.upper()
        metrics["generated_at"] = datetime.utcnow().isoformat()
        return metrics
    except Exception as exc:
        logger.error("Error reading stock price data: %s", exc)
        return {"ticker": ticker.upper(), "error": f"Error processing stock price data: {exc}"}

