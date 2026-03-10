"""
Lambda handler: GET /api/stocks, GET /api/stock/{symbol}, GET /api/stocks/list
Wraps StockFetcher + SignalAgent with DynamoDB caching.
"""
import json
import os
import asyncio

import dynamo_cache
from backend.data.stock_fetcher import StockFetcher
from backend.agents.signal_agent import SignalAgent

INDIAN_STOCKS = {
    "RELIANCE.NS": "Reliance Industries", "TCS.NS": "Tata Consultancy Services",
    "INFY.NS": "Infosys", "HDFCBANK.NS": "HDFC Bank", "ICICIBANK.NS": "ICICI Bank",
    "WIPRO.NS": "Wipro", "TATAMOTORS.NS": "Tata Motors", "SBIN.NS": "State Bank of India",
    "AXISBANK.NS": "Axis Bank", "KOTAKBANK.NS": "Kotak Mahindra Bank",
    "BAJFINANCE.NS": "Bajaj Finance", "SUNPHARMA.NS": "Sun Pharmaceutical",
    "MARUTI.NS": "Maruti Suzuki", "LT.NS": "Larsen & Toubro", "ONGC.NS": "ONGC",
}

_fetcher = None
_agent   = None


def _init():
    global _fetcher, _agent
    if _fetcher is None:
        _fetcher = StockFetcher()
    if _agent is None:
        _agent = SignalAgent()


async def _analyse_one(symbol: str, name: str) -> dict:
    cache_key = symbol
    cached    = dynamo_cache.get_cached(cache_key)
    if cached:
        return cached

    stock_data = await _fetcher.get_stock_data(symbol)
    if not stock_data:
        return {"symbol": symbol, "name": name, "error": "No data available"}

    result = _agent.analyze(symbol, name, stock_data)
    dynamo_cache.set_cached(cache_key, result, ttl_seconds=300)
    return result


async def _analyse_all(warmup: bool = False) -> list:
    tasks = [_analyse_one(sym, name) for sym, name in INDIAN_STOCKS.items()]
    return await asyncio.gather(*tasks)


def handler(event, context):
    _init()

    raw_path    = event.get("rawPath", "")
    path_params = event.get("pathParameters") or {}
    qs          = event.get("queryStringParameters") or {}
    is_warmup   = event.get("warmup") or qs.get("warmup") == "true"

    # GET /api/stocks/list — static list, no API calls
    if "list" in raw_path:
        return _json([{"symbol": s, "name": n} for s, n in INDIAN_STOCKS.items()])

    # GET /api/stock/{symbol} — single stock detail
    if path_params.get("symbol"):
        symbol = path_params["symbol"].upper()
        if not symbol.endswith(".NS"):
            symbol += ".NS"
        name   = INDIAN_STOCKS.get(symbol, symbol.replace(".NS", ""))
        result = asyncio.run(_analyse_one(symbol, name))
        return _json(result)

    # GET /api/stocks — all stocks (or EventBridge warmup)
    results = asyncio.run(_analyse_all(warmup=is_warmup))
    if is_warmup:
        return _json({"warmed": len(results), "message": "Cache pre-warmed"})
    return _json({"stocks": results, "count": len(results)})


def _json(data, status: int = 200):
    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(data, default=str),
    }
