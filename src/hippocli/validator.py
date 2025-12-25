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


def validate_ndjson(ndjson_path: Path) -> Tuple[int, List[str]]:
    """Validate each line of an NDJSON file as CompanyRecord."""
    errors: List[str] = []
    if not ndjson_path.exists():
        errors.append(f"NDJSON not found: {ndjson_path}")
        return 0, errors

    count = 0
    with ndjson_path.open("r", encoding="utf-8") as f:
        for line_number, line in enumerate(f, start=1):
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
                CompanyRecord.model_validate(payload)
                count += 1
            except ValidationError as exc:
                errors.append(f"Line {line_number}: {exc}")
            except json.JSONDecodeError as exc:
                errors.append(f"Line {line_number}: invalid JSON ({exc})")
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

