"""Tests for hippocli.converter module."""
from __future__ import annotations

import json
from pathlib import Path

import polars as pl
import pytest

from hippocli.converter import (
    json_to_csv,
    json_to_json_array,
    json_to_parquet,
    json_to_sql,
    read_json,
)

DATA_DIR = Path(__file__).parent / "data"
COMPANY_JSON = DATA_DIR / "sample_company_details.json"
STOCK_PRICE_JSON = DATA_DIR / "sample_stock_price_insights.json"


# ---------------------------------------------------------------------------
# read_json
# ---------------------------------------------------------------------------

class TestReadJson:
    def test_read_array(self):
        df = read_json(COMPANY_JSON)
        assert isinstance(df, pl.DataFrame)
        assert df.height == 2
        assert "ticker" in df.columns

    def test_read_single_object(self, tmp_path: Path):
        single = tmp_path / "single.json"
        single.write_text(json.dumps({"id": 1, "name": "Solo", "ticker": "SOLO"}))
        df = read_json(single)
        assert df.height == 1
        assert df["ticker"][0] == "SOLO"

    def test_read_missing_file(self, tmp_path: Path):
        with pytest.raises(FileNotFoundError):
            read_json(tmp_path / "nope.json")

    def test_read_empty_array(self, tmp_path: Path):
        empty = tmp_path / "empty.json"
        empty.write_text("[]")
        df = read_json(empty)
        assert df.height == 0

    def test_read_stock_price_data(self):
        df = read_json(STOCK_PRICE_JSON)
        assert df.height == 10
        assert "value" in df.columns
        assert "ticker" in df.columns


# ---------------------------------------------------------------------------
# json_to_csv
# ---------------------------------------------------------------------------

class TestJsonToCsv:
    def test_basic_conversion(self, tmp_path: Path):
        csv_out = tmp_path / "company.csv"
        company_count, stock_count = json_to_csv(COMPANY_JSON, csv_out)
        assert company_count == 2
        assert stock_count == 0  # no stock_price_csv specified
        assert csv_out.exists()
        content = csv_out.read_text()
        assert "ACME" in content
        assert "TEST" in content

    def test_with_stock_price(self, tmp_path: Path):
        csv_out = tmp_path / "company.csv"
        stock_csv = tmp_path / "stock.csv"
        company_count, stock_count = json_to_csv(
            COMPANY_JSON, csv_out,
            stock_price_csv=stock_csv,
            stock_price_json=STOCK_PRICE_JSON,
        )
        assert company_count == 2
        assert stock_count == 10
        assert csv_out.exists()
        assert stock_csv.exists()

    def test_output_directory_created(self, tmp_path: Path):
        nested = tmp_path / "a" / "b" / "out.csv"
        json_to_csv(COMPANY_JSON, nested)
        assert nested.exists()


# ---------------------------------------------------------------------------
# json_to_parquet
# ---------------------------------------------------------------------------

class TestJsonToParquet:
    def test_basic_conversion(self, tmp_path: Path):
        pq_out = tmp_path / "company.parquet"
        company_count, stock_count = json_to_parquet(COMPANY_JSON, pq_out)
        assert company_count == 2
        assert stock_count == 0
        assert pq_out.exists()
        # Verify parquet is readable
        df = pl.read_parquet(pq_out)
        assert df.height == 2

    def test_with_stock_price(self, tmp_path: Path):
        pq_out = tmp_path / "company.parquet"
        stock_pq = tmp_path / "stock.parquet"
        company_count, stock_count = json_to_parquet(
            COMPANY_JSON, pq_out,
            stock_price_parquet=stock_pq,
            stock_price_json=STOCK_PRICE_JSON,
        )
        assert company_count == 2
        assert stock_count == 10
        assert stock_pq.exists()
        stock_df = pl.read_parquet(stock_pq)
        assert stock_df.height == 10


# ---------------------------------------------------------------------------
# json_to_sql
# ---------------------------------------------------------------------------

class TestJsonToSql:
    def test_basic_conversion(self, tmp_path: Path):
        sql_out = tmp_path / "company.sql"
        company_count, stock_count = json_to_sql(COMPANY_JSON, sql_out)
        assert company_count == 2
        assert stock_count == 0
        assert sql_out.exists()
        content = sql_out.read_text()
        assert "CREATE TABLE" in content
        assert "INSERT INTO" in content
        assert "ACME" in content

    def test_with_stock_price(self, tmp_path: Path):
        sql_out = tmp_path / "company.sql"
        stock_sql = tmp_path / "stock.sql"
        company_count, stock_count = json_to_sql(
            COMPANY_JSON, sql_out,
            stock_price_sql=stock_sql,
            stock_price_json=STOCK_PRICE_JSON,
        )
        assert company_count == 2
        assert stock_count == 10
        assert stock_sql.exists()
        stock_content = stock_sql.read_text()
        assert "stock_price_insights" in stock_content

    def test_custom_table_name(self, tmp_path: Path):
        sql_out = tmp_path / "custom.sql"
        json_to_sql(COMPANY_JSON, sql_out, table_name="my_companies")
        content = sql_out.read_text()
        assert "my_companies" in content


# ---------------------------------------------------------------------------
# json_to_json_array
# ---------------------------------------------------------------------------

class TestJsonToJsonArray:
    def test_roundtrip(self, tmp_path: Path):
        out = tmp_path / "out.json"
        count = json_to_json_array(COMPANY_JSON, out)
        assert count == 2
        assert out.exists()
        data = json.loads(out.read_text())
        assert isinstance(data, list)
        assert len(data) == 2

    def test_stock_price_roundtrip(self, tmp_path: Path):
        out = tmp_path / "stock_out.json"
        count = json_to_json_array(STOCK_PRICE_JSON, out)
        assert count == 10


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestConverterEdgeCases:
    def test_csv_empty_input(self, tmp_path: Path):
        empty = tmp_path / "empty.json"
        empty.write_text("[]")
        csv_out = tmp_path / "out.csv"
        company_count, stock_count = json_to_csv(empty, csv_out)
        assert company_count == 0

    def test_parquet_empty_input(self, tmp_path: Path):
        empty = tmp_path / "empty.json"
        empty.write_text("[]")
        pq_out = tmp_path / "out.parquet"
        company_count, stock_count = json_to_parquet(empty, pq_out)
        assert company_count == 0

    def test_sql_empty_input(self, tmp_path: Path):
        empty = tmp_path / "empty.json"
        empty.write_text("[]")
        sql_out = tmp_path / "out.sql"
        company_count, stock_count = json_to_sql(empty, sql_out)
        assert company_count == 0
        content = sql_out.read_text()
        assert "CREATE TABLE" in content
