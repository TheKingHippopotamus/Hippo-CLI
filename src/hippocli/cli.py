from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Tuple

import typer
from rich.console import Console
from rich.table import Table

from .analytics import analytics_from_json
from .config import AppSettings, load_settings_with_env
from .converter import (
    json_to_csv,
    json_to_parquet,
    json_to_sql,
    read_json,
)
from .fetcher import fetch_and_write
from .logging_config import setup_logging
from .validator import fix_mapping_ids, load_mapping, validate_mapping, validate_json

console = Console()
app = typer.Typer(
    help="HippoCLI - Financial Data Toolkit",
    epilog="""
╭─ Examples ───────────────────────────────────────────────────────────────╮
│                                                                             
│  Fetch data for a single ticker:                                           
│    $ hippocli fetch --ticker AAPL                                            
│                                                                             
│  Fetch all tickers from mapping file:                                      
│    $ hippocli fetch --mapping output/mappings/ticker_mapping.json           
│                                                                             
│  Validate data:                                                            
│    $ hippocli validate                                                      
│                                                                             
│  Convert to all formats:                                                   
│    $ hippocli convert                                                       
│                                                                             
│  Run analytics for a ticker:                                               
│    $ hippocli analytics AAPL --horizon 90                                   
│                                                                             
│  Using Docker:                                                             
│    $ docker run --rm -v $(pwd)/output:/app/output                   
│          hippocli fetch --ticker AAPL                                        
│    $ docker run --rm -v $(pwd)/output:/app/output hippocli validate          
│    $ docker run -it --rm -v $(pwd)/data:/app/data hippocli shell start                                                 
╰────────────────────────────────────────────────────────────────────────────
""",
)
interactive = typer.Typer(help="Interactive shell for continuous operations")
app.add_typer(interactive, name="shell")


# ---------- Helper Functions ----------


def _load_settings(config_path: Optional[Path], env_file: Optional[Path]) -> AppSettings:
    return load_settings_with_env(config_path, env_file)


def _resolve_mapping_path(mapping_path: Optional[Path], settings: AppSettings) -> Path:
    """Resolve mapping file path, falling back to settings default."""
    return mapping_path or settings.paths.mapping_path


def _resolve_json_file(
    json_path: Optional[Path],
    ticker: Optional[str],
    settings: AppSettings,
) -> Path:
    """Resolve JSON file path, with fallback to old filename format."""
    if json_path:
        return json_path
    
    if not ticker:
        raise ValueError("Either json_path or ticker must be provided")
    
    ticker_paths = settings.paths.get_ticker_paths(ticker)
    json_file = ticker_paths["json"]
    
    # Fallback to old filename if new one doesn't exist
    if not json_file.exists():
        old_json = settings.paths.json_output_dir / ticker.upper() / "company_details.json"
        if old_json.exists():
            return old_json
    
    return json_file


def _ensure_json_exists(json_file: Path, ticker: Optional[str] = None) -> None:
    """Check if JSON file exists, raise error if not."""
    if not json_file.exists():
        error_msg = f"JSON file not found: {json_file}"
        if ticker:
            error_msg = f"JSON file not found for ticker {ticker}: {json_file}"
        console.print(f"[red]Error:[/red] {error_msg}")
        raise typer.Exit(code=1)


def _extract_ticker_from_path(json_path: Path, settings: AppSettings) -> Optional[str]:
    """Try to extract ticker from JSON file path or content."""
    # Try from path: output/json/AAPL/company_details.json -> AAPL
    if json_path.parent.name and json_path.parent.name.isupper():
        return json_path.parent.name
    
    # Try to read ticker from JSON file
    try:
        df = read_json(json_path)
        if df.height > 0 and "ticker" in df.columns:
            return df.select("ticker").item()
    except Exception:
        pass
    
    return None


