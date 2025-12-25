from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, List, Tuple

import polars as pl

from .logging_config import get_logger

logger = get_logger(__name__)


def read_json(path: Path) -> pl.DataFrame:
    """Read JSON file (array or single object) and convert to DataFrame."""
    if not path.exists():
        raise FileNotFoundError(f"JSON file not found: {path}")
    
    # Use polars read_json which handles both array and object
    try:
        df = pl.read_json(path)
        # If it's a single object, wrap it in a list
        if df.height == 0:
            with path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                # Single object - create DataFrame from dict
                return pl.DataFrame([data])
            elif isinstance(data, list):
                return pl.DataFrame(data)
        return df
    except Exception:
        # Fallback: read as JSON and convert
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        
        if isinstance(data, list):
            records = data
        elif isinstance(data, dict):
            records = [data]
        else:
            raise ValueError(f"Unexpected JSON structure in {path}")
        
        if not records:
            return pl.DataFrame()
        
        return pl.DataFrame(records)


def read_json_with_stock_price(company_json: Path, stock_price_json: Path | None = None) -> Tuple[pl.DataFrame, pl.DataFrame]:
    """
    Read company JSON and optionally stock price JSON.
    If stock_price_json is provided and exists, read it separately.
    Otherwise, try to extract stock_price from company_json.
    """
    company_df = read_json(company_json)
    
    # Try to read stock price from separate file if provided
    if stock_price_json and stock_price_json.exists():
        stock_price_df = read_json(stock_price_json)
        return company_df, stock_price_df
    
    # Otherwise, stock_price will be extracted from company_df in _split_dataframes
    return company_df, pl.DataFrame()


def _flatten_dict_column(df: pl.DataFrame, column_name: str, prefix: str = "") -> pl.DataFrame:
    """Flatten a dictionary/struct column into separate columns."""
    if column_name not in df.columns:
        return df
    
    # Check if column is a Struct type in polars
    use_unnest = isinstance(df[column_name].dtype, pl.Struct) and not prefix
    
    if use_unnest:
        # Use polars struct unnest to flatten (faster, but no prefix control)
        return df.unnest(column_name)
    
    # Manually extract as a dict to have full control over column naming (especially for prefix)
    flattened_data = []
    base_columns = [col for col in df.columns if col != column_name]
    
    for row in df.to_dicts():
        base_row = {col: row.get(col) for col in base_columns}
        nested_data = row.get(column_name, {})
        
        # Handle polars Struct type - convert to dict
        if isinstance(df[column_name].dtype, pl.Struct):
            # For Struct, we need to access it differently
            try:
                # Polars Struct can be accessed as dict-like
                if hasattr(nested_data, 'to_dict'):
                    nested_data = nested_data.to_dict()
                elif hasattr(nested_data, '__getitem__'):
                    # Try to convert struct to dict manually
                    struct_dict = {}
                    for field in df[column_name].dtype.fields:
                        try:
                            struct_dict[field.name] = nested_data[field.name]
                        except (KeyError, TypeError):
                            pass
                    nested_data = struct_dict if struct_dict else {}
            except Exception:
                nested_data = {}
        elif isinstance(nested_data, str):
            # Try to parse as JSON string
            try:
                nested_data = json.loads(nested_data)
            except (json.JSONDecodeError, TypeError):
                nested_data = {}
        
        if isinstance(nested_data, dict):
            # Flatten into the base row with optional prefix
            for key, value in nested_data.items():
                col_name = f"{prefix}_{key}" if prefix else key
                base_row[col_name] = value
        elif nested_data is not None:
            # Try other conversion methods
            try:
                if not isinstance(nested_data, (list, tuple)):
                    # Try to convert to dict
                    nested_data = dict(nested_data) if hasattr(nested_data, '__iter__') and not isinstance(nested_data, str) else {}
                    if isinstance(nested_data, dict):
                        for key, value in nested_data.items():
                            col_name = f"{prefix}_{key}" if prefix else key
                            base_row[col_name] = value
            except Exception:
                pass
        flattened_data.append(base_row)
    
    return pl.DataFrame(flattened_data)


def _flatten_aggregations(df: pl.DataFrame) -> pl.DataFrame:
    """Flatten the aggregations and lastUpdated columns into separate columns."""
    # First flatten aggregations
    df = _flatten_dict_column(df, "aggregations")
    
    # Then flatten lastUpdated with prefix
    df = _flatten_dict_column(df, "lastUpdated", prefix="last_updated")
    
    return df


