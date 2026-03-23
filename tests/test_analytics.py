"""Tests for hippocli.analytics module."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from hippocli.analytics import analytics_from_json, compute_price_metrics


DATA_DIR = Path(__file__).parent / "data"
COMPANY_JSON = DATA_DIR / "sample_company_details.json"
STOCK_PRICE_JSON = DATA_DIR / "sample_stock_price_insights.json"


# ---------------------------------------------------------------------------
# compute_price_metrics (unit-level)
# ---------------------------------------------------------------------------

class TestComputePriceMetrics:
    def test_basic_metrics(self):
        prices = [100.0, 102.0, 98.0, 105.0, 103.0]
        result = compute_price_metrics(prices, horizon_days=63)
        assert result["latest_price"] == 103.0
        assert result["high"] == 105.0
        assert result["low"] == 98.0
        assert result["observations"] == 5
        assert "volatility_annual" in result
        assert "max_drawdown_pct" in result
        assert "error" not in result

    def test_empty_prices(self):
        result = compute_price_metrics([], horizon_days=63)
        assert "error" in result

    def test_single_price(self):
        result = compute_price_metrics([50.0], horizon_days=63)
        assert result["latest_price"] == 50.0
        assert result["high"] == 50.0
        assert result["low"] == 50.0
        assert result["observations"] == 1

    def test_horizon_trims_data(self):
        prices = list(range(1, 101))  # 100 prices
        result = compute_price_metrics([float(p) for p in prices], horizon_days=10)
        assert result["observations"] == 10
        assert result["latest_price"] == 100.0
        assert result["low"] == 91.0


# ---------------------------------------------------------------------------
# analytics_from_json
# ---------------------------------------------------------------------------

class TestAnalyticsFromJson:
    def test_basic_analytics(self):
        result = analytics_from_json(
            COMPANY_JSON, ticker="ACME", horizon_days=90,
            stock_price_json_path=STOCK_PRICE_JSON,
        )
        assert result["ticker"] == "ACME"
        assert "latest_price" in result
        assert "error" not in result

    def test_ticker_not_found(self):
        result = analytics_from_json(
            COMPANY_JSON, ticker="ZZZZZ", horizon_days=90,
            stock_price_json_path=STOCK_PRICE_JSON,
        )
        assert result["ticker"] == "ZZZZZ"
        assert "error" in result
        assert "not found" in result["error"].lower()

    def test_case_insensitive_ticker(self):
        result = analytics_from_json(
            COMPANY_JSON, ticker="acme", horizon_days=90,
            stock_price_json_path=STOCK_PRICE_JSON,
        )
        assert result["ticker"] == "ACME"
        assert "error" not in result

    def test_missing_stock_price_file(self, tmp_path: Path):
        result = analytics_from_json(
            COMPANY_JSON, ticker="ACME", horizon_days=90,
            stock_price_json_path=tmp_path / "nonexistent.json",
        )
        assert "error" in result

    def test_metrics_fields_present(self):
        result = analytics_from_json(
            COMPANY_JSON, ticker="ACME", horizon_days=90,
            stock_price_json_path=STOCK_PRICE_JSON,
        )
        for key in ("latest_price", "average_price", "high", "low",
                     "volatility_annual", "max_drawdown_pct", "observations",
                     "generated_at"):
            assert key in result, f"Missing key: {key}"

    def test_empty_stock_price_data(self, tmp_path: Path):
        empty_stock = tmp_path / "empty_stock.json"
        empty_stock.write_text("[]")
        result = analytics_from_json(
            COMPANY_JSON, ticker="ACME", horizon_days=90,
            stock_price_json_path=empty_stock,
        )
        assert "error" in result


# ---------------------------------------------------------------------------
# Config path resolution
# ---------------------------------------------------------------------------

class TestConfigPaths:
    def test_repo_root_is_valid(self):
        from hippocli.config import REPO_ROOT
        assert REPO_ROOT.exists()

    def test_path_settings_defaults(self):
        from hippocli.config import PathSettings
        ps = PathSettings()
        assert ps.base_dir.exists()

    def test_get_ticker_paths(self):
        from hippocli.config import PathSettings
        ps = PathSettings()
        paths = ps.get_ticker_paths("ACME")
        assert "json" in paths
        assert "csv" in paths
        assert "parquet" in paths
        assert "sql" in paths
        assert "ACME" in str(paths["json"])
        # Stock price paths
        assert "json_stock_price" in paths
        assert "stock_price_insights" in str(paths["json_stock_price"])

    def test_get_ticker_paths_case_insensitive(self):
        from hippocli.config import PathSettings
        ps = PathSettings()
        paths = ps.get_ticker_paths("  acme  ")
        assert "ACME" in str(paths["json"])