def _convert_ticker(
    ticker: str,
    settings: AppSettings,
    csv_out: Optional[Path] = None,
    parquet_out: Optional[Path] = None,
    sql_out: Optional[Path] = None,
) -> None:
    """Convert all formats for a specific ticker."""
    ticker_paths = settings.paths.get_ticker_paths(ticker)
    json_in = _resolve_json_file(None, ticker, settings)
    _ensure_json_exists(json_in, ticker)
    
    csv_path = csv_out or ticker_paths["csv"]
    csv_stock_path = ticker_paths["csv_stock_price"]
    parquet_path = parquet_out or ticker_paths["parquet"]
    parquet_stock_path = ticker_paths["parquet_stock_price"]
    sql_path = sql_out or ticker_paths["sql"]
    sql_stock_path = ticker_paths["sql_stock_price"]
    stock_price_json = ticker_paths.get("json_stock_price")
    
    json_to_csv(json_in, csv_path, csv_stock_path, stock_price_json)
    json_to_parquet(json_in, parquet_path, parquet_stock_path, stock_price_json)
    json_to_sql(json_in, sql_path, sql_stock_path, stock_price_table_name="stock_price_insights", stock_price_json=stock_price_json)


def _convert_json_file(
    json_path: Path,
    settings: AppSettings,
    csv_out: Optional[Path] = None,
    parquet_out: Optional[Path] = None,
    sql_out: Optional[Path] = None,
) -> None:
    """Convert a specific JSON file to all formats."""
    _ensure_json_exists(json_path)
    
    ticker = _extract_ticker_from_path(json_path, settings)
    base_dir = json_path.parent
    ticker_upper = ticker.upper() if ticker else ""
    
    # Determine output paths
    csv_out_path = csv_out or (base_dir / f"{ticker_upper}_company_details.csv" if ticker_upper else base_dir / "company_details.csv")
    csv_stock_path = base_dir / f"{ticker_upper}_stock_price_insights.csv" if ticker_upper else base_dir / "stock_price_insights.csv"
    
    parquet_out_path = parquet_out or (base_dir / f"{ticker_upper}_company_details.parquet" if ticker_upper else base_dir / "company_details.parquet")
    parquet_stock_path = base_dir / f"{ticker_upper}_stock_price_insights.parquet" if ticker_upper else base_dir / "stock_price_insights.parquet"
    
    sql_out_path = sql_out or (base_dir / f"{ticker_upper}_company_details.sql" if ticker_upper else base_dir / "company_details.sql")
    sql_stock_path = base_dir / f"{ticker_upper}_stock_price_insights.sql" if ticker_upper else base_dir / "stock_price_insights.sql"
    
    json_to_csv(json_path, csv_out_path, csv_stock_path)
    json_to_parquet(json_path, parquet_out_path, parquet_stock_path)
    json_to_sql(json_path, sql_out_path, sql_stock_path)


def _convert_all_tickers(settings: AppSettings) -> int:
    """Convert all tickers from mapping file. Returns count of converted tickers."""
    mapping = settings.paths.mapping_path
    records = load_mapping(mapping)
    total_converted = 0
    
    for record in records:
        ticker_paths = settings.paths.get_ticker_paths(record.ticker)
        json_in = ticker_paths["json"]
        if json_in.exists():
            stock_price_json = ticker_paths.get("json_stock_price")
            json_to_csv(json_in, ticker_paths["csv"], ticker_paths["csv_stock_price"], stock_price_json)
            json_to_parquet(json_in, ticker_paths["parquet"], ticker_paths["parquet_stock_price"], stock_price_json)
            json_to_sql(json_in, ticker_paths["sql"], ticker_paths["sql_stock_price"], stock_price_table_name="stock_price_insights", stock_price_json=stock_price_json)
            total_converted += 1
    
    return total_converted


