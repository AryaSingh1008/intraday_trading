"""
Bedrock Action Group handler: OptionsChainAnalysis
Called by the Bedrock Agent when it needs options chain data.
Input  API schema: { "symbol": "NIFTY" }
Output: { pcr, signal, iv_percentile, max_pain, atm_strike, explanation }
"""
import json
import os
import asyncio
import logging

import dynamo_cache
from backend.data.options_fetcher import OptionsFetcher
from backend.agents.options_agent import OptionsAgent

logger = logging.getLogger(__name__)

_fetcher = None
_agent   = None


def _init():
    global _fetcher, _agent
    if _fetcher is None:
        _fetcher = OptionsFetcher()
    if _agent is None:
        _agent = OptionsAgent()


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


async def _analyse(symbol: str) -> dict:
    # Check trading-cache first (options-refresh Lambda keeps this warm)
    cache_key = f"options_{symbol}"
    cached    = dynamo_cache.get_cached(cache_key)
    if cached:
        return _extract_bedrock_fields(cached, symbol)

    raw = await _fetcher.get_option_chain(symbol)
    if not raw:
        return {"symbol": symbol, "error": "No options data available for this symbol"}

    full_result = _agent.analyze(raw)
    dynamo_cache.set_cached(cache_key, full_result, ttl_seconds=150)
    return _extract_bedrock_fields(full_result, symbol)


def _extract_bedrock_fields(full_result: dict, symbol: str) -> dict:
    """Return only the fields the Bedrock agent needs (keeps response compact)."""
    return {
        "symbol":        symbol,
        "pcr":           full_result.get("pcr"),
        "signal":        full_result.get("signal"),
        "iv_percentile": full_result.get("iv_percentile"),
        "avg_iv":        full_result.get("avg_iv"),
        "max_pain":      full_result.get("max_pain"),
        "atm_strike":    full_result.get("atm_strike"),
        "spot":          full_result.get("spot"),
        "explanation":   full_result.get("explanation", ""),
    }


def handler(event, context):
    _init()

    params = _parse_parameters(event)
    symbol = params.get("symbol", "NIFTY").upper()

    result = asyncio.run(_analyse(symbol))

    return {
        "messageVersion": "1.0",
        "response": {
            "actionGroup":  event.get("actionGroup", "OptionsChainAnalysis"),
            "function":     event.get("function", "get_options_data"),
            "functionResponse": {
                "responseBody": {
                    "TEXT": {
                        "body": json.dumps(result, default=str)
                    }
                }
            }
        }
    }
