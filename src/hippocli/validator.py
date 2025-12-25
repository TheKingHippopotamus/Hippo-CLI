from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

from pydantic import ValidationError

from .logging_config import get_logger
from .models import CompanyRecord, TickerEntry

logger = get_logger(__name__)


def load_mapping(mapping_path: Path) -> List[TickerEntry]:
    """Load and validate the ticker mapping file."""
    if not mapping_path.exists():
        raise FileNotFoundError(f"Mapping file not found: {mapping_path}")
    data = json.loads(mapping_path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("Mapping file must contain a JSON array")
    return [TickerEntry.model_validate(item) for item in data]


def save_mapping(mapping_path: Path, entries: List[TickerEntry]) -> None:
    """Save ticker mapping entries to file."""
    mapping_path.parent.mkdir(parents=True, exist_ok=True)
    # Convert to dict and ensure id is string (matching file format)
    data = []
    for entry in entries:
        entry_dict = entry.model_dump()
        entry_dict["id"] = str(entry_dict["id"])  # Convert int to string
        data.append(entry_dict)
    with mapping_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    logger.info("Saved %d entries to mapping file: %s", len(entries), mapping_path)


def add_ticker_to_mapping(mapping_path: Path, ticker: str, name: Optional[str] = None) -> TickerEntry:
    """Add a new ticker to the mapping file. Returns the created entry."""
    records = load_mapping(mapping_path) if mapping_path.exists() else []
    
    # Check if ticker already exists
    ticker_upper = ticker.strip().upper()
    for rec in records:
        if rec.ticker == ticker_upper:
            logger.info("Ticker %s already exists in mapping", ticker_upper)
            return rec
    
    # Find next available ID (convert to int for comparison)
    existing_ids = {int(rec.id) for rec in records}
    next_id_int = max(existing_ids, default=0) + 1
    
    # Create new entry (id will be int in model, converted to string when saving)
    new_entry = TickerEntry(
        id=next_id_int,
        name=name or ticker_upper,
        ticker=ticker_upper,
    )
    
    # Add to records and save
    records.append(new_entry)
    save_mapping(mapping_path, records)
    
    logger.info("Added ticker %s to mapping with ID %s", ticker_upper, next_id_int)
    return new_entry


def validate_mapping(mapping_path: Path) -> Tuple[int, List[str]]:
    """Return (count, errors) for mapping validation."""
    errors: List[str] = []
    records: List[TickerEntry] = []
    try:
        records = load_mapping(mapping_path)
    except Exception as exc:  # noqa: BLE001
        errors.append(str(exc))
        return 0, errors

    seen_ids = set()
    seen_tickers = set()
    for rec in records:
        if rec.id in seen_ids:
            errors.append(f"Duplicate id detected: {rec.id}")
        seen_ids.add(rec.id)
        if rec.ticker in seen_tickers:
            errors.append(f"Duplicate ticker detected: {rec.ticker}")
        seen_tickers.add(rec.ticker)

    return len(records), errors


def validate_json(json_path: Path) -> Tuple[int, List[str]]:
    """Validate JSON file (array or single object) as CompanyRecord(s)."""
    errors: List[str] = []
    if not json_path.exists():
        errors.append(f"JSON not found: {json_path}")
        return 0, errors

    count = 0
    try:
        with json_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Handle both array and single object
        if isinstance(data, list):
            records = data
        elif isinstance(data, dict):
            records = [data]
        else:
            errors.append(f"Invalid JSON structure: expected array or object, got {type(data).__name__}")
            return 0, errors
        
        for idx, record in enumerate(records, start=1):
            try:
                CompanyRecord.model_validate(record)
                count += 1
            except ValidationError as exc:
                errors.append(f"Record {idx}: {exc}")
    except json.JSONDecodeError as exc:
        errors.append(f"Invalid JSON: {exc}")
    except Exception as exc:  # noqa: BLE001
        errors.append(f"Error reading file: {exc}")
    
    return count, errors


def validate_all(mapping_path: Path, ndjson_path: Path) -> List[str]:
    """Run mapping and NDJSON validation; return error list."""
    _, map_errors = validate_mapping(mapping_path)
    _, ndjson_errors = validate_ndjson(ndjson_path)
    return map_errors + ndjson_errors


def fix_mapping_ids(mapping_path: Path, backup_path: Optional[Path] = None) -> int:
    """
    Re-sequence mapping IDs to be 1..N in file order.
    Writes a backup if backup_path provided.
    Returns total records.
    """
    if not mapping_path.exists():
        raise FileNotFoundError(f"Mapping file not found: {mapping_path}")

    with mapping_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("Mapping file must be a JSON array")

    total = len(data)
    if backup_path:
        backup_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.info("Backup created at %s", backup_path)

    for idx, entry in enumerate(data, start=1):
        if isinstance(entry, dict):
            entry["id"] = str(idx)

    mapping_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("Re-sequenced %d records in %s", total, mapping_path)
    return total


def iter_errors(errors: Iterable[str]) -> None:
    for err in errors:
        logger.error(err)

