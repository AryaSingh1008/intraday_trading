"""
Bedrock Action Group handler: NewsSentimentAnalysis
Called by the Bedrock Agent when it needs news sentiment for a stock.
Input  API schema: { "symbol": "INFY.NS", "company_name": "Infosys" }
Output: { sentiment_score, sentiment_label, top_headlines[], reasons[] }
"""
import json
import os
import asyncio
import logging

import dynamo_cache
from backend.agents.sentiment_agent import SentimentAgent

logger = logging.getLogger(__name__)

_agent = None


def _init():
    global _agent
    if _agent is None:
        _agent = SentimentAgent()


def _parse_parameters(event: dict) -> dict:
    """Extract parameters from Bedrock action group request format."""
    params = {}
    for p in event.get("parameters", []):
        params[p["name"]] = p["value"]

    if not params and event.get("requestBody"):
        body = event["requestBody"].get("content", {})
        for media_type, content in body.items():
            for prop, val in content.get("properties", {}).items():
                params[prop] = val.get("value", "")

    return params


async def _analyse(symbol: str, company_name: str) -> dict:
    cache_key = f"news_{symbol}"
    cached    = dynamo_cache.get_cached(cache_key)
    if cached:
        return cached

    try:
        score, label, headlines, reasons = await _agent.get_sentiment_score(
            symbol, company_name
        )
    except TypeError:
        # If agent returns 3-tuple without reasons
        result_raw = await _agent.get_sentiment_score(symbol, company_name)
        if isinstance(result_raw, (list, tuple)) and len(result_raw) >= 3:
            score, label, headlines = result_raw[:3]
            reasons = []
        else:
            return {"symbol": symbol, "error": "Unexpected sentiment response"}

    result = {
        "symbol":          symbol,
        "company_name":    company_name,
        "sentiment_score": round(float(score), 1) if score is not None else 0,
        "sentiment_label": label or "NEUTRAL",
        "top_headlines":   headlines[:5] if headlines else [],
        "reasons":         reasons[:5]   if reasons   else [],
    }

    dynamo_cache.set_cached(cache_key, result, ttl_seconds=300)
    return result


def handler(event, context):
    _init()

    params       = _parse_parameters(event)
    symbol       = params.get("symbol", "INFY.NS")
    company_name = params.get("company_name", symbol.replace(".NS", ""))

    result = asyncio.run(_analyse(symbol, company_name))

    return {
        "messageVersion": "1.0",
        "response": {
            "actionGroup":  event.get("actionGroup", "NewsSentimentAnalysis"),
            "function":     event.get("function", "get_news_sentiment"),
            "functionResponse": {
                "responseBody": {
                    "TEXT": {
                        "body": json.dumps(result, default=str)
                    }
                }
            }
        }
    }
