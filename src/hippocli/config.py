from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Optional

import yaml
from dotenv import dotenv_values
from pydantic import BaseModel, Field, HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[2]


class PathSettings(BaseModel):
    """Filesystem locations with safe defaults rooted at the repository."""

    base_dir: Path = Field(default=REPO_ROOT)
    data_dir: Path = Field(default_factory=lambda: REPO_ROOT / "data")
    mapping_path: Path = Field(
        default_factory=lambda: REPO_ROOT / "data/mappings/ticker_mapping.json"
    )
    ndjson_output: Path = Field(
        default_factory=lambda: REPO_ROOT / "data/json/company_details.ndjson"
    )
    json_output: Path = Field(
        default_factory=lambda: REPO_ROOT / "data/json/company_details.json"
    )
    csv_output_dir: Path = Field(default_factory=lambda: REPO_ROOT / "data/csv")
    parquet_output: Path = Field(
        default_factory=lambda: REPO_ROOT / "data/parquet/company_details.parquet"
    )
    sql_output: Path = Field(
        default_factory=lambda: REPO_ROOT / "data/sql/company_details.sql"
    )

    def ensure_output_dirs(self) -> None:
        """Create output directories without touching existing data."""
        self.csv_output_dir.mkdir(parents=True, exist_ok=True)
        self.parquet_output.parent.mkdir(parents=True, exist_ok=True)
        self.sql_output.parent.mkdir(parents=True, exist_ok=True)
        self.ndjson_output.parent.mkdir(parents=True, exist_ok=True)
        self.json_output.parent.mkdir(parents=True, exist_ok=True)


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

