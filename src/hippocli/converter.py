from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, List

import polars as pl

from .logging_config import get_logger

logger = get_logger(__name__)


def read_ndjson(path: Path) -> pl.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"NDJSON file not found: {path}")
    return pl.read_ndjson(path)


def _stringify_nested(df: pl.DataFrame, exclude: Iterable[str] = ()) -> pl.DataFrame:
    nested_types = (pl.List, pl.Struct, pl.Object)

    def _encode(value: object) -> str:
        if value is None:
            return ""
        if isinstance(value, pl.Series):
            value = value.to_list()
        return json.dumps(value)

    for col in df.columns:
        if col in exclude:
            continue
        if isinstance(df[col].dtype, nested_types):
            df = df.with_columns(
                pl.col(col).map_elements(_encode, return_dtype=pl.String)
            )
    return df


def ndjson_to_json_array(input_ndjson: Path, output_json: Path) -> int:
    df = read_ndjson(input_ndjson)
    records: List[dict] = df.to_dicts()
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("Wrote JSON array to %s (%d records)", output_json, len(records))
    return len(records)


def ndjson_to_parquet(input_ndjson: Path, output_parquet: Path) -> int:
    df = read_ndjson(input_ndjson)
    output_parquet.parent.mkdir(parents=True, exist_ok=True)
    df.write_parquet(output_parquet)
    logger.info("Wrote Parquet to %s (%d records)", output_parquet, df.height)
    return df.height


def ndjson_to_csv(input_ndjson: Path, output_csv: Path) -> int:
    df = read_ndjson(input_ndjson)
    df = _stringify_nested(df)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    df.write_csv(output_csv)
    logger.info("Wrote CSV to %s (%d records)", output_csv, df.height)
    return df.height


def ndjson_to_sql(
    input_ndjson: Path, output_sql: Path, table_name: str = "companies"
) -> int:
    df = read_ndjson(input_ndjson)
    df = _stringify_nested(df)
    output_sql.parent.mkdir(parents=True, exist_ok=True)

    def sql_escape(value: str) -> str:
        return value.replace("'", "''")

    columns = df.columns
    with output_sql.open("w", encoding="utf-8") as f:
        f.write(f"DROP TABLE IF EXISTS {table_name};\n")
        f.write(
            f"CREATE TABLE {table_name} (\n"
            "    id INTEGER PRIMARY KEY,\n"
            "    name TEXT NOT NULL,\n"
            "    ticker TEXT,\n"
            "    sector TEXT,\n"
            "    industry TEXT,\n"
            "    description TEXT,\n"
            "    indices_json TEXT,\n"
            "    exchanges_json TEXT,\n"
            "    aggregations_json TEXT,\n"
            "    insights_json TEXT,\n"
            "    lastUpdated_json TEXT\n"
            ");\n\n"
        )
        f.write(f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES\n")
        values_lines = []
        for row in df.to_dicts():
            values: List[str] = []
            for col in columns:
                val = row.get(col)
                if val is None or val == "":
                    values.append("NULL")
                elif isinstance(val, (int, float)):
                    values.append(str(val))
                else:
                    values.append(f"'{sql_escape(str(val))}'")
            values_lines.append(f"  ({', '.join(values)})")
        f.write(",\n".join(values_lines))
        f.write(";\n")

    logger.info("Wrote SQL to %s (%d records)", output_sql, df.height)
    return df.height

