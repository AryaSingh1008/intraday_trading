"""
Lambda handler: EventBridge trigger
Appends daily IV history for percentile calculation.
Cache pre-warming removed — all analysis uses live data now.
"""
import json
import os
import asyncio
import logging
from datetime import datetime

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


async def _append_iv_one(symbol: str) -> dict:
    """Fetch options data and record IV for percentile calculation."""
    try:
        raw = await _fetcher.get_option_chain(symbol)
        if not raw:
            return {"symbol": symbol, "status": "no_data"}

        result = _agent.analyze(raw)

        iv_val = result.get("avg_iv") or result.get("atm_iv")
        if iv_val:
            iv_history_store.append_iv(symbol, iv_val)

        return {"symbol": symbol, "status": "ok", "signal": result.get("signal")}
    except Exception as exc:
        logger.warning(f"options_refresh: {symbol} failed: {exc}")
        return {"symbol": symbol, "status": "error", "error": str(exc)}


async def _append_iv_all() -> list:
    tasks = [_append_iv_one(sym) for sym in WARM_SYMBOLS]
    return await asyncio.gather(*tasks)


def handler(event, context):
    _init()

    append_iv = bool(event.get("append_iv", False))

    if not append_iv:
        # No cache to warm — only IV history append is useful now
        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Caching disabled — no warmup needed. Use append_iv=true for IV history.",
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }),
        }

    results = asyncio.run(_append_iv_all())

    ok_count  = sum(1 for r in results if r.get("status") == "ok")
    err_count = len(results) - ok_count

    logger.info(f"options_refresh: IV appended for {ok_count}/{len(results)} symbols")

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
