from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Optional

import yaml
from dotenv import dotenv_values
from pydantic import BaseModel, Field, HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[2]


def _get_output_base_dir() -> Path:
    """Determine the base directory for output storage.
    
    Checks for /app/data first (Docker mount), then /app/output, then REPO_ROOT.
    When using /app/data, paths are relative to it directly (not /app/data/output).
    """
    # Check for /app/data (common Docker mount point)
    docker_data_dir = Path("/app/data")
    if docker_data_dir.exists():
        return docker_data_dir
    
    # Check for /app/output (alternative Docker mount point)
    docker_output_dir = Path("/app/output")
    if docker_output_dir.exists():
        return docker_output_dir
    
    # Fall back to REPO_ROOT / "output" for local development
    return REPO_ROOT / "output"


class PathSettings(BaseModel):
    """Filesystem locations with safe defaults rooted at the repository."""

    base_dir: Path = Field(default=REPO_ROOT)
    data_dir: Path = Field(default_factory=lambda: _get_output_base_dir())
    mapping_path: Path = Field(
        default_factory=lambda: _get_output_base_dir() / "mappings" / "ticker_mapping.json"
    )
    json_output_dir: Path = Field(
        default_factory=lambda: _get_output_base_dir() / "json"
    )
    csv_output_dir: Path = Field(default_factory=lambda: _get_output_base_dir() / "csv")
    parquet_output_dir: Path = Field(default_factory=lambda: _get_output_base_dir() / "parquet")
    sql_output_dir: Path = Field(default_factory=lambda: _get_output_base_dir() / "sql")

    def ensure_output_dirs(self) -> None:
        """Create output directories without touching existing data."""
        self.json_output_dir.mkdir(parents=True, exist_ok=True)
        self.csv_output_dir.mkdir(parents=True, exist_ok=True)
        self.parquet_output_dir.mkdir(parents=True, exist_ok=True)
        self.sql_output_dir.mkdir(parents=True, exist_ok=True)
    
    def get_ticker_paths(self, ticker: str) -> dict[str, Path]:
        """Get all output paths for a specific ticker."""
        ticker_upper = ticker.strip().upper()
        return {
            "json": self.json_output_dir / ticker_upper / f"{ticker_upper}_company_details.json",
            "json_stock_price": self.json_output_dir / ticker_upper / f"{ticker_upper}_stock_price_insights.json",
            "csv": self.csv_output_dir / ticker_upper / f"{ticker_upper}_company_details.csv",
            "csv_stock_price": self.csv_output_dir / ticker_upper / f"{ticker_upper}_stock_price_insights.csv",
            "parquet": self.parquet_output_dir / ticker_upper / f"{ticker_upper}_company_details.parquet",
            "parquet_stock_price": self.parquet_output_dir / ticker_upper / f"{ticker_upper}_stock_price_insights.parquet",
            "sql": self.sql_output_dir / ticker_upper / f"{ticker_upper}_company_details.sql",
            "sql_stock_price": self.sql_output_dir / ticker_upper / f"{ticker_upper}_stock_price_insights.sql",
        }


class AppSettings(BaseSettings):
    """Top-level application settings."""

    model_config = SettingsConfigDict(
        env_prefix="HIPPOCLI_",
        env_file=None,
        env_nested_delimiter="__",
        extra="ignore",
    )

    base_url: HttpUrl = "https://compoundeer.com/api/trpc/company.getByTicker"
    session_token: Optional[str] = None
    request_timeout: float = 30.0
    max_retries: int = 3
    concurrency: int = 4
    user_agent: str = "hippocli/0.1.0"
    paths: PathSettings = Field(default_factory=PathSettings)


def load_settings(config_path: Optional[Path] = None) -> AppSettings:
    """
    Load application settings from YAML (optional) + environment variables.

    Order of precedence: explicit config_path > config/default.yaml > env vars > defaults.
    """
    candidates = []
    if config_path:
        candidates.append(Path(config_path))
    candidates.append(REPO_ROOT / "config" / "default.yaml")

    data: dict[str, Any] = {}
    for path in candidates:
        if path.exists():
            with path.open("r", encoding="utf-8") as f:
                loaded = yaml.safe_load(f) or {}
                if isinstance(loaded, dict):
                    data |= loaded
            break

    # Resolve relative paths in YAML config relative to the output base directory
    output_base = _get_output_base_dir()
    if "paths" in data and isinstance(data["paths"], dict):
        paths_data = data["paths"]
        for key in ["mapping_path", "json_output_dir", "csv_output_dir", "parquet_output_dir", "sql_output_dir"]:
            if key in paths_data:
                path_value = paths_data[key]
                if isinstance(path_value, str):
                    path_obj = Path(path_value)
                    # If relative path, resolve relative to output base
                    if not path_obj.is_absolute():
                        # If path starts with "output/", strip it when using Docker data dir
                        path_str = str(path_obj)
                        if str(output_base) == "/app/data" and path_str.startswith("output/"):
                            # Remove "output/" prefix for Docker mount
                            path_str = path_str[7:]  # len("output/") = 7
                            paths_data[key] = str(output_base / path_str)
                        else:
                            paths_data[key] = str(output_base / path_obj)
                    else:
                        paths_data[key] = path_value

    settings = AppSettings(**data)
    settings.paths.ensure_output_dirs()
    return settings


def load_settings_with_env(
    config_path: Optional[Path] = None,
    env_file: Optional[Path] = None,
) -> AppSettings:
    """
    Load settings, optionally merging an explicit .env file without emitting noisy warnings.
    """
    if env_file and env_file.exists():
        env_data = dotenv_values(env_file)
        for key, val in env_data.items():
            if val is not None:
                os.environ[key] = val
    return load_settings(config_path)

