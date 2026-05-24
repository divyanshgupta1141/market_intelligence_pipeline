import os
import json
import logging
import re
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import requests
import yfinance as yf

# Reuse database operations
from backend.database import store_analysis_record

logger = logging.getLogger("market_intelligence.pipeline")

DEFAULT_MODEL = "gemini-3.5-flash"
GEMINI_URL_TEMPLATE = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

# 1. Ingestion Layer
def fetch_financial_data(ticker_symbol: str) -> Optional[Dict[str, Any]]:
    """Fetch market metrics and headlines for a ticker using yfinance."""
    logger.info(f"Ingesting data for ticker: {ticker_symbol}")
    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info

        # Extract specific metrics defensively (defaulting to None if missing)
        forward_pe = info.get("forwardPE")
        revenue_growth = info.get("revenueGrowth")
        debt_to_equity = info.get("debtToEquity")

        # Extract top 3 recent news headlines
        headlines = []
        news_items = ticker.news or []
        for item in news_items[:3]:
            title = item.get("title")
            if title:
                headlines.append(title)

        data = {
            "ticker": ticker_symbol,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "forward_pe": forward_pe,
            "revenue_growth": revenue_growth,
            "debt_to_equity": debt_to_equity,
            "news_headlines": headlines
        }

        logger.info(
            f"Successfully fetched data for {ticker_symbol} "
            f"(Forward P/E: {forward_pe}, Revenue Growth: {revenue_growth}, "
            f"Debt/Equity: {debt_to_equity})"
        )
        return data

    except Exception as e:
        logger.error(f"Error fetching data for ticker {ticker_symbol}: {e}", exc_info=True)
        return None

# 2. LLM Reasoning Layer
def analyze_with_llm(ticker_data: Dict[str, Any], api_key: str, model: str = DEFAULT_MODEL) -> Optional[Dict[str, Any]]:
    """Send financial metrics to Gemini API for equity analysis."""
    ticker = ticker_data["ticker"]
    logger.info(f"Running agentic analysis for {ticker}...")

    # Strict prompt instructing LLM to output ONLY structured JSON
    system_prompt = (
        "You are an expert financial analyst evaluating the fundamental strength and macroeconomic "
        "trends of Indian equities based on provided quantitative data and news headlines.\n"
        "Analyze the inputs carefully and output a deterministic, structured JSON object with exactly "
        "the following keys:\n"
        '1. "growth_score": An integer from 1 to 100 representing long-term growth prospects.\n'
        '2. "sentiment": A string representing general market sentiment, restricted to: "Bullish", "Bearish", or "Neutral".\n'
        '3. "key_insight": A string containing a precise, one-sentence summary of the main driver of your analysis.\n\n'
        "Your response MUST be a single JSON object. Do not include any intro, explanation, markdown formatting "
        "(like ```json), or extra text outside the JSON object."
    )

    user_prompt = (
        f"Analyze the following equity data:\n"
        f"Ticker: {ticker_data['ticker']}\n"
        f"Forward P/E: {ticker_data['forward_pe']}\n"
        f"Revenue Growth (YoY): {ticker_data['revenue_growth']}\n"
        f"Debt-to-Equity: {ticker_data['debt_to_equity']}\n"
        f"Recent News Headlines:\n"
    )
    for idx, headline in enumerate(ticker_data["news_headlines"], 1):
        user_prompt += f"{idx}. {headline}\n"

    # Handling dry-run/mock fallback if key is a placeholder or not provided
    if not api_key or api_key.startswith("PLACEHOLDER") or api_key == "YOUR_GEMINI_API_KEY":
        logger.warning(f"Using fallback Mock LLM response for {ticker} (no valid Gemini API key provided).")
        return generate_mock_analysis(ticker_data)

    try:
        url = GEMINI_URL_TEMPLATE.format(model=model, api_key=api_key)
        headers = {"Content-Type": "application/json"}
        
        payload = {
            "systemInstruction": {
                "parts": [{"text": system_prompt}]
            },
            "contents": [
                {"role": "user", "parts": [{"text": user_prompt}]}
            ],
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": 0.1
            }
        }

        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()

        response_data = response.json()
        raw_content = response_data["candidates"][0]["content"]["parts"][0]["text"].strip()
        
        parsed_result = parse_json_safely(raw_content)
        if parsed_result:
            return parsed_result
        else:
            raise ValueError(f"Could not parse valid JSON structure from content: {raw_content}")

    except Exception as e:
        logger.error(f"Error during LLM reasoning layer for {ticker}: {e}. Falling back to mock analysis.", exc_info=True)
        return generate_mock_analysis(ticker_data)