def _validate_ticker(
    ticker: str,
    settings: AppSettings,
    mapping_path: Optional[Path] = None,
) -> Tuple[int, List[str]]:
    """Validate a specific ticker. Returns (count, errors)."""
    ticker_paths = settings.paths.get_ticker_paths(ticker)
    json_file = ticker_paths["json"]
    if json_file.exists():
        return validate_json(json_file)
    else:
        return 0, [f"JSON file not found for ticker {ticker}: {json_file}"]


def _validate_all_tickers(
    settings: AppSettings,
    mapping_path: Optional[Path] = None,
) -> Tuple[int, List[str]]:
    """Validate all tickers in mapping. Returns (total_count, errors)."""
    mapping = _resolve_mapping_path(mapping_path, settings)
    records = load_mapping(mapping)
    total_count = 0
    all_errors: List[str] = []
    
    for record in records:
        ticker_paths = settings.paths.get_ticker_paths(record.ticker)
        json_file = ticker_paths["json"]
        if json_file.exists():
            count, errors = validate_json(json_file)
            total_count += count
            all_errors.extend([f"{record.ticker}: {e}" for e in errors])
    
    return total_count, all_errors


def _run_validation(
    settings: AppSettings,
    mapping_path: Optional[Path] = None,
    json_path: Optional[Path] = None,
    ticker: Optional[str] = None,
) -> None:
    """Run validation and display results."""
    mapping = _resolve_mapping_path(mapping_path, settings)
    mapping_count, map_errors = validate_mapping(mapping)
    
    if ticker:
        json_count, json_errors = _validate_ticker(ticker, settings, mapping_path)
    elif json_path:
        json_count, json_errors = validate_json(json_path)
    else:
        json_count, json_errors = _validate_all_tickers(settings, mapping_path)
    
    table = Table(title="Validation Results")
    table.add_column("Item")
    table.add_column("Count/Status")
    table.add_row("Mapping entries", str(mapping_count))
    table.add_row("JSON records", str(json_count))
    console.print(table)
    
    if map_errors or json_errors:
        console.print("[red]Errors detected:[/red]")
        for err in map_errors + json_errors:
            console.print(f"- {err}")
        raise typer.Exit(code=1)
    console.print("[green]Validation passed[/green]")


@app.callback()
def main(
    ctx: typer.Context,
    config: Optional[Path] = typer.Option(
        None, "--config", help="Path to YAML config (overrides defaults)."
    ),
    env_file: Optional[Path] = typer.Option(
        None, "--env-file", help="Optional .env file to load (explicit only)."
    ),
    log_level: str = typer.Option("INFO", "--log-level", help="Logging level"),
) -> None:
    """Initialize shared context."""
    setup_logging(log_level)
    ctx.obj = {"settings": _load_settings(config, env_file)}


@app.command()
def fetch(
    ctx: typer.Context,
    mapping_path: Optional[Path] = typer.Option(
        None, "--mapping", help="Ticker mapping JSON file."
    ),
    output_json: Optional[Path] = typer.Option(
        None, "--out", help="Destination JSON file (optional, defaults to ticker directory)."
    ),
    ticker: Optional[str] = typer.Option(None, "--ticker", help="Fetch a single ticker only."),
    resume: bool = typer.Option(
        False, "--resume", help="Skip existing files (resume mode)."
    ),
) -> None:
    settings: AppSettings = ctx.obj["settings"]
    mapping = _resolve_mapping_path(mapping_path, settings)
    success, errors = fetch_and_write(
        settings=settings,
        mapping_file=mapping,
        output_path=output_json,
        single_ticker=ticker,
        resume=resume,
    )
    console.print(f"[green]Completed[/green]: {success} records, [yellow]{errors} errors[/yellow]")


@app.command()
def validate(
    ctx: typer.Context,
    mapping_path: Optional[Path] = typer.Option(
        None, "--mapping", help="Ticker mapping JSON file."
    ),
    json_path: Optional[Path] = typer.Option(
        None, "--json", help="JSON file to validate (or ticker to validate all its files)."
    ),
    ticker: Optional[str] = typer.Option(
        None, "--ticker", help="Validate all files for a specific ticker."
    ),
) -> None:
    settings: AppSettings = ctx.obj["settings"]
    _run_validation(settings, mapping_path, json_path, ticker)


