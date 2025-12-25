from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class TickerEntry(BaseModel):
    """Represents a single ticker mapping entry."""

    id: int
    name: str
    ticker: str

    @field_validator("ticker")
    @classmethod
    def uppercase_ticker(cls, value: str) -> str:
        return value.strip().upper()


class CompanyRecord(BaseModel):
    """Normalized company record as emitted to NDJSON/JSON."""

    id: int
    name: str
    ticker: str
    sector: Optional[str] = None
    industry: Optional[str] = None
    description: Optional[str] = None
    indices: List[str] = Field(default_factory=list)
    exchanges: List[str] = Field(default_factory=list)
    aggregations: Dict[str, Any] = Field(default_factory=dict)
    insights: Dict[str, Any] = Field(default_factory=dict)
    lastUpdated: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("ticker")
    @classmethod
    def uppercase_ticker(cls, value: str) -> str:
        return value.strip().upper()

