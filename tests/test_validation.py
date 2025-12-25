from pathlib import Path

from hippocli.validator import validate_mapping, validate_ndjson


def test_validate_mapping_ok():
    mapping = Path(__file__).parent / "data" / "sample_mapping.json"
    count, errors = validate_mapping(mapping)
    assert count == 2
    assert errors == []


def test_validate_ndjson_ok():
    ndjson = Path(__file__).parent / "data" / "sample_companies.ndjson"
    count, errors = validate_ndjson(ndjson)
    assert count == 2
    assert errors == []