@app.command()
def fix_mapping(
    ctx: typer.Context,
    mapping_path: Optional[Path] = typer.Option(
        None, "--mapping", help="Ticker mapping JSON file."
    ),
    backup_path: Optional[Path] = typer.Option(
        None, "--backup", help="Optional backup file path."
    ),
) -> None:
    settings: AppSettings = ctx.obj["settings"]
    mapping = _resolve_mapping_path(mapping_path, settings)
    backup = backup_path or (mapping.parent / "ticker_mapping.backup.json")
    total = fix_mapping_ids(mapping, backup)
    console.print(f"[green]Mapping IDs fixed[/green]: {total} records. Backup: {backup}")


@app.command()
def convert(
    ctx: typer.Context,
    json_path: Optional[Path] = typer.Option(None, "--json", help="Source JSON file."),
    ticker: Optional[str] = typer.Option(None, "--ticker", help="Convert all formats for a specific ticker."),
    csv_out: Optional[Path] = typer.Option(None, "--csv-out", help="CSV output path."),
    parquet_out: Optional[Path] = typer.Option(None, "--parquet-out", help="Parquet output path."),
    sql_out: Optional[Path] = typer.Option(None, "--sql-out", help="SQL output path."),
) -> None:
    settings: AppSettings = ctx.obj["settings"]
    
    if ticker:
        _convert_ticker(ticker, settings, csv_out, parquet_out, sql_out)
        console.print(f"[green]Conversion complete[/green] for {ticker}")
    elif json_path:
        _convert_json_file(json_path, settings, csv_out, parquet_out, sql_out)
        console.print("[green]Conversion complete[/green]")
    else:
        total_converted = _convert_all_tickers(settings)
        console.print(f"[green]Conversion complete[/green]: {total_converted} tickers converted")


@app.command()
def analytics(
    ctx: typer.Context,
    ticker: str = typer.Argument(..., help="Ticker to analyze."),
    json_path: Optional[Path] = typer.Option(None, "--json", help="Source JSON file (defaults to ticker directory)."),
    horizon_days: int = typer.Option(63, "--horizon", help="Rolling days to consider."),
) -> None:
    settings: AppSettings = ctx.obj["settings"]
    json_file = json_path or _resolve_json_file(None, ticker, settings)
    _ensure_json_exists(json_file, ticker)
    
    # Get stock price insights path from settings
    ticker_paths = settings.paths.get_ticker_paths(ticker)
    stock_price_json = ticker_paths.get("json_stock_price")
    
    result = analytics_from_json(json_file, ticker=ticker, horizon_days=horizon_days, stock_price_json_path=stock_price_json)
    console.print_json(data=result)


def run() -> None:
    app()


if __name__ == "__main__":
    run()


# ---------- Interactive shell ----------


