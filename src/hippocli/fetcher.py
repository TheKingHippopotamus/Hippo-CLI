from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, List, Optional

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from .config import AppSettings
from .logging_config import get_logger
from .models import CompanyRecord, TickerEntry
from .validator import load_mapping

logger = get_logger(__name__)


class FetchError(RuntimeError):
    """Raised when the upstream API cannot be read."""


def build_headers(settings: AppSettings) -> dict[str, str]:
    headers = {
        "accept": "*/*",
        "user-agent": settings.user_agent,
        "content-type": "application/json",
        "accept-language": "en-US,en;q=0.8",
        "cache-control": "no-cache",
        "pragma": "no-cache",
        "dnt": "1",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "x-trpc-source": "nextjs-react",
    }
    if settings.session_token:
        headers["cookie"] = f"compoundeer.session-token={settings.session_token}"
    return headers


@retry(
    reraise=True,
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type((httpx.HTTPError, FetchError)),
)
def _fetch_company_json(
    client: httpx.Client, settings: AppSettings, ticker: str
) -> dict:
    payload = {"0": {"json": ticker}}
    response = client.get(
        str(settings.base_url),
        params={"batch": 1, "input": json.dumps(payload)},
    )
    response.raise_for_status()
    data = response.json()
    try:
        return data[0]["result"]["data"]["json"]["company"]
    except Exception as exc:  # noqa: BLE001
        raise FetchError(f"Unexpected response shape for {ticker}") from exc


def to_company_record(raw_company: dict, mapping: TickerEntry) -> CompanyRecord:
    base = raw_company or {}
    return CompanyRecord(
        id=mapping.id,
        name=base.get("name", mapping.name),
        ticker=base.get("ticker", mapping.ticker),
        sector=base.get("sector"),
        industry=base.get("industry"),
        description=base.get("description"),
        indices=base.get("indices") or [],
        exchanges=base.get("exchanges") or [],
        aggregations=(base.get("aggregations") or {}),
        insights=(base.get("insights") or {}),
        lastUpdated=(base.get("lastUpdated") or {}),
    )


def iter_targets(
    mapping_file: Path, single_ticker: Optional[str] = None
) -> List[TickerEntry]:
    records = load_mapping(mapping_file)
    if single_ticker:
        target = single_ticker.strip().upper()
        filtered = [rec for rec in records if rec.ticker == target]
        if not filtered:
            logger.warning("Ticker %s not found in mapping; creating ad-hoc entry.", target)
            return [TickerEntry(id=0, name=target, ticker=target)]
        return filtered
    return records


def fetch_and_write(
    settings: AppSettings,
    mapping_file: Path,
    output_ndjson: Path,
    single_ticker: Optional[str] = None,
    resume: bool = False,
) -> tuple[int, int]:
    """
    Fetch company data and write NDJSON.

    Returns (success_count, error_count).
    """
    targets = iter_targets(mapping_file, single_ticker)
    output_ndjson.parent.mkdir(parents=True, exist_ok=True)

    processed_ids: set[int] = set()
    if resume and output_ndjson.exists():
        with output_ndjson.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    rec = json.loads(line)
                    processed_ids.add(int(rec.get("id", -1)))
                except json.JSONDecodeError:
                    continue
        logger.info("Resume enabled: skipping %d already-written records", len(processed_ids))
    elif output_ndjson.exists() and not resume:
        raise FileExistsError(
            f"Output file already exists: {output_ndjson}. Use --resume or delete first."
        )

    success = 0
    errors = 0

    headers = build_headers(settings)
    with httpx.Client(timeout=settings.request_timeout, headers=headers) as client, output_ndjson.open(
        "a", encoding="utf-8"
    ) as out:
        for mapping in targets:
            if mapping.id in processed_ids:
                continue
            try:
                raw = _fetch_company_json(client, settings, mapping.ticker)
                record = to_company_record(raw, mapping)
                out.write(json.dumps(record.model_dump()) + "\n")
                success += 1
            except Exception as exc:  # noqa: BLE001
                logger.error("Failed to fetch %s (%s): %s", mapping.name, mapping.ticker, exc)
                errors += 1

    logger.info("Fetch complete. Success: %s, Errors: %s", success, errors)
    return success, errors

