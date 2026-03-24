"""
Lambda handler: GET /api/stocks, GET /api/stock/{symbol}, GET /api/stocks/list
Wraps StockFetcher + SignalAgent with DynamoDB caching.
"""
import json
import os
import asyncio
import time
from datetime import datetime

import dynamo_cache
from backend.data.stock_fetcher import StockFetcher
from backend.agents.signal_agent import SignalAgent

INDIAN_STOCKS = {
    # ── Original large-caps (retained) ────────────────────────────────────────
    "RELIANCE.NS":   "Reliance Industries",
    "TCS.NS":        "Tata Consultancy Services",
    "INFY.NS":       "Infosys",
    "HDFCBANK.NS":   "HDFC Bank",
    "ICICIBANK.NS":  "ICICI Bank",
    "WIPRO.NS":      "Wipro",
    "TATAMOTORS.NS": "Tata Motors",
    "SBIN.NS":       "State Bank of India",
    "AXISBANK.NS":   "Axis Bank",
    "KOTAKBANK.NS":  "Kotak Mahindra Bank",
    "BAJFINANCE.NS": "Bajaj Finance",
    "SUNPHARMA.NS":  "Sun Pharmaceutical",
    "MARUTI.NS":     "Maruti Suzuki",
    "LT.NS":         "Larsen & Toubro",
    "ONGC.NS":       "ONGC",
    # ── NIFTY 50 additions ────────────────────────────────────────────────────
    "ADANIENT.NS":   "Adani Enterprises",
    "ADANIPORTS.NS": "Adani Ports",
    "APOLLOHOSP.NS": "Apollo Hospitals",
    "ASIANPAINT.NS": "Asian Paints",
    "BAJAJ-AUTO.NS": "Bajaj Auto",
    "BAJAJFINSV.NS": "Bajaj Finserv",
    "BEL.NS":        "Bharat Electronics",
    "BPCL.NS":       "Bharat Petroleum",
    "BHARTIARTL.NS": "Bharti Airtel",
    "BRITANNIA.NS":  "Britannia Industries",
    "CIPLA.NS":      "Cipla",
    "COALINDIA.NS":  "Coal India",
    "DRREDDY.NS":    "Dr. Reddy's Laboratories",
    "EICHERMOT.NS":  "Eicher Motors",
    "GRASIM.NS":     "Grasim Industries",
    "HCLTECH.NS":    "HCL Technologies",
    "HDFCLIFE.NS":   "HDFC Life Insurance",
    "HEROMOTOCO.NS": "Hero MotoCorp",
    "HINDALCO.NS":   "Hindalco Industries",
    "HINDUNILVR.NS": "Hindustan Unilever",
    "INDUSINDBK.NS": "IndusInd Bank",
    "ITC.NS":        "ITC",
    "JIOFIN.NS":     "Jio Financial Services",
    "JSWSTEEL.NS":   "JSW Steel",
    "LTIM.NS":       "LTIMindtree",
    "M&M.NS":        "Mahindra & Mahindra",
    "NESTLEIND.NS":  "Nestle India",
    "NTPC.NS":       "NTPC",
    "POWERGRID.NS":  "Power Grid Corporation",
    "SHRIRAMFIN.NS": "Shriram Finance",
    "TATACONSUM.NS": "Tata Consumer Products",
    "TATASTEEL.NS":  "Tata Steel",
    "TECHM.NS":      "Tech Mahindra",
    "TITAN.NS":      "Titan Company",
    "TRENT.NS":      "Trent",
    "ULTRACEMCO.NS": "UltraTech Cement",
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

    result = await _agent.analyze(symbol, name, stock_data)
    dynamo_cache.set_cached(cache_key, result, ttl_seconds=900)
    return result


async def _analyse_all(warmup: bool = False, deadline: float = 0) -> list:
    # Check cache first — return cached results without hitting yfinance
    symbols_to_fetch = {}
    cached_results = []
    for symbol, name in INDIAN_STOCKS.items():
        cached = dynamo_cache.get_cached(symbol)
        if cached:
            cached_results.append(cached)
        else:
            symbols_to_fetch[symbol] = name

    # If everything is cached, return immediately
    if not symbols_to_fetch:
        return cached_results

    # Process uncached symbols in batches of 10
    uncached_symbols = list(symbols_to_fetch.items())
    BATCH_SIZE = 10

    for i in range(0, len(uncached_symbols), BATCH_SIZE):
        # If we have a deadline and are running low on time, stop and return
        # what we have so far (partial results are better than a timeout)
        if deadline and time.time() > deadline:
            break

        batch = uncached_symbols[i : i + BATCH_SIZE]
        batch_symbols = [sym for sym, _ in batch]

        # Batch-download this chunk
        batch_data = await _fetcher.get_batch_stock_data(batch_symbols)

        # Analyse each fetched stock in this chunk
        analyse_tasks = []
        for symbol, name in batch:
            stock_data = batch_data.get(symbol)
            if not stock_data:
                cached_results.append({"symbol": symbol, "name": name, "error": "No data available"})
                continue
            analyse_tasks.append(_analyse_and_cache(symbol, name, stock_data))

        if analyse_tasks:
            new_results = await asyncio.gather(*analyse_tasks)
            cached_results.extend(new_results)

    return cached_results


async def _analyse_and_cache(symbol: str, name: str, stock_data: dict) -> dict:
    result = await _agent.analyze(symbol, name, stock_data)
    dynamo_cache.set_cached(symbol, result, ttl_seconds=900)
    return result


async def _analyse_page(page: int, per_page: int) -> list:
    """Analyse only the stocks for a specific page (fast for first page)."""
    all_symbols = list(INDIAN_STOCKS.items())
    start = (page - 1) * per_page
    page_symbols = all_symbols[start : start + per_page]

    results = []
    symbols_to_fetch = {}
    for symbol, name in page_symbols:
        cached = dynamo_cache.get_cached(symbol)
        if cached:
            results.append(cached)
        else:
            symbols_to_fetch[symbol] = name

    if not symbols_to_fetch:
        return results

    batch_data = await _fetcher.get_batch_stock_data(list(symbols_to_fetch.keys()))
    analyse_tasks = []
    for symbol, name in symbols_to_fetch.items():
        stock_data = batch_data.get(symbol)
        if not stock_data:
            results.append({"symbol": symbol, "name": name, "error": "No data available"})
            continue
        analyse_tasks.append(_analyse_and_cache(symbol, name, stock_data))

    if analyse_tasks:
        new_results = await asyncio.gather(*analyse_tasks)
        results.extend(new_results)

    return results


def _now_str() -> str:
    return datetime.now().strftime("%d %b %Y, %I:%M %p")


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
    if is_warmup:
        # EventBridge warmup — no API Gateway timeout, fetch everything
        results = asyncio.run(_analyse_all(warmup=True, deadline=0))
        return _json({"warmed": len(results), "message": "Cache pre-warmed"})

    # Paginated request — ?page=1&per_page=10 — fast for first page
    page     = int(qs.get("page", 0))
    per_page = int(qs.get("per_page", 0))
    if page > 0 and per_page > 0:
        results = asyncio.run(_analyse_page(page, per_page))
        return _json({
            "stocks": results,
            "count": len(results),
            "total": len(INDIAN_STOCKS),
            "page": page,
            "per_page": per_page,
            "last_updated": _now_str(),
        })

    # Full request — used by background fetch
    deadline = time.time() + 20
    results = asyncio.run(_analyse_all(warmup=False, deadline=deadline))
    return _json({
        "stocks": results,
        "count": len(results),
        "last_updated": _now_str(),
    })


def _json(data, status: int = 200):
    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(data, default=str),
    }
