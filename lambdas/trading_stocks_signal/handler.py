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
from ai_validator import validate_signal

INDIAN_STOCKS = {
    # ── IT (8) ────────────────────────────────────────────────────────────────
    "TCS.NS":        {"name": "Tata Consultancy Services", "sector": "IT"},
    "INFY.NS":       {"name": "Infosys",                   "sector": "IT"},
    "WIPRO.NS":      {"name": "Wipro",                     "sector": "IT"},
    "HCLTECH.NS":    {"name": "HCL Technologies",          "sector": "IT"},
    "TECHM.NS":      {"name": "Tech Mahindra",             "sector": "IT"},
    "LTIM.NS":       {"name": "LTIMindtree",               "sector": "IT"},
    "MPHASIS.NS":    {"name": "Mphasis",                   "sector": "IT"},
    "PERSISTENT.NS": {"name": "Persistent Systems",        "sector": "IT"},
    # ── Banking (8) ───────────────────────────────────────────────────────────
    "HDFCBANK.NS":   {"name": "HDFC Bank",                 "sector": "Banking"},
    "ICICIBANK.NS":  {"name": "ICICI Bank",                "sector": "Banking"},
    "SBIN.NS":       {"name": "State Bank of India",       "sector": "Banking"},
    "AXISBANK.NS":   {"name": "Axis Bank",                 "sector": "Banking"},
    "KOTAKBANK.NS":  {"name": "Kotak Mahindra Bank",       "sector": "Banking"},
    "INDUSINDBK.NS": {"name": "IndusInd Bank",             "sector": "Banking"},
    "BANKBARODA.NS": {"name": "Bank of Baroda",            "sector": "Banking"},
    "PNB.NS":        {"name": "Punjab National Bank",      "sector": "Banking"},
    # ── Finance (7) ───────────────────────────────────────────────────────────
    "BAJFINANCE.NS": {"name": "Bajaj Finance",             "sector": "Finance"},
    "BAJAJFINSV.NS": {"name": "Bajaj Finserv",             "sector": "Finance"},
    "SHRIRAMFIN.NS": {"name": "Shriram Finance",           "sector": "Finance"},
    "JIOFIN.NS":     {"name": "Jio Financial Services",    "sector": "Finance"},
    "HDFCLIFE.NS":   {"name": "HDFC Life Insurance",       "sector": "Finance"},
    "SBILIFE.NS":    {"name": "SBI Life Insurance",        "sector": "Finance"},
    "ICICIPRULI.NS": {"name": "ICICI Prudential Life",     "sector": "Finance"},
    # ── Energy (8) ────────────────────────────────────────────────────────────
    "RELIANCE.NS":   {"name": "Reliance Industries",       "sector": "Energy"},
    "ONGC.NS":       {"name": "ONGC",                      "sector": "Energy"},
    "BPCL.NS":       {"name": "Bharat Petroleum",          "sector": "Energy"},
    "NTPC.NS":       {"name": "NTPC",                      "sector": "Energy"},
    "POWERGRID.NS":  {"name": "Power Grid Corporation",    "sector": "Energy"},
    "COALINDIA.NS":  {"name": "Coal India",                "sector": "Energy"},
    "ADANIENT.NS":   {"name": "Adani Enterprises",         "sector": "Energy"},
    "ADANIGREEN.NS": {"name": "Adani Green Energy",        "sector": "Energy"},
    # ── Pharma (7) ────────────────────────────────────────────────────────────
    "SUNPHARMA.NS":  {"name": "Sun Pharmaceutical",        "sector": "Pharma"},
    "CIPLA.NS":      {"name": "Cipla",                     "sector": "Pharma"},
    "DRREDDY.NS":    {"name": "Dr. Reddy's Laboratories",  "sector": "Pharma"},
    "APOLLOHOSP.NS": {"name": "Apollo Hospitals",          "sector": "Pharma"},
    "DIVISLAB.NS":   {"name": "Divi's Laboratories",       "sector": "Pharma"},
    "BIOCON.NS":     {"name": "Biocon",                    "sector": "Pharma"},
    "LUPIN.NS":      {"name": "Lupin",                     "sector": "Pharma"},
    # ── Auto (8) ──────────────────────────────────────────────────────────────
    "PAYTM.NS":      {"name": "Paytm (One97 Comm)",        "sector": "Others"},
    "MARUTI.NS":     {"name": "Maruti Suzuki",             "sector": "Auto"},
    "BAJAJ-AUTO.NS": {"name": "Bajaj Auto",                "sector": "Auto"},
    "EICHERMOT.NS":  {"name": "Eicher Motors",             "sector": "Auto"},
    "HEROMOTOCO.NS": {"name": "Hero MotoCorp",             "sector": "Auto"},
    "M&M.NS":        {"name": "Mahindra & Mahindra",       "sector": "Auto"},
    "ASHOKLEY.NS":   {"name": "Ashok Leyland",             "sector": "Auto"},
    "TVSMOTOR.NS":   {"name": "TVS Motor Company",         "sector": "Auto"},
    # ── FMCG (8) ──────────────────────────────────────────────────────────────
    "HINDUNILVR.NS": {"name": "Hindustan Unilever",        "sector": "FMCG"},
    "ITC.NS":        {"name": "ITC",                       "sector": "FMCG"},
    "BRITANNIA.NS":  {"name": "Britannia Industries",      "sector": "FMCG"},
    "NESTLEIND.NS":  {"name": "Nestle India",              "sector": "FMCG"},
    "TATACONSUM.NS": {"name": "Tata Consumer Products",    "sector": "FMCG"},
    "DABUR.NS":      {"name": "Dabur India",               "sector": "FMCG"},
    "MARICO.NS":     {"name": "Marico",                    "sector": "FMCG"},
    "GODREJCP.NS":   {"name": "Godrej Consumer Products",  "sector": "FMCG"},
    # ── Infrastructure (7) ────────────────────────────────────────────────────
    "LT.NS":         {"name": "Larsen & Toubro",           "sector": "Infra"},
    "ULTRACEMCO.NS": {"name": "UltraTech Cement",          "sector": "Infra"},
    "GRASIM.NS":     {"name": "Grasim Industries",         "sector": "Infra"},
    "ADANIPORTS.NS": {"name": "Adani Ports",               "sector": "Infra"},
    "SIEMENS.NS":    {"name": "Siemens",                   "sector": "Infra"},
    "ABB.NS":        {"name": "ABB India",                 "sector": "Infra"},
    "HAVELLS.NS":    {"name": "Havells India",             "sector": "Infra"},
    # ── Metals (6) ────────────────────────────────────────────────────────────
    "TATASTEEL.NS":  {"name": "Tata Steel",                "sector": "Metals"},
    "JSWSTEEL.NS":   {"name": "JSW Steel",                 "sector": "Metals"},
    "HINDALCO.NS":   {"name": "Hindalco Industries",       "sector": "Metals"},
    "VEDL.NS":       {"name": "Vedanta",                   "sector": "Metals"},
    "NMDC.NS":       {"name": "NMDC",                      "sector": "Metals"},
    "NATIONALUM.NS": {"name": "National Aluminium",        "sector": "Metals"},
    # ── Telecom (4) ───────────────────────────────────────────────────────────
    "BHARTIARTL.NS": {"name": "Bharti Airtel",             "sector": "Telecom"},
    "IDEA.NS":       {"name": "Vodafone Idea",             "sector": "Telecom"},
    "INDUSTOWER.NS": {"name": "Indus Towers",              "sector": "Telecom"},
    "TATACOMM.NS":   {"name": "Tata Communications",       "sector": "Telecom"},
    # ── Others (9) ────────────────────────────────────────────────────────────
    "TITAN.NS":      {"name": "Titan Company",             "sector": "Others"},
    "TRENT.NS":      {"name": "Trent",                     "sector": "Others"},
    "BEL.NS":        {"name": "Bharat Electronics",        "sector": "Others"},
    "ASIANPAINT.NS": {"name": "Asian Paints",              "sector": "Others"},
    "PIDILITIND.NS": {"name": "Pidilite Industries",       "sector": "Others"},
    "HAL.NS":        {"name": "Hindustan Aeronautics",     "sector": "Others"},
    "IRCTC.NS":      {"name": "IRCTC",                     "sector": "Others"},
    "NYKAA.NS":      {"name": "Nykaa (FSN E-Commerce)",    "sector": "Others"},
    "DMART.NS":      {"name": "Avenue Supermarts (DMart)",  "sector": "Others"},
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
    for symbol, info in INDIAN_STOCKS.items():
        name = info["name"]
        cached = dynamo_cache.get_cached(symbol)
        if cached:
            cached_results.append(cached)
        else:
            symbols_to_fetch[symbol] = info

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
        for symbol, info in batch:
            name   = info["name"]
            sector = info.get("sector", "Others")
            stock_data = batch_data.get(symbol)
            if not stock_data:
                cached_results.append({"symbol": symbol, "name": name, "error": "No data available"})
                continue
            analyse_tasks.append(_analyse_and_cache(symbol, name, stock_data, sector=sector))

        if analyse_tasks:
            new_results = await asyncio.gather(*analyse_tasks)
            cached_results.extend(new_results)

    return cached_results


async def _analyse_and_cache(symbol: str, name: str, stock_data: dict,
                             sector: str = "Others") -> dict:
    result = await _agent.analyze(symbol, name, stock_data, sector=sector)
    dynamo_cache.set_cached(symbol, result, ttl_seconds=900)
    return result


async def _analyse_page(page: int, per_page: int) -> list:
    """Analyse only the stocks for a specific page (fast for first page)."""
    all_symbols = list(INDIAN_STOCKS.items())
    start = (page - 1) * per_page
    page_symbols = all_symbols[start : start + per_page]

    results = []
    symbols_to_fetch = {}
    for symbol, info in page_symbols:
        name = info["name"]
        cached = dynamo_cache.get_cached(symbol)
        if cached:
            results.append(cached)
        else:
            symbols_to_fetch[symbol] = info

    if not symbols_to_fetch:
        return results

    batch_data = await _fetcher.get_batch_stock_data(list(symbols_to_fetch.keys()))
    analyse_tasks = []
    for symbol, info in symbols_to_fetch.items():
        name   = info["name"]
        sector = info.get("sector", "Others")
        stock_data = batch_data.get(symbol)
        if not stock_data:
            results.append({"symbol": symbol, "name": name, "error": "No data available"})
            continue
        analyse_tasks.append(_analyse_and_cache(symbol, name, stock_data, sector=sector))

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
        return _json([
            {"symbol": s, "name": info["name"], "sector": info["sector"]}
            for s, info in INDIAN_STOCKS.items()
        ])

    # GET /api/stock/{symbol} — single stock detail (with AI validation)
    if path_params.get("symbol"):
        symbol = path_params["symbol"].upper()
        if not symbol.endswith(".NS"):
            symbol += ".NS"
        info   = INDIAN_STOCKS.get(symbol, {})
        name   = info.get("name", symbol.replace(".NS", "")) if info else symbol.replace(".NS", "")
        result = asyncio.run(_analyse_one(symbol, name))

        # AI Signal Validation (cached separately, 15 min TTL)
        ai_cache_key = f"ai_{symbol}"
        ai_data = dynamo_cache.get_cached(ai_cache_key)
        if not ai_data:
            try:
                ai_data = validate_signal(result)
                if ai_data.get("ai_available"):
                    dynamo_cache.set_cached(ai_cache_key, ai_data, ttl_seconds=900)
            except Exception:
                ai_data = {"ai_available": False}
        result.update(ai_data)

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
