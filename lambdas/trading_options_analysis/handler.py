"""
Lambda handler: GET /api/options?symbol=NIFTY
Wraps OptionsFetcher (curl_cffi path) + OptionsAgent with DynamoDB caching.
"""
import json
import os
import asyncio

import dynamo_cache
from backend.data.options_fetcher import OptionsFetcher
from backend.agents.options_agent import OptionsAgent

_fetcher = None
_agent   = None

# Warm symbols pre-loaded by EventBridge every 2.5 minutes
WARM_SYMBOLS = ["NIFTY", "BANKNIFTY", "RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK"]


def _init():
    global _fetcher, _agent
    if _fetcher is None:
        _fetcher = OptionsFetcher()
    if _agent is None:
        _agent = OptionsAgent()


async def _analyse(symbol: str) -> dict:
    cache_key = f"options_{symbol}"
    cached    = dynamo_cache.get_cached(cache_key)
    if cached:
        return cached

    raw = await _fetcher.get_option_chain(symbol)
    if not raw:
        return {"symbol": symbol, "error": "No options data available"}

    result = _agent.analyze(raw)
    dynamo_cache.set_cached(cache_key, result, ttl_seconds=150)   # 2.5 min — matched to refresh rate
    return result


def handler(event, context):
    _init()

    qs     = event.get("queryStringParameters") or {}
    symbol = (qs.get("symbol") or "NIFTY").upper()

    result = asyncio.run(_analyse(symbol))
    return _json(result)


def _json(data, status: int = 200):
    return {
        "statusCode": status,
        "headers": {
            "Content-Type":                "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(data, default=str),
    }
