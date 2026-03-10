"""
Lambda handler: EventBridge rate(2m30s) trigger
Pre-warms the options cache for WARM_SYMBOLS and appends IV history.
Replaces the Playwright background loop (which can't run on Lambda).
"""
import json
import os
import asyncio
import logging
from datetime import datetime

import dynamo_cache
from backend.data.options_fetcher import OptionsFetcher
from backend.agents.options_agent import OptionsAgent
from backend.utils import iv_history_store

logger = logging.getLogger(__name__)

WARM_SYMBOLS = ["NIFTY", "BANKNIFTY", "RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK"]

_fetcher = None
_agent   = None


def _init():
    global _fetcher, _agent
    if _fetcher is None:
        _fetcher = OptionsFetcher()
    if _agent is None:
        _agent = OptionsAgent()


async def _refresh_one(symbol: str, append_iv: bool = False) -> dict:
    """Fetch fresh options data, update DynamoDB cache, optionally record IV."""
    try:
        raw = await _fetcher.get_option_chain(symbol)
        if not raw:
            return {"symbol": symbol, "status": "no_data"}

        result  = _agent.analyze(raw)
        cache_key = f"options_{symbol}"
        dynamo_cache.set_cached(cache_key, result, ttl_seconds=150)

        # Append daily IV for percentile calculation
        if append_iv:
            iv_val = result.get("avg_iv") or result.get("atm_iv")
            if iv_val:
                iv_history_store.append_iv(symbol, iv_val)

        return {"symbol": symbol, "status": "ok", "signal": result.get("signal")}
    except Exception as exc:
        logger.warning(f"options_refresh: {symbol} failed: {exc}")
        return {"symbol": symbol, "status": "error", "error": str(exc)}


async def _refresh_all(append_iv: bool = False) -> list:
    tasks = [_refresh_one(sym, append_iv=append_iv) for sym in WARM_SYMBOLS]
    return await asyncio.gather(*tasks)


def handler(event, context):
    _init()

    # EventBridge daily close rule sends {"append_iv": true}
    append_iv = bool(event.get("append_iv", False))

    results = asyncio.run(_refresh_all(append_iv=append_iv))

    ok_count  = sum(1 for r in results if r.get("status") == "ok")
    err_count = len(results) - ok_count

    logger.info(f"options_refresh: refreshed {ok_count}/{len(results)} symbols, "
                f"append_iv={append_iv}")

    return {
        "statusCode": 200,
        "body": json.dumps({
            "refreshed": ok_count,
            "errors":    err_count,
            "append_iv": append_iv,
            "symbols":   results,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }, default=str),
    }
