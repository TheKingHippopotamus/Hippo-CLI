from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, List, Optional

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from .config import AppSettings
from .logging_config import get_logger
from .models import CompanyRecord, TickerEntry
from .validator import add_ticker_to_mapping, load_mapping

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
    mapping_file: Path, single_ticker: Optional[str] = None, auto_add: bool = True
) -> List[TickerEntry]:
    # Handle case where mapping file doesn't exist yet
    if not mapping_file.exists():
        if single_ticker:
            # If we have a single ticker, create the mapping file and add it
            target = single_ticker.strip().upper()
            logger.info("Mapping file not found; creating it and adding ticker %s.", target)
            new_entry = add_ticker_to_mapping(mapping_file, target)
            return [new_entry]
        else:
            # If no single ticker, we need the mapping file to exist
            raise FileNotFoundError(
                f"Mapping file not found: {mapping_file}. "
                "Please create it first or specify a single ticker to auto-create it."
            )
    
    records = load_mapping(mapping_file)
    if single_ticker:
        target = single_ticker.strip().upper()
        filtered = [rec for rec in records if rec.ticker == target]
        if not filtered:
            if auto_add:
                logger.info("Ticker %s not found in mapping; adding to mapping file.", target)
                new_entry = add_ticker_to_mapping(mapping_file, target)
                return [new_entry]
            else:
                logger.warning("Ticker %s not found in mapping; creating ad-hoc entry.", target)
                return [TickerEntry(id=0, name=target, ticker=target)]
        return filtered
    return records


def fetch_and_write(
    settings: AppSettings,
    mapping_file: Path,
    output_path: Optional[Path] = None,
    single_ticker: Optional[str] = None,
    resume: bool = False,
) -> tuple[int, int]:
    """
    Fetch company data and write JSON (one file per ticker in ticker directory).

    Returns (success_count, error_count).
    """
    targets = iter_targets(mapping_file, single_ticker)
    
    success = 0
    errors = 0
    headers = build_headers(settings)
    
    with httpx.Client(timeout=settings.request_timeout, headers=headers) as client:
        for mapping in targets:
            ticker = mapping.ticker
            ticker_paths = settings.paths.get_ticker_paths(ticker)
            output_json = output_path or ticker_paths["json"]
            
            # Create ticker directory
            output_json.parent.mkdir(parents=True, exist_ok=True)
            
            # Check if file exists (for resume logic)
            if output_json.exists():
                if resume:
                    logger.info("File exists for %s, skipping (resume mode)", ticker)
                    success += 1
                    continue
                else:
                    logger.warning("File exists for %s, overwriting", ticker)
            
            try:
                raw = _fetch_company_json(client, settings, ticker)
                record = to_company_record(raw, mapping)
                
                # Split into company details and stock price data
                record_dict = record.model_dump()
                
                # Company details (without insights)
                company_details = {k: v for k, v in record_dict.items() if k != "insights"}
                
                # Stock price and insights data
                insights_data = record_dict.get("insights", {})
                stock_price_data = insights_data.get("stock_price", [])
                
                # Determine output paths
                ticker_paths = settings.paths.get_ticker_paths(ticker)
                company_json = output_path or ticker_paths["json"]
                stock_price_json = ticker_paths["json_stock_price"]
                
                # Write company details JSON
                company_json.parent.mkdir(parents=True, exist_ok=True)
                with company_json.open("w", encoding="utf-8") as f:
                    json.dump([company_details], f, indent=2, ensure_ascii=False)
                
                logger.info("Saved %s company details to %s", ticker, company_json)
                
                # Write stock price insights JSON
                stock_price_json.parent.mkdir(parents=True, exist_ok=True)
                stock_price_records = []
                for price_point in stock_price_data:
                    if isinstance(price_point, dict):
                        stock_price_records.append({
                            "company_id": record.id,
                            "ticker": record.ticker,
                            "ts": price_point.get("ts"),
                            "value": price_point.get("value"),
                            "interval": price_point.get("interval"),
                            "valueUnit": price_point.get("valueUnit"),
                        })
                
                with stock_price_json.open("w", encoding="utf-8") as f:
                    json.dump(stock_price_records, f, indent=2, ensure_ascii=False)
                
                logger.info("Saved %s stock price data to %s (%d records)", ticker, stock_price_json, len(stock_price_records))
                success += 1
            except Exception as exc:  # noqa: BLE001
                logger.error("Failed to fetch %s (%s): %s", mapping.name, ticker, exc)
                errors += 1

    logger.info("Fetch complete. Success: %s, Errors: %s", success, errors)
    return success, errors

