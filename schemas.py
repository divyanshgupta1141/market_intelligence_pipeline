"""
Pydantic v2 Extraction Models and Contract Boundaries for Market Intelligence Pipeline.

This module enforces strict schema invariants, deterministic parsing, and boundary
validation on raw market feeds and LLM reasoning payloads.
"""

import re
from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict, ValidationError

# Regex for uppercase alphabetic tickers with optional standard exchange suffixes (e.g., 'AAPL', 'TCS.NS', 'M&M.NS')
TICKER_REGEX = re.compile(r"^[A-Z&]+([._-][A-Z&]+)*$")


class FinancialExtraction(BaseModel):
    """
    Pydantic v2 Extraction Model for Market Intelligence Ingestion.

    Enforces strict boundary contracts on raw market payloads:
      - Validates ticker symbol as uppercase alphabetic with optional exchange delimiters.
      - Enforces positive values (gt=0) on financial amounts (e.g. market_cap, current_price, volume).
      - Tolerates missing/optional fundamental ratios while ensuring correct typing.
    """
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="ignore"
    )

    ticker: str = Field(
        ...,
        description="Uppercase equity ticker symbol (e.g. 'AAPL', 'TCS.NS', 'RELIANCE.NS')"
    )
    timestamp: Optional[str] = Field(
        default=None,
        description="ISO 8601 UTC timestamp of data ingestion"
    )
    market_cap: Optional[float] = Field(
        default=None,
        gt=0,
        description="Market capitalization in base currency (must be strictly positive > 0)"
    )
    forward_pe: Optional[float] = Field(
        default=None,
        description="Forward Price-to-Earnings ratio"
    )
    revenue_growth: Optional[float] = Field(
        default=None,
        description="Year-over-Year revenue growth rate"
    )
    debt_to_equity: Optional[float] = Field(
        default=None,
        description="Debt-to-Equity ratio"
    )
    current_price: Optional[float] = Field(
        default=None,
        gt=0,
        description="Current market price per share (must be strictly positive > 0)"
    )
    volume: Optional[int] = Field(
        default=None,
        gt=0,
        description="Daily trading volume (must be strictly positive > 0)"
    )
    news_headlines: List[str] = Field(
        default_factory=list,
        description="Recent news headlines for qualitative analysis"
    )

    @field_validator("ticker")
    @classmethod
    def validate_ticker(cls, v: str) -> str:
        if not isinstance(v, str) or not v.strip():
            raise ValueError("Ticker symbol cannot be empty.")
        clean_v = v.strip()
        if not TICKER_REGEX.match(clean_v):
            raise ValueError(
                f"Malformed ticker symbol '{v}'. Tickers must be uppercase alphabetic characters "
                f"with optional standard separators (e.g., 'AAPL', 'TCS.NS', 'RELIANCE.NS')."
            )
        return clean_v


class LLMAnalysisResult(BaseModel):
    """
    Pydantic v2 Schema for structured Gemini LLM reasoning output.

    Enforces deterministic compliance on agentic equity evaluation.
    """
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="ignore"
    )

    growth_score: int = Field(
        ...,
        ge=1,
        le=100,
        description="Deterministic long-term growth score between 1 and 100"
    )
    sentiment: Literal["Bullish", "Bearish", "Neutral"] = Field(
        ...,
        description="Market sentiment classification"
    )
    key_insight: str = Field(
        ...,
        min_length=5,
        description="Concise analytical insight summarizing valuation and fundamentals"
    )


class AssetAnalysisRecord(BaseModel):
    """
    Unified database entity model combining raw extraction and reasoning output.
    """
    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="ignore"
    )

    id: Optional[int] = Field(default=None, description="Primary key identifier")
    ticker: str = Field(..., description="Equity ticker symbol")
    date: str = Field(..., description="Date of analysis recording")
    growth_score: int = Field(..., ge=1, le=100)
    sentiment: Literal["Bullish", "Bearish", "Neutral"]
    forward_pe: Optional[float] = None
    revenue_growth: Optional[float] = None
    debt_to_equity: Optional[float] = None
    market_cap: Optional[float] = Field(default=None, gt=0)
    headlines: List[str] = Field(default_factory=list)
    key_insight: Optional[str] = None
    raw_analysis: Optional[str] = None


class TickerRequest(BaseModel):
    """Request model for watchlist addition."""
    model_config = ConfigDict(str_strip_whitespace=True)
    ticker: str = Field(..., min_length=1)

    @field_validator("ticker")
    @classmethod
    def validate_ticker(cls, v: str) -> str:
        if not isinstance(v, str) or not v.strip():
            raise ValueError("Ticker symbol cannot be empty.")
        clean_v = v.strip().upper()
        if not TICKER_REGEX.match(clean_v):
            raise ValueError(f"Malformed ticker symbol '{v}'.")
        return clean_v


class PipelineRunRequest(BaseModel):
    """Request model for manual pipeline execution."""
    tickers: Optional[List[str]] = None


# Backward compatibility and semantic aliases
FinancialDataPayload = FinancialExtraction
MarketDataExtraction = FinancialExtraction
ExtractionModel = FinancialExtraction
AnalysisOutput = LLMAnalysisResult


def validate_extraction_payload(payload: Dict[str, Any]) -> FinancialExtraction:
    """Validate raw payload against the Pydantic v2 FinancialExtraction boundary."""
    return FinancialExtraction.model_validate(payload)
