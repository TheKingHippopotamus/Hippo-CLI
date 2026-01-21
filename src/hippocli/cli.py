from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
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


def _get_project_status(settings: AppSettings) -> Dict[str, any]:
    """Get current project status including tickers, files, etc."""
    mapping_path = settings.paths.mapping_path
    status: Dict[str, any] = {
        "mapping_exists": mapping_path.exists(),
        "mapping_count": 0,
        "tickers_with_data": 0,
        "tickers_with_all_formats": 0,
        "ticker_details": [],
    }
    
    if status["mapping_exists"]:
        try:
            records = load_mapping(mapping_path)
            status["mapping_count"] = len(records)
            
            for record in records:
                ticker_paths = settings.paths.get_ticker_paths(record.ticker)
                has_json = ticker_paths["json"].exists()
                has_csv = ticker_paths["csv"].exists()
                has_parquet = ticker_paths["parquet"].exists()
                has_sql = ticker_paths["sql"].exists()
                
                if has_json:
                    status["tickers_with_data"] += 1
                
                if has_json and has_csv and has_parquet and has_sql:
                    status["tickers_with_all_formats"] += 1
                
                status["ticker_details"].append({
                    "ticker": record.ticker,
                    "name": record.name,
                    "has_json": has_json,
                    "has_csv": has_csv,
                    "has_parquet": has_parquet,
                    "has_sql": has_sql,
                })
        except Exception:
            pass
    
    return status


def _display_status(settings: AppSettings) -> None:
    """Display project status in a formatted table."""
    status = _get_project_status(settings)
    
    console.print("\n[bold cyan]Project Status[/bold cyan]")
    console.print("─" * 60)
    
    # Summary table
    summary_table = Table(show_header=False, box=None, padding=(0, 2))
    summary_table.add_row("[bold]Mapping file:[/bold]", 
                          "[green]✓ Found[/green]" if status["mapping_exists"] else "[red]✗ Not found[/red]")
    summary_table.add_row("[bold]Tickers in mapping:[/bold]", str(status["mapping_count"]))
    summary_table.add_row("[bold]Tickers with data:[/bold]", str(status["tickers_with_data"]))
    summary_table.add_row("[bold]Tickers with all formats:[/bold]", str(status["tickers_with_all_formats"]))
    console.print(summary_table)
    
    # Detailed ticker table
    if status["ticker_details"]:
        ticker_table = Table(title="Ticker Details")
        ticker_table.add_column("Ticker", style="cyan")
        ticker_table.add_column("Name", style="white")
        ticker_table.add_column("JSON", justify="center")
        ticker_table.add_column("CSV", justify="center")
        ticker_table.add_column("Parquet", justify="center")
        ticker_table.add_column("SQL", justify="center")
        
        for detail in status["ticker_details"]:
            ticker_table.add_row(
                detail["ticker"],
                detail["name"],
                "[green]✓[/green]" if detail["has_json"] else "[red]✗[/red]",
                "[green]✓[/green]" if detail["has_csv"] else "[red]✗[/red]",
                "[green]✓[/green]" if detail["has_parquet"] else "[red]✗[/red]",
                "[green]✓[/green]" if detail["has_sql"] else "[red]✗[/red]",
            )
        console.print(ticker_table)


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
    ticker: Optional[str] = typer.Argument(None, help="Ticker symbol to fetch (optional, fetches all if not specified)."),
    mapping_path: Optional[Path] = typer.Option(
        None, "--mapping", help="Ticker mapping JSON file."
    ),
    output_json: Optional[Path] = typer.Option(
        None, "--out", help="Destination JSON file (optional, defaults to ticker directory)."
    ),
    resume: bool = typer.Option(
        False, "--resume", help="Skip existing files (resume mode)."
    ),
) -> None:
    """Fetch financial data for ticker(s)."""
    settings: AppSettings = ctx.obj["settings"]
    mapping = _resolve_mapping_path(mapping_path, settings)
    
    if ticker:
        ticker = ticker.upper().strip()
        console.print(f"[cyan]Fetching data for {ticker}...[/cyan]")
    else:
        console.print("[cyan]Fetching data for all tickers...[/cyan]")
    
    success, errors = fetch_and_write(
        settings=settings,
        mapping_file=mapping,
        output_path=output_json,
        single_ticker=ticker,
        resume=resume,
    )
    console.print(f"[green]✓ Completed:[/green] {success} records, [yellow]{errors} errors[/yellow]")