def _split_dataframes(df: pl.DataFrame, stock_price_df: pl.DataFrame | None = None) -> Tuple[pl.DataFrame, pl.DataFrame]:
    """
    Split DataFrame into two:
    1. Company details (without insights and stock_price)
    2. Stock price and insights data
    
    If stock_price_df is provided, use it directly. Otherwise, extract from df.
    """
    # Company details: all columns except insights
    company_cols = [col for col in df.columns if col != "insights"]
    company_df = df.select(company_cols)
    
    # If stock_price_df is already provided, use it
    if stock_price_df is not None and stock_price_df.height > 0:
        return company_df, stock_price_df
    
    # Otherwise, extract stock price from insights column
    stock_price_records = []
    
    for row in df.to_dicts():
        company_id = row.get("id")
        ticker = row.get("ticker")
        insights = row.get("insights", {})
        
        if isinstance(insights, dict):
            stock_price_data = insights.get("stock_price", [])
            if isinstance(stock_price_data, list):
                for price_point in stock_price_data:
                    if isinstance(price_point, dict):
                        stock_price_records.append({
                            "company_id": company_id,
                            "ticker": ticker,
                            "ts": price_point.get("ts"),
                            "value": price_point.get("value"),
                            "interval": price_point.get("interval"),
                            "valueUnit": price_point.get("valueUnit"),
                        })
    
    stock_price_df = pl.DataFrame(stock_price_records) if stock_price_records else pl.DataFrame(
        schema={"company_id": pl.Int64, "ticker": pl.String, "ts": pl.Int64, "value": pl.Float64, "interval": pl.Int64, "valueUnit": pl.String}
    )
    
    return company_df, stock_price_df


def _stringify_nested(df: pl.DataFrame, exclude: Iterable[str] = ()) -> pl.DataFrame:
    """Stringify nested columns (lists, structs) for CSV/SQL output."""
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


def _move_description_to_end(df: pl.DataFrame) -> pl.DataFrame:
    """Move description column to the end of the DataFrame."""
    if "description" not in df.columns:
        return df
    
    # Get all columns except description
    other_columns = [col for col in df.columns if col != "description"]
    # Reorder: all other columns first, then description
    new_column_order = other_columns + ["description"]
    return df.select(new_column_order)


def json_to_json_array(input_json: Path, output_json: Path) -> int:
    """Convert JSON to JSON array (essentially just copy/format)."""
    df = read_json(input_json)
    records: List[dict] = df.to_dicts()
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("Wrote JSON array to %s (%d records)", output_json, len(records))
    return len(records)


def json_to_parquet(
    input_json: Path, 
    output_parquet: Path, 
    stock_price_parquet: Path | None = None,
    stock_price_json: Path | None = None
) -> Tuple[int, int]:
    """
    Convert JSON to Parquet format.
    Creates two files: company_details.parquet and stock_price_insights.parquet
    """
    # Try to read stock price from separate JSON file if provided
    stock_price_df_from_file = None
    if stock_price_json and stock_price_json.exists():
        stock_price_df_from_file = read_json(stock_price_json)
    
    df = read_json(input_json)
    
    # Flatten aggregations
    df = _flatten_aggregations(df)
    
    # Split into company details and stock price data
    company_df, stock_price_df = _split_dataframes(df, stock_price_df_from_file)
    
    # Move description to the end
    company_df = _move_description_to_end(company_df)
    
    # Write company details
    output_parquet.parent.mkdir(parents=True, exist_ok=True)
    company_df.write_parquet(output_parquet)
    logger.info("Wrote company Parquet to %s (%d records)", output_parquet, company_df.height)
    
    # Write stock price data if provided
    stock_price_count = 0
    if stock_price_parquet:
        stock_price_parquet.parent.mkdir(parents=True, exist_ok=True)
        stock_price_df.write_parquet(stock_price_parquet)
        stock_price_count = stock_price_df.height
        logger.info("Wrote stock price Parquet to %s (%d records)", stock_price_parquet, stock_price_count)
    
    return company_df.height, stock_price_count


def json_to_csv(
    input_json: Path, 
    output_csv: Path, 
    stock_price_csv: Path | None = None,
    stock_price_json: Path | None = None
) -> Tuple[int, int]:
    """
    Convert JSON to CSV format.
    Creates two files: company_details.csv and stock_price_insights.csv
    """
    # Try to read stock price from separate JSON file if provided
    stock_price_df_from_file = None
    if stock_price_json and stock_price_json.exists():
        stock_price_df_from_file = read_json(stock_price_json)
    
    df = read_json(input_json)
    
    # Flatten aggregations
    df = _flatten_aggregations(df)
    
    # Split into company details and stock price data
    company_df, stock_price_df = _split_dataframes(df, stock_price_df_from_file)
    
    # Stringify any remaining nested columns (like indices, exchanges)
    company_df = _stringify_nested(company_df, exclude=[])
    
    # Move description to the end
    company_df = _move_description_to_end(company_df)
    
    # Write company details
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    company_df.write_csv(output_csv)
    logger.info("Wrote company CSV to %s (%d records)", output_csv, company_df.height)
    
    # Write stock price data if provided
    stock_price_count = 0
    if stock_price_csv:
        stock_price_csv.parent.mkdir(parents=True, exist_ok=True)
        stock_price_df.write_csv(stock_price_csv)
        stock_price_count = stock_price_df.height
        logger.info("Wrote stock price CSV to %s (%d records)", stock_price_csv, stock_price_count)
    
    return company_df.height, stock_price_count


