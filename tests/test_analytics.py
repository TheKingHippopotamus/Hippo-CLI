from pathlib import Path

from hippocli.analytics import analytics_from_ndjson


def test_analytics_basic():
    ndjson = Path(__file__).parent / "data" / "sample_companies.ndjson"
    result = analytics_from_ndjson(ndjson, ticker="ACME", horizon_days=90)
    assert result["ticker"] == "ACME"
    assert "latest_price" in result
    assert "error" not in result

