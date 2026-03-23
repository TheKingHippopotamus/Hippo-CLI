"""Tests for hippocli.validator module."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from hippocli.validator import validate_mapping, validate_json, load_mapping
from hippocli.models import TickerEntry, CompanyRecord


DATA_DIR = Path(__file__).parent / "data"


# ---------------------------------------------------------------------------
# validate_mapping
# ---------------------------------------------------------------------------

class TestValidateMapping:
    def test_valid_mapping(self):
        count, errors = validate_mapping(DATA_DIR / "sample_mapping.json")
        assert count == 2
        assert errors == []

    def test_missing_mapping_file(self, tmp_path: Path):
        count, errors = validate_mapping(tmp_path / "nonexistent.json")
        assert count == 0
        assert len(errors) == 1
        assert "not found" in errors[0].lower()

    def test_mapping_not_an_array(self, tmp_path: Path):
        bad = tmp_path / "bad.json"
        bad.write_text('{"id": 1, "name": "X", "ticker": "X"}')
        count, errors = validate_mapping(bad)
        assert count == 0
        assert len(errors) == 1

    def test_mapping_duplicate_ids(self, tmp_path: Path):
        dup = tmp_path / "dup.json"
        dup.write_text(json.dumps([
            {"id": 1, "name": "A", "ticker": "AAA"},
            {"id": 1, "name": "B", "ticker": "BBB"},
        ]))
        count, errors = validate_mapping(dup)
        assert count == 2
        assert any("Duplicate id" in e for e in errors)

    def test_mapping_duplicate_tickers(self, tmp_path: Path):
        dup = tmp_path / "dup.json"
        dup.write_text(json.dumps([
            {"id": 1, "name": "A", "ticker": "SAME"},
            {"id": 2, "name": "B", "ticker": "SAME"},
        ]))
        count, errors = validate_mapping(dup)
        assert count == 2
        assert any("Duplicate ticker" in e for e in errors)

    def test_mapping_empty_array(self, tmp_path: Path):
        empty = tmp_path / "empty.json"
        empty.write_text("[]")
        count, errors = validate_mapping(empty)
        assert count == 0
        assert errors == []

    def test_mapping_invalid_entry(self, tmp_path: Path):
        bad = tmp_path / "bad.json"
        bad.write_text(json.dumps([{"id": "not_int_but_ok", "name": "A"}]))
        count, errors = validate_mapping(bad)
        # Missing 'ticker' field should cause a validation error
        assert len(errors) >= 1


# ---------------------------------------------------------------------------
# validate_json (company records)
# ---------------------------------------------------------------------------

class TestValidateJson:
    def test_valid_json(self):
        count, errors = validate_json(DATA_DIR / "sample_company_details.json")
        assert count == 2
        assert errors == []

    def test_missing_json_file(self, tmp_path: Path):
        count, errors = validate_json(tmp_path / "nonexistent.json")
        assert count == 0
        assert len(errors) == 1
        assert "not found" in errors[0].lower()

    def test_invalid_json_syntax(self, tmp_path: Path):
        bad = tmp_path / "bad.json"
        bad.write_text("{not valid json}")
        count, errors = validate_json(bad)
        assert count == 0
        assert any("Invalid JSON" in e for e in errors)

    def test_json_single_object(self, tmp_path: Path):
        """validate_json should accept a single JSON object (not just arrays)."""
        single = tmp_path / "single.json"
        single.write_text(json.dumps({
            "id": 1, "name": "Solo Corp", "ticker": "SOLO",
            "sector": "Tech", "industry": "AI",
        }))
        count, errors = validate_json(single)
        assert count == 1
        assert errors == []

    def test_json_record_missing_required_field(self, tmp_path: Path):
        """A record missing 'name' should produce a validation error."""
        bad = tmp_path / "missing.json"
        bad.write_text(json.dumps([{"id": 1, "ticker": "BAD"}]))
        count, errors = validate_json(bad)
        assert count == 0
        assert len(errors) == 1
        assert "Record 1" in errors[0]

    def test_json_empty_array(self, tmp_path: Path):
        empty = tmp_path / "empty.json"
        empty.write_text("[]")
        count, errors = validate_json(empty)
        assert count == 0
        assert errors == []

    def test_json_partial_valid(self, tmp_path: Path):
        """Mix of valid and invalid records."""
        mixed = tmp_path / "mixed.json"
        mixed.write_text(json.dumps([
            {"id": 1, "name": "Good", "ticker": "GOOD"},
            {"id": "bad_id_type"},  # missing name and ticker
        ]))
        count, errors = validate_json(mixed)
        assert count == 1
        assert len(errors) == 1


# ---------------------------------------------------------------------------
# load_mapping
# ---------------------------------------------------------------------------

class TestLoadMapping:
    def test_load_returns_ticker_entries(self):
        entries = load_mapping(DATA_DIR / "sample_mapping.json")
        assert len(entries) == 2
        assert all(isinstance(e, TickerEntry) for e in entries)
        assert entries[0].ticker == "ACME"
        assert entries[1].ticker == "GLBX"

    def test_load_missing_file(self, tmp_path: Path):
        with pytest.raises(FileNotFoundError):
            load_mapping(tmp_path / "nope.json")


# ---------------------------------------------------------------------------
# Model validation
# ---------------------------------------------------------------------------

class TestTickerEntry:
    def test_valid(self):
        entry = TickerEntry(id=1, name="Acme", ticker="acme")
        assert entry.ticker == "ACME"  # uppercased

    def test_strips_whitespace(self):
        entry = TickerEntry(id=1, name="X", ticker="  foo  ")
        assert entry.ticker == "FOO"

    def test_missing_ticker_raises(self):
        with pytest.raises(Exception):
            TickerEntry(id=1, name="X")


class TestCompanyRecord:
    def test_minimal_valid(self):
        rec = CompanyRecord(id=1, name="Test", ticker="tst")
        assert rec.ticker == "TST"
        assert rec.indices == []
        assert rec.exchanges == []
        assert rec.aggregations == {}

    def test_full_record(self):
        rec = CompanyRecord(
            id=1, name="Test", ticker="TST",
            sector="Tech", industry="Software",
            description="A test company",
            indices=["S&P 500"], exchanges=["NYSE"],
            aggregations={"marketCap": 100},
            insights={"stock_price": []},
            lastUpdated={"companyDetails": "2025-01-01"},
        )
        assert rec.sector == "Tech"
        assert rec.aggregations["marketCap"] == 100

    def test_missing_name_raises(self):
        with pytest.raises(Exception):
            CompanyRecord(id=1, ticker="X")

    def test_missing_id_raises(self):
        with pytest.raises(Exception):
            CompanyRecord(name="X", ticker="X")