def parse_json_safely(content: str) -> Optional[Dict[str, Any]]:
    """Robust JSON parser that removes Markdown block markers and attempts fallback regex."""
    cleaned = content.strip()
    if cleaned.startswith("```"):
        match = re.search(r"```(?:json)?\s*(.*?)\s*```", cleaned, re.DOTALL)
        if match:
            cleaned = match.group(1)

    try:
        parsed = json.loads(cleaned)
        required_keys = {"growth_score", "sentiment", "key_insight"}
        if all(k in parsed for k in required_keys):
            parsed["growth_score"] = int(parsed["growth_score"])
            parsed["sentiment"] = str(parsed["sentiment"])
            parsed["key_insight"] = str(parsed["key_insight"])
            return parsed
    except Exception as e:
        logger.debug(f"JSON direct parsing failed: {e}. Trying regex fallback...")

    try:
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            parsed = json.loads(match.group(0))
            if all(k in parsed for k in {"growth_score", "sentiment", "key_insight"}):
                parsed["growth_score"] = int(parsed["growth_score"])
                return parsed
    except Exception as e:
        logger.warning(f"Regex JSON fallback failed: {e}")

    return None


def generate_mock_analysis(ticker_data: Dict[str, Any]) -> Dict[str, Any]:
    """Generates deterministic but realistic mock metrics when API key is missing."""
    pe = ticker_data.get("forward_pe") or 25
    debt = ticker_data.get("debt_to_equity") or 50
    rev = ticker_data.get("revenue_growth") or 0.1

    # Base growth score logic
    score = 50
    if rev > 0.15:
        score += 15
    elif rev < 0:
        score -= 15

    if pe < 20:
        score += 10
    elif pe > 50:
        score -= 10

    if debt > 150:
        score -= 10

    score = max(1, min(100, int(score)))

    # Sentiment mapping
    if score >= 65:
        sentiment = "Bullish"
    elif score <= 45:
        sentiment = "Bearish"
    else:
        sentiment = "Neutral"

    return {
        "growth_score": score,
        "sentiment": sentiment,
        "key_insight": f"Mock analysis: {ticker_data['ticker']} shows stable financials with P/E ratio at {pe:.1f} and debt-to-equity at {debt:.1f}%."
    }

# 3. Execution Pipeline wrapper
def run_pipeline_for_watchlist(watchlist: List[str]) -> Dict[str, Any]:
    """Runs data ingestion and LLM analysis for a list of tickers, storing records in the DB."""
    # Load API Key from environment or use fallback placeholder
    api_key = os.getenv("GEMINI_API_KEY", "")
    model = os.getenv("GEMINI_MODEL", DEFAULT_MODEL)
    
    if api_key == "YOUR_GEMINI_API_KEY" or not api_key:
        logger.warning("GEMINI_API_KEY environment variable is not set. Running in DRY-RUN mock mode.")

    success_count = 0
    fail_count = 0
    results = []

    for ticker in watchlist:
        try:
            # 1. Fetch Data
            ticker_data = fetch_financial_data(ticker)
            if not ticker_data:
                fail_count += 1
                continue

            # 2. Run LLM
            analysis = analyze_with_llm(ticker_data, api_key, model=model)
            if not analysis:
                fail_count += 1
                continue

            # 3. Store Database
            stored = store_analysis_record(ticker, ticker_data, analysis)
            if stored:
                success_count += 1
                results.append({
                    "ticker": ticker,
                    "growth_score": analysis["growth_score"],
                    "sentiment": analysis["sentiment"],
                    "key_insight": analysis["key_insight"]
                })
            else:
                fail_count += 1

        except Exception as e:
            logger.error(f"Unexpected error processing ticker {ticker}: {e}", exc_info=True)
            fail_count += 1

    return {
        "status": "complete",
        "success_count": success_count,
        "fail_count": fail_count,
        "results": results
    }