def json_to_sql(
    input_json: Path, 
    output_sql: Path, 
    stock_price_sql: Path | None = None,
    table_name: str = "companies",
    stock_price_table_name: str = "stock_price_insights",
    stock_price_json: Path | None = None
) -> Tuple[int, int]:
    """
    Convert JSON to SQL format.
    Creates two files: company_details.sql and stock_price_insights.sql
    """
    # Try to read stock price from separate JSON file if provided
    stock_price_df_from_file = None
    if stock_price_json and stock_price_json.exists():
        stock_price_df_from_file = read_json(stock_price_json)
    
    df = read_json(input_json)
    
    # Flatten aggregations
    df = _flatten_aggregations(df)
    
    # Split into company details and stock price data
    company_df, stock_price_df = _split_dataframes(df, stock_price_df_from_file)
    
    # Stringify nested columns for company data
    company_df = _stringify_nested(company_df, exclude=[])
    
    # Move description to the end
    company_df = _move_description_to_end(company_df)
    
    output_sql.parent.mkdir(parents=True, exist_ok=True)
    
    def sql_escape(value: str) -> str:
        return value.replace("'", "''")
    
    def _get_sql_type(col_name: str, dtype: pl.DataType) -> str:
        """Determine SQL type for a column."""
        if isinstance(dtype, pl.Int64) or isinstance(dtype, pl.Int32):
            return "INTEGER"
        elif isinstance(dtype, pl.Float64) or isinstance(dtype, pl.Float32):
            return "REAL"
        elif isinstance(dtype, pl.Boolean):
            return "INTEGER"
        else:
            return "TEXT"
    
    # Write company details SQL
    columns = company_df.columns
    with output_sql.open("w", encoding="utf-8") as f:
        f.write(f"DROP TABLE IF EXISTS {table_name};\n")
        f.write(f"CREATE TABLE {table_name} (\n")
        
        # Generate column definitions
        col_defs = []
        for col in columns:
            dtype = company_df[col].dtype
            sql_type = _get_sql_type(col, dtype)
            if col == "id":
                col_defs.append(f"    {col} {sql_type} PRIMARY KEY")
            else:
                col_defs.append(f"    {col} {sql_type}")
        
        f.write(",\n".join(col_defs))
        f.write("\n);\n\n")
        
        if company_df.height > 0:
            f.write(f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES\n")
            values_lines = []
            for row in company_df.to_dicts():
                values: List[str] = []
                for col in columns:
                    val = row.get(col)
                    if val is None or val == "":
                        values.append("NULL")
                    elif isinstance(val, (int, float, bool)):
                        values.append(str(val))
                    else:
                        values.append(f"'{sql_escape(str(val))}'")
                values_lines.append(f"  ({', '.join(values)})")
            f.write(",\n".join(values_lines))
            f.write(";\n")
    
    logger.info("Wrote company SQL to %s (%d records)", output_sql, company_df.height)
    
    # Write stock price SQL if provided
    stock_price_count = 0
    if stock_price_sql and stock_price_df.height > 0:
        stock_price_sql.parent.mkdir(parents=True, exist_ok=True)
        with stock_price_sql.open("w", encoding="utf-8") as f:
            f.write(f"DROP TABLE IF EXISTS {stock_price_table_name};\n")
            f.write(f"CREATE TABLE {stock_price_table_name} (\n")
            f.write("    company_id INTEGER,\n")
            f.write("    ticker TEXT,\n")
            f.write("    ts INTEGER,\n")
            f.write("    value REAL,\n")
            f.write("    interval INTEGER,\n")
            f.write("    valueUnit TEXT,\n")
            f.write("    FOREIGN KEY (company_id) REFERENCES companies(id)\n")
            f.write(");\n\n")
            
            f.write(f"INSERT INTO {stock_price_table_name} (company_id, ticker, ts, value, interval, valueUnit) VALUES\n")
            values_lines = []
            for row in stock_price_df.to_dicts():
                company_id = row.get("company_id", "NULL")
                ticker = row.get("ticker", "")
                ts = row.get("ts", "NULL")
                value = row.get("value", "NULL")
                interval = row.get("interval", "NULL")
                value_unit = row.get("valueUnit", "")
                
                values = [
                    str(company_id) if company_id != "NULL" else "NULL",
                    f"'{sql_escape(str(ticker))}'",
                    str(ts) if ts != "NULL" else "NULL",
                    str(value) if value != "NULL" else "NULL",
                    str(interval) if interval != "NULL" else "NULL",
                    f"'{sql_escape(str(value_unit))}'"
                ]
                values_lines.append(f"  ({', '.join(values)})")
            f.write(",\n".join(values_lines))
            f.write(";\n")
        
        stock_price_count = stock_price_df.height
        logger.info("Wrote stock price SQL to %s (%d records)", stock_price_sql, stock_price_count)
    
    return company_df.height, stock_price_count

