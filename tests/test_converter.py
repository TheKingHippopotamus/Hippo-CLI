from pathlib import Path

from hippocli.converter import (
    ndjson_to_csv,
    ndjson_to_json_array,
    ndjson_to_parquet,
    ndjson_to_sql,
)


def test_converters_roundtrip(tmp_path: Path):
    ndjson = Path(__file__).parent / "data" / "sample_companies.ndjson"

    json_out = tmp_path / "out.json"
    csv_out = tmp_path / "out.csv"
    parquet_out = tmp_path / "out.parquet"
    sql_out = tmp_path / "out.sql"

    count_json = ndjson_to_json_array(ndjson, json_out)
    count_csv = ndjson_to_csv(ndjson, csv_out)
    count_parquet = ndjson_to_parquet(ndjson, parquet_out)
    count_sql = ndjson_to_sql(ndjson, sql_out)

    assert count_json == 2
    assert count_csv == 2
    assert count_parquet == 2
    assert count_sql == 2

    assert json_out.exists()
    assert csv_out.exists()
    assert parquet_out.exists()
    assert sql_out.exists()