@app.command()
def validate(
    ctx: typer.Context,
    ticker: Optional[str] = typer.Argument(None, help="Ticker symbol to validate (optional, validates all if not specified)."),
    mapping_path: Optional[Path] = typer.Option(
        None, "--mapping", help="Ticker mapping JSON file."
    ),
    json_path: Optional[Path] = typer.Option(
        None, "--json", help="JSON file to validate."
    ),
) -> None:
    """Validate data integrity for ticker(s)."""
    settings: AppSettings = ctx.obj["settings"]
    
    if ticker:
        ticker = ticker.upper().strip()
        console.print(f"[cyan]Validating {ticker}...[/cyan]")
    else:
        console.print("[cyan]Validating all tickers...[/cyan]")
    
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
    ticker: Optional[str] = typer.Argument(None, help="Ticker symbol to convert (optional, converts all if not specified)."),
    json_path: Optional[Path] = typer.Option(None, "--json", help="Source JSON file."),
    csv_out: Optional[Path] = typer.Option(None, "--csv-out", help="CSV output path."),
    parquet_out: Optional[Path] = typer.Option(None, "--parquet-out", help="Parquet output path."),
    sql_out: Optional[Path] = typer.Option(None, "--sql-out", help="SQL output path."),
) -> None:
    """Convert JSON data to CSV, Parquet, and SQL formats."""
    settings: AppSettings = ctx.obj["settings"]
    
    if ticker:
        ticker = ticker.upper().strip()
        console.print(f"[cyan]Converting {ticker}...[/cyan]")
        _convert_ticker(ticker, settings, csv_out, parquet_out, sql_out)
        console.print(f"[green]✓ Conversion complete for {ticker}[/green]")
    elif json_path:
        console.print(f"[cyan]Converting {json_path}...[/cyan]")
        _convert_json_file(json_path, settings, csv_out, parquet_out, sql_out)
        console.print("[green]✓ Conversion complete[/green]")
    else:
        console.print("[cyan]Converting all tickers...[/cyan]")
        total_converted = _convert_all_tickers(settings)
        console.print(f"[green]✓ Conversion complete:[/green] {total_converted} tickers converted")


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


@app.command()
def status(
    ctx: typer.Context,
) -> None:
    """Display project status including tickers, files, and data availability."""
    settings: AppSettings = ctx.obj["settings"]
    _display_status(settings)


@app.command()
def list(
    ctx: typer.Context,
) -> None:
    """List all tickers with their status."""
    settings: AppSettings = ctx.obj["settings"]
    status = _get_project_status(settings)
    
    if not status["ticker_details"]:
        console.print("[yellow]No tickers found in mapping file[/yellow]")
        return
    
    table = Table(title="All Tickers")
    table.add_column("Ticker", style="cyan")
    table.add_column("Name", style="white")
    table.add_column("Status", style="green")
    
    for detail in status["ticker_details"]:
        formats = []
        if detail["has_json"]:
            formats.append("JSON")
        if detail["has_csv"]:
            formats.append("CSV")
        if detail["has_parquet"]:
            formats.append("Parquet")
        if detail["has_sql"]:
            formats.append("SQL")
        
        status_text = ", ".join(formats) if formats else "[red]No data[/red]"
        if len(formats) == 4:
            status_text = "[green]Complete[/green]"
        
        table.add_row(detail["ticker"], detail["name"], status_text)
    
    console.print(table)


@app.command()
def setup(
    ctx: typer.Context,
    ticker: Optional[str] = typer.Argument(None, help="Ticker symbol to set up (optional)."),
) -> None:
    """Initial setup: create mapping file and fetch first ticker."""
    settings: AppSettings = ctx.obj["settings"]
    mapping = settings.paths.mapping_path
    
    # Ensure mapping file exists
    if not mapping.exists():
        mapping.parent.mkdir(parents=True, exist_ok=True)
        mapping.write_text("[]", encoding="utf-8")
        console.print(f"[green]Created mapping file:[/green] {mapping}")
    
    if ticker:
        from .validator import add_ticker_to_mapping
        add_ticker_to_mapping(mapping, ticker)
        console.print(f"[green]Added ticker {ticker} to mapping[/green]")
        
        # Fetch data for the ticker
        console.print(f"[cyan]Fetching data for {ticker}...[/cyan]")
        success, errors = fetch_and_write(
            settings=settings,
            mapping_file=mapping,
            single_ticker=ticker,
            resume=False,
        )
        console.print(f"[green]Setup complete:[/green] {success} records fetched, [yellow]{errors} errors[/yellow]")
    else:
        console.print(f"[green]Mapping file ready:[/green] {mapping}")
        console.print("[yellow]Tip:[/yellow] Use 'hippocli setup TICKER' to add and fetch a ticker")


