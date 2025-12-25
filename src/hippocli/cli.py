from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from .analytics import analytics_from_ndjson
from .config import AppSettings, load_settings_with_env
from .converter import (
    ndjson_to_csv,
    ndjson_to_json_array,
    ndjson_to_parquet,
    ndjson_to_sql,
)
from .fetcher import fetch_and_write
from .logging_config import setup_logging
from .validator import fix_mapping_ids, validate_mapping, validate_ndjson

console = Console()
app = typer.Typer(help="HippoCLI - Financial Data Toolkit")
interactive = typer.Typer(help="Interactive shell for continuous operations")
app.add_typer(interactive, name="shell")


def _load_settings(config_path: Optional[Path], env_file: Optional[Path]) -> AppSettings:
    return load_settings_with_env(config_path, env_file)


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
    output_ndjson: Optional[Path] = typer.Option(
        None, "--out", help="Destination NDJSON file."
    ),
    ticker: Optional[str] = typer.Option(None, "--ticker", help="Fetch a single ticker only."),
    resume: bool = typer.Option(
        False, "--resume", help="Append to existing NDJSON (skip already-written IDs)."
    ),
) -> None:
    settings: AppSettings = ctx.obj["settings"]
    mapping = mapping_path or settings.paths.mapping_path
    ndjson_path = output_ndjson or settings.paths.ndjson_output
    success, errors = fetch_and_write(
        settings=settings,
        mapping_file=mapping,
        output_ndjson=ndjson_path,
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
    ndjson_path: Optional[Path] = typer.Option(
        None, "--ndjson", help="NDJSON file to validate."
    ),
) -> None:
    settings: AppSettings = ctx.obj["settings"]
    mapping = mapping_path or settings.paths.mapping_path
    ndjson = ndjson_path or settings.paths.ndjson_output

    mapping_count, map_errors = validate_mapping(mapping)
    ndjson_count, ndjson_errors = validate_ndjson(ndjson)

    table = Table(title="Validation Results")
    table.add_column("Item")
    table.add_column("Count/Status")
    table.add_row("Mapping entries", str(mapping_count))
    table.add_row("NDJSON records", str(ndjson_count))
    console.print(table)

    if map_errors or ndjson_errors:
        console.print("[red]Errors detected:[/red]")
        for err in map_errors + ndjson_errors:
            console.print(f"- {err}")
        raise typer.Exit(code=1)
    console.print("[green]Validation passed[/green]")


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
    mapping = mapping_path or settings.paths.mapping_path
    backup = backup_path or (mapping.parent / "ticker_mapping.backup.json")
    total = fix_mapping_ids(mapping, backup)
    console.print(f"[green]Mapping IDs fixed[/green]: {total} records. Backup: {backup}")


@app.command()
def convert(
    ctx: typer.Context,
    ndjson_path: Optional[Path] = typer.Option(None, "--ndjson", help="Source NDJSON file."),
    json_out: Optional[Path] = typer.Option(None, "--json-out", help="JSON array output path."),
    csv_out: Optional[Path] = typer.Option(None, "--csv-out", help="CSV output path."),
    parquet_out: Optional[Path] = typer.Option(None, "--parquet-out", help="Parquet output path."),
    sql_out: Optional[Path] = typer.Option(None, "--sql-out", help="SQL output path."),
) -> None:
    settings: AppSettings = ctx.obj["settings"]
    ndjson = ndjson_path or settings.paths.ndjson_output
    json_out = json_out or settings.paths.json_output
    csv_out = csv_out or settings.paths.csv_output_dir / "company_details.csv"
    parquet_out = parquet_out or settings.paths.parquet_output
    sql_out = sql_out or settings.paths.sql_output

    ndjson_to_json_array(ndjson, json_out)
    ndjson_to_csv(ndjson, csv_out)
    ndjson_to_parquet(ndjson, parquet_out)
    ndjson_to_sql(ndjson, sql_out)
    console.print("[green]Conversion complete[/green]")


