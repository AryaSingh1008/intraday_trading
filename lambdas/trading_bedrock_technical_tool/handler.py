"""
Bedrock Action Group handler: StockTechnicalAnalysis
Called by the Bedrock Agent when it needs technical indicators for a stock.
Input  API schema: { "symbol": "INFY.NS" }
Output: { tech_score, rsi, macd_signal, bollinger, trend, volume_signal, reasons[] }
"""
import json
import os
import asyncio
import logging

import dynamo_cache
from backend.data.stock_fetcher import StockFetcher
from backend.agents.technical_agent import TechnicalAgent

logger = logging.getLogger(__name__)

_fetcher = None
_agent   = None


def _init():
    global _fetcher, _agent
    if _fetcher is None:
        _fetcher = StockFetcher()
    if _agent is None:
        _agent = TechnicalAgent()


def _parse_parameters(event: dict) -> dict:
    """Extract parameters from Bedrock action group request format."""
    params = {}

    # Bedrock passes parameters as a list of {name, value} dicts
    for p in event.get("parameters", []):
        params[p["name"]] = p["value"]

    # Also handle direct invocation with a flat body (for testing)
    if not params and event.get("requestBody"):
        body = event["requestBody"].get("content", {})
        for media_type, content in body.items():
            for prop, val in content.get("properties", {}).items():
                params[prop] = val.get("value", "")

    return params


async def _analyse(symbol: str) -> dict:
    if not symbol.endswith(".NS"):
        symbol = symbol + ".NS"

    cache_key = f"tech_{symbol}"
    cached    = dynamo_cache.get_cached(cache_key)
    if cached:
        return cached

    stock_data = await _fetcher.get_stock_data(symbol)
    if not stock_data:
        return {"symbol": symbol, "error": "No data available"}

    hist          = stock_data.get("hist")
    current_price = stock_data.get("price", 0)
    volume        = stock_data.get("volume", 0)
    avg_volume    = stock_data.get("avg_volume", volume)

    if hist is None or hist.empty:
        return {"symbol": symbol, "error": "Insufficient historical data"}

    tech_score, reasons = _agent.analyze(hist, current_price, volume, avg_volume)

    result = {
        "symbol":       symbol,
        "tech_score":   round(tech_score, 1),
        "price":        current_price,
        "reasons":      reasons,
        "data_source":  "yfinance",
    }

    dynamo_cache.set_cached(cache_key, result, ttl_seconds=300)
    return result


def handler(event, context):
    _init()

    params  = _parse_parameters(event)
    symbol  = params.get("symbol", "INFY.NS")
    result  = asyncio.run(_analyse(symbol))

    # Bedrock action group expects this exact response format
    return {
        "messageVersion": "1.0",
        "response": {
            "actionGroup":  event.get("actionGroup", "StockTechnicalAnalysis"),
            "function":     event.get("function", "get_technical_analysis"),
            "functionResponse": {
                "responseBody": {
                    "TEXT": {
                        "body": json.dumps(result, default=str)
                    }
                }
            }
        }
    }