@app.command()
def update(
    ctx: typer.Context,
    ticker: Optional[str] = typer.Argument(None, help="Ticker to update (optional, updates all if not specified)."),
    skip_validate: bool = typer.Option(False, "--skip-validate", help="Skip validation step."),
) -> None:
    """Full pipeline: fetch + convert + validate for ticker(s)."""
    settings: AppSettings = ctx.obj["settings"]
    mapping = _resolve_mapping_path(None, settings)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # Step 1: Fetch
        task1 = progress.add_task("[cyan]Fetching data...", total=None)
        success, errors = fetch_and_write(
            settings=settings,
            mapping_file=mapping,
            single_ticker=ticker,
            resume=False,
        )
        progress.update(task1, completed=True)
        console.print(f"[green]✓ Fetched:[/green] {success} records, [yellow]{errors} errors[/yellow]")
        
        # Step 2: Convert
        task2 = progress.add_task("[cyan]Converting formats...", total=None)
        if ticker:
            try:
                _convert_ticker(ticker, settings)
                converted_count = 1
            except typer.Exit:
                converted_count = 0
        else:
            converted_count = _convert_all_tickers(settings)
        progress.update(task2, completed=True)
        console.print(f"[green]✓ Converted:[/green] {converted_count} ticker(s)")
        
        # Step 3: Validate
        if not skip_validate:
            task3 = progress.add_task("[cyan]Validating data...", total=None)
            try:
                _run_validation(settings, None, None, ticker)
                progress.update(task3, completed=True)
                console.print("[green]✓ Validation passed[/green]")
            except typer.Exit:
                progress.update(task3, completed=True)
                console.print("[yellow]⚠ Validation found errors[/yellow]")
        
    console.print("[bold green]Update complete![/bold green]")


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

    def show_status_summary() -> None:
        """Display quick status summary."""
        status = _get_project_status(settings)
        console.print(Panel(
            f"[bold]Tickers:[/bold] {status['mapping_count']} | "
            f"[bold]With Data:[/bold] {status['tickers_with_data']} | "
            f"[bold]Complete:[/bold] {status['tickers_with_all_formats']}",
            title="[cyan]Project Status[/cyan]",
            border_style="cyan",
        ))

    def prompt_choice() -> str:
        console.print("\n[bold cyan]╭─ HippoCLI Interactive Menu ────────────────────────────────────────╮[/bold cyan]")
        show_status_summary()
        console.print("\n[bold cyan]Workflows:[/bold cyan]")
        console.print("  [yellow]1[/yellow]) Quick Start (Setup new ticker: fetch + convert + validate)")
        console.print("  [yellow]2[/yellow]) Update All (Fetch + convert + validate all tickers)")
        console.print("  [yellow]3[/yellow]) Full Pipeline (Complete workflow for specific ticker)")
        console.print("\n[bold cyan]Actions:[/bold cyan]")
        console.print("  [yellow]4[/yellow]) Fetch Data")
        console.print("  [yellow]5[/yellow]) Convert Formats")
        console.print("  [yellow]6[/yellow]) Validate Data")
        console.print("  [yellow]7[/yellow]) Run Analytics")
        console.print("\n[bold cyan]Utilities:[/bold cyan]")
        console.print("  [yellow]8[/yellow]) View Status")
        console.print("  [yellow]9[/yellow]) List Tickers")
        console.print("  [yellow]f[/yellow]) Fix Mapping IDs")
        console.print("\n  [yellow]q[/yellow]) Quit")
        console.print("[bold cyan]╰───────────────────────────────────────────────────────────────────╯[/bold cyan]")
        return input("\n[bold]Select:[/bold] ").strip().lower()

    def confirm_action(action_description: str) -> bool:
        """Prompt user for y/n confirmation before executing an action."""
        response = input(f"\n[bold yellow]Proceed with {action_description}?[/bold yellow] [y/N]: ").strip().lower()
        return response == "y"
    
    def prompt_ticker(prompt_text: str = "Enter ticker", allow_blank: bool = True) -> Optional[str]:
        """Prompt for ticker input."""
        if allow_blank:
            ticker = input(f"{prompt_text} (blank for all): ").strip() or None
        else:
            ticker = input(f"{prompt_text}: ").strip()
            if not ticker:
                console.print("[red]Ticker is required[/red]")
                return None
        return ticker.upper() if ticker else None

    while True:
        choice = prompt_choice()
        if choice in ("q", "quit", "exit"):
            console.print("\n[green]Goodbye![/green]")
            break

        # Workflows
        if choice == "1":  # Quick Start
            if not confirm_action("Quick Start (setup new ticker)"):
                continue
            ticker = prompt_ticker("Enter ticker to set up", allow_blank=False)
            if not ticker:
                continue
            
            from .validator import add_ticker_to_mapping
            mapping = settings.paths.mapping_path
            add_ticker_to_mapping(mapping, ticker)
            console.print(f"[green]✓ Added {ticker} to mapping[/green]")
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                # Fetch
                task1 = progress.add_task(f"[cyan]Fetching {ticker}...", total=None)
                success, errors = fetch_and_write(
                    settings=settings,
                    mapping_file=mapping,
                    single_ticker=ticker,
                    resume=False,
                )
                progress.update(task1, completed=True)
                
                # Convert
                task2 = progress.add_task(f"[cyan]Converting {ticker}...", total=None)
                try:
                    _convert_ticker(ticker, settings)
                    progress.update(task2, completed=True)
                except typer.Exit:
                    progress.update(task2, completed=True)
                    console.print(f"[red]Conversion failed for {ticker}[/red]")
                    continue
                
                # Validate
                task3 = progress.add_task(f"[cyan]Validating {ticker}...", total=None)
                try:
                    _run_validation(settings, None, None, ticker)
                    progress.update(task3, completed=True)
                except typer.Exit:
                    progress.update(task3, completed=True)
            
            console.print(f"[bold green]✓ Quick Start complete for {ticker}![/bold green]")

        elif choice == "2":  # Update All
            if not confirm_action("Update All (fetch + convert + validate all tickers)"):
                continue
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task1 = progress.add_task("[cyan]Fetching all tickers...", total=None)
                success, errors = fetch_and_write(
                    settings=settings,
                    mapping_file=_resolve_mapping_path(None, settings),
                    single_ticker=None,
                    resume=False,
                )
                progress.update(task1, completed=True)
                console.print(f"[green]✓ Fetched:[/green] {success} records, [yellow]{errors} errors[/yellow]")
                
                task2 = progress.add_task("[cyan]Converting all tickers...", total=None)
                total = _convert_all_tickers(settings)
                progress.update(task2, completed=True)
                console.print(f"[green]✓ Converted:[/green] {total} tickers")
                
                task3 = progress.add_task("[cyan]Validating all tickers...", total=None)
                try:
                    _run_validation(settings, None, None, None)
                    progress.update(task3, completed=True)
                    console.print("[green]✓ Validation passed[/green]")
                except typer.Exit:
                    progress.update(task3, completed=True)
                    console.print("[yellow]⚠ Validation found errors[/yellow]")
            
            console.print("[bold green]✓ Update All complete![/bold green]")

        elif choice == "3":  # Full Pipeline
            if not confirm_action("Full Pipeline (complete workflow)"):
                continue
            ticker = prompt_ticker("Enter ticker", allow_blank=False)
            if not ticker:
                continue
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task1 = progress.add_task(f"[cyan]Fetching {ticker}...", total=None)
                success, errors = fetch_and_write(
                    settings=settings,
                    mapping_file=_resolve_mapping_path(None, settings),
                    single_ticker=ticker,
                    resume=False,
                )
                progress.update(task1, completed=True)
                console.print(f"[green]✓ Fetched:[/green] {success} records, [yellow]{errors} errors[/yellow]")
                
                task2 = progress.add_task(f"[cyan]Converting {ticker}...", total=None)
                try:
                    _convert_ticker(ticker, settings)
                    progress.update(task2, completed=True)
                    console.print(f"[green]✓ Converted {ticker}[/green]")
                except typer.Exit:
                    progress.update(task2, completed=True)
                    console.print(f"[red]Conversion failed for {ticker}[/red]")
                    continue
                
                task3 = progress.add_task(f"[cyan]Validating {ticker}...", total=None)
                try:
                    _run_validation(settings, None, None, ticker)
                    progress.update(task3, completed=True)
                    console.print("[green]✓ Validation passed[/green]")
                except typer.Exit:
                    progress.update(task3, completed=True)
                    console.print("[yellow]⚠ Validation found errors[/yellow]")
            
            console.print(f"[bold green]✓ Full Pipeline complete for {ticker}![/bold green]")

        # Individual Actions
        elif choice == "4":  # Fetch
            if not confirm_action("Fetch Data"):
                continue
            ticker = prompt_ticker("Enter ticker")
            resume = input("Resume existing files? [y/N]: ").strip().lower() == "y"
            success, errors = fetch_and_write(
                settings=settings,
                mapping_file=_resolve_mapping_path(None, settings),
                output_path=None,
                single_ticker=ticker,
                resume=resume,
            )
            console.print(f"[green]✓ Fetch complete:[/green] {success} records, [yellow]{errors} errors[/yellow]")

        elif choice == "5":  # Convert
            if not confirm_action("Convert Formats"):
                continue
            ticker = prompt_ticker("Enter ticker")
            if ticker:
                try:
                    _convert_ticker(ticker, settings)
                    console.print(f"[green]✓ Convert complete for {ticker}[/green]")
                except typer.Exit:
                    console.print(f"[red]JSON file not found for {ticker}[/red]")
            else:
                total = _convert_all_tickers(settings)
                console.print(f"[green]✓ Convert complete:[/green] {total} tickers converted")

        elif choice == "6":  # Validate
            if not confirm_action("Validate Data"):
                continue
            ticker = prompt_ticker("Enter ticker")
            try:
                _run_validation(settings, None, None, ticker)
            except typer.Exit:
                pass  # Errors already displayed

        elif choice == "7":  # Analytics
            if not confirm_action("Run Analytics"):
                continue
            ticker = prompt_ticker("Enter ticker", allow_blank=False)
            if not ticker:
                continue
            horizon_input = input("Horizon days (default 63): ").strip()
            horizon_days = int(horizon_input) if horizon_input else 63
            try:
                json_file_path = _resolve_json_file(None, ticker, settings)
                _ensure_json_exists(json_file_path, ticker)
                ticker_paths = settings.paths.get_ticker_paths(ticker)
                stock_price_json = ticker_paths.get("json_stock_price")
                result = analytics_from_json(
                    json_file_path, 
                    ticker=ticker, 
                    horizon_days=horizon_days, 
                    stock_price_json_path=stock_price_json
                )
                console.print_json(data=result)
            except typer.Exit:
                pass  # Error already displayed

        # Utilities
        elif choice == "8":  # Status
            _display_status(settings)
            input("\nPress Enter to continue...")

        elif choice == "9":  # List
            status = _get_project_status(settings)
            if not status["ticker_details"]:
                console.print("[yellow]No tickers found[/yellow]")
            else:
                table = Table(title="All Tickers")
                table.add_column("Ticker", style="cyan")
                table.add_column("Name", style="white")
                table.add_column("Status", style="green")
                for detail in status["ticker_details"]:
                    formats = []
                    if detail["has_json"]:
                        formats.append("JSON")
                    if detail["has_csv"]:
                        formats.append("CSV")
                    if detail["has_parquet"]:
                        formats.append("Parquet")
                    if detail["has_sql"]:
                        formats.append("SQL")
                    status_text = ", ".join(formats) if formats else "[red]No data[/red]"
                    if len(formats) == 4:
                        status_text = "[green]Complete[/green]"
                    table.add_row(detail["ticker"], detail["name"], status_text)
                console.print(table)
            input("\nPress Enter to continue...")

        elif choice == "f":  # Fix Mapping
            if not confirm_action("Fix Mapping IDs"):
                continue
            mapping_path = _resolve_mapping_path(None, settings)
            backup_path = mapping_path.parent / "ticker_mapping.backup.json"
            total = fix_mapping_ids(mapping_path, backup_path)
            console.print(f"[green]✓ Mapping IDs fixed:[/green] {total} records. Backup: {backup_path}")

        else:
            console.print("[yellow]Invalid choice. Please try again.[/yellow]")