@app.command()
def analytics(
    ctx: typer.Context,
    ticker: str = typer.Argument(..., help="Ticker to analyze."),
    ndjson_path: Optional[Path] = typer.Option(None, "--ndjson", help="Source NDJSON file."),
    horizon_days: int = typer.Option(63, "--horizon", help="Rolling days to consider."),
) -> None:
    settings: AppSettings = ctx.obj["settings"]
    ndjson = ndjson_path or settings.paths.ndjson_output
    result = analytics_from_ndjson(ndjson, ticker=ticker, horizon_days=horizon_days)
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
        console.print("1) Fetch")
        console.print("2) Convert")
        console.print("3) Validate")
        console.print("4) Analytics")
        console.print("5) Fix mapping IDs")
        console.print("q) Quit")
        return input("> ").strip().lower()

    while True:
        choice = prompt_choice()
        if choice in ("q", "quit", "exit"):
            console.print("[green]Bye[/green]")
            break

        if choice == "1":
            ticker = input("Single ticker (blank for all): ").strip() or None
            resume = input("Resume existing NDJSON? [y/N]: ").strip().lower() == "y"
            mapping = input(f"Mapping path [{settings.paths.mapping_path}]: ").strip()
            ndjson_out = input(f"NDJSON out [{settings.paths.ndjson_output}]: ").strip()
            mapping_path = Path(mapping) if mapping else settings.paths.mapping_path
            ndjson_path = Path(ndjson_out) if ndjson_out else settings.paths.ndjson_output
            fetch_and_write(
                settings=settings,
                mapping_file=mapping_path,
                output_ndjson=ndjson_path,
                single_ticker=ticker,
                resume=resume,
            )
            console.print("[green]Fetch done[/green]")

        elif choice == "2":
            ndjson_in = input(f"NDJSON in [{settings.paths.ndjson_output}]: ").strip()
            json_out = input(f"JSON out [{settings.paths.json_output}]: ").strip()
            csv_out = input(
                f"CSV out [{settings.paths.csv_output_dir / 'company_details.csv'}]: "
            ).strip()
            parquet_out = input(f"Parquet out [{settings.paths.parquet_output}]: ").strip()
            sql_out = input(f"SQL out [{settings.paths.sql_output}]: ").strip()
            ndjson_path = Path(ndjson_in) if ndjson_in else settings.paths.ndjson_output
            ndjson_to_json_array(
                ndjson_path, Path(json_out) if json_out else settings.paths.json_output
            )
            ndjson_to_csv(
                ndjson_path,
                Path(csv_out) if csv_out else settings.paths.csv_output_dir / "company_details.csv",
            )
            ndjson_to_parquet(
                ndjson_path, Path(parquet_out) if parquet_out else settings.paths.parquet_output
            )
            ndjson_to_sql(ndjson_path, Path(sql_out) if sql_out else settings.paths.sql_output)
            console.print("[green]Convert done[/green]")

        elif choice == "3":
            mapping = input(f"Mapping path [{settings.paths.mapping_path}]: ").strip()
            ndjson = input(f"NDJSON path [{settings.paths.ndjson_output}]: ").strip()
            mapping_path = Path(mapping) if mapping else settings.paths.mapping_path
            ndjson_path = Path(ndjson) if ndjson else settings.paths.ndjson_output
            mapping_count, map_errors = validate_mapping(mapping_path)
            ndjson_count, ndjson_errors = validate_ndjson(ndjson_path)
            console.print(f"Mapping entries: {mapping_count}")
            console.print(f"NDJSON records: {ndjson_count}")
            if map_errors or ndjson_errors:
                console.print("[red]Errors detected:[/red]")
                for err in map_errors + ndjson_errors:
                    console.print(f"- {err}")
            else:
                console.print("[green]Validation passed[/green]")

        elif choice == "4":
            ticker = input("Ticker (required): ").strip()
            if not ticker:
                console.print("[red]Ticker is required[/red]")
                continue
            ndjson = input(f"NDJSON path [{settings.paths.ndjson_output}]: ").strip()
            horizon = input("Horizon days (default 63): ").strip()
            ndjson_path = Path(ndjson) if ndjson else settings.paths.ndjson_output
            horizon_days = int(horizon) if horizon else 63
            result = analytics_from_ndjson(ndjson_path, ticker=ticker, horizon_days=horizon_days)
            console.print_json(data=result)
        elif choice == "5":
            mapping = input(f"Mapping path [{settings.paths.mapping_path}]: ").strip()
            backup = input(
                "Backup path (blank for default ticker_mapping.backup.json): "
            ).strip()
            mapping_path = Path(mapping) if mapping else settings.paths.mapping_path
            backup_path = (
                Path(backup)
                if backup
                else mapping_path.parent / "ticker_mapping.backup.json"
            )
            total = fix_mapping_ids(mapping_path, backup_path)
            console.print(f"[green]Mapping IDs fixed[/green]: {total} records. Backup: {backup_path}")
        else:
            console.print("[yellow]Invalid choice[/yellow]")