@interactive.command("start")
def shell(
    ctx: typer.Context,
    config: Optional[Path] = typer.Option(
        None, "--config", help="Path to YAML config (overrides defaults)."
    ),
    env_file: Optional[Path] = typer.Option(
        None, "--env-file", help="Optional .env file to load (explicit only)."
    ),
    log_level: str = typer.Option("INFO", "--log-level", help="Logging level"),
) -> None:
    """
    Interactive menu loop for fetch/convert/validate/analytics without restarting.
    """
    setup_logging(log_level)
    settings: AppSettings = load_settings_with_env(config, env_file)

    def prompt_choice() -> str:
        console.print("\n[bold cyan]Select an action:[/bold cyan]")
        console.print("1) Fetch Data (Download Company Details -  JSON Format -- default )")
        console.print("2) Convert (Convert JSON to CSV, Parquet, SQL,JSONL)")
        console.print("3) Validate (Validate JSON, CSV, Parquet, SQL,JSONL)")
        console.print("4) Analytics (Calculate financial metrics and statistics for a ticker)")
        console.print("5) Fix mapping IDs (Fix mapping IDs in the mapping file -- If Needed)")
        console.print("q) Quit")
        return input("> ").strip().lower()

    def confirm_action(action_description: str) -> bool:
        """Prompt user for y/n confirmation before executing an action."""
        response = input(f"Proceed with {action_description}? [y/N]: ").strip().lower()
        return response == "y"

    while True:
        choice = prompt_choice()
        if choice in ("q", "quit", "exit"):
            console.print("[green]Bye[/green]")
            break

        if choice == "1":
            if not confirm_action("Fetch Data"):
                continue
            ticker = input("Single ticker (blank for all): ").strip() or None
            resume = input("Resume existing files? [y/N]: ").strip().lower() == "y"
            mapping = input(f"Mapping path [{settings.paths.mapping_path}]: ").strip()
            json_out = input("JSON output (blank for default ticker directory): ").strip()
            mapping_path = Path(mapping) if mapping else None
            output_path = Path(json_out) if json_out else None
            fetch_and_write(
                settings=settings,
                mapping_file=_resolve_mapping_path(mapping_path, settings),
                output_path=output_path,
                single_ticker=ticker,
                resume=resume,
            )
            console.print("[green]Fetch done[/green]")

        elif choice == "2":
            if not confirm_action("Convert"):
                continue
            ticker = input("Ticker (blank to convert all): ").strip() or None
            if ticker:
                try:
                    _convert_ticker(ticker, settings)
                    console.print(f"[green]Convert done[/green] for {ticker}")
                except typer.Exit:
                    console.print(f"[red]JSON file not found for {ticker}[/red]")
            else:
                total = _convert_all_tickers(settings)
                console.print(f"[green]Convert done[/green]: {total} tickers converted")

        elif choice == "3":
            if not confirm_action("Validate"):
                continue
            mapping = input(f"Mapping path [{settings.paths.mapping_path}]: ").strip()
            ticker = input("Ticker (blank to validate all): ").strip() or None
            mapping_path = Path(mapping) if mapping else None
            try:
                _run_validation(settings, mapping_path, None, ticker)
            except typer.Exit:
                pass  # Errors already displayed

        elif choice == "4":
            if not confirm_action("Analytics"):
                continue
            ticker = input("Ticker (required): ").strip()
            if not ticker:
                console.print("[red]Ticker is required[/red]")
                continue
            json_file = input("JSON path (blank for default): ").strip()
            horizon = input("Horizon days (default 63): ").strip()
            json_path = Path(json_file) if json_file else None
            horizon_days = int(horizon) if horizon else 63
            try:
                json_file_path = json_path or _resolve_json_file(None, ticker, settings)
                _ensure_json_exists(json_file_path, ticker)
                # Get stock price insights path from settings
                ticker_paths = settings.paths.get_ticker_paths(ticker)
                stock_price_json = ticker_paths.get("json_stock_price")
                result = analytics_from_json(json_file_path, ticker=ticker, horizon_days=horizon_days, stock_price_json_path=stock_price_json)
                console.print_json(data=result)
            except typer.Exit:
                pass  # Error already displayed
        elif choice == "5":
            if not confirm_action("Fix mapping IDs"):
                continue
            mapping = input(f"Mapping path [{settings.paths.mapping_path}]: ").strip()
            backup = input(
                "Backup path (blank for default ticker_mapping.backup.json): "
            ).strip()
            mapping_path = _resolve_mapping_path(Path(mapping) if mapping else None, settings)
            backup_path = (
                Path(backup)
                if backup
                else mapping_path.parent / "ticker_mapping.backup.json"
            )
            total = fix_mapping_ids(mapping_path, backup_path)
            console.print(f"[green]Mapping IDs fixed[/green]: {total} records. Backup: {backup_path}")
        else:
            console.print("[yellow]Invalid choice[/yellow]")

