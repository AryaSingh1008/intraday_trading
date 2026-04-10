"""
Lambda handler: GET /api/options?symbol=NIFTY
Wraps OptionsFetcher (curl_cffi path) + OptionsAgent — always uses live data.
"""
import json
import os
import asyncio

from backend.data.options_fetcher import OptionsFetcher
from backend.agents.options_agent import OptionsAgent

_fetcher = None
_agent   = None


def _init():
    global _fetcher, _agent
    if _fetcher is None:
        _fetcher = OptionsFetcher()
    if _agent is None:
        _agent = OptionsAgent()


async def _analyse(symbol: str) -> dict:
    raw = await _fetcher.get_option_chain(symbol)
    if not raw:
        return {"symbol": symbol, "error": "No options data available"}

    return _agent.analyze(raw)


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
