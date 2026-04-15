"""
Lambda handler: GET /api/stocks, GET /api/stock/{symbol}, GET /api/stocks/list
Wraps StockFetcher + SignalAgent — always uses live data.
"""
import json
import os
import asyncio
import time
from datetime import datetime
from zoneinfo import ZoneInfo

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
    stock_data = await _fetcher.get_stock_data(symbol)
    if not stock_data:
        return {"symbol": symbol, "name": name, "error": "No data available"}

    result = await _agent.analyze(symbol, name, stock_data)
    return result


async def _analyse_all(deadline: float = 0) -> list:
    all_symbols = list(INDIAN_STOCKS.items())
    results = []
    BATCH_SIZE = 10

    for i in range(0, len(all_symbols), BATCH_SIZE):
        if deadline and time.time() > deadline:
            break

        batch = all_symbols[i : i + BATCH_SIZE]
        batch_symbols = [sym for sym, _ in batch]

        batch_data = await _fetcher.get_batch_stock_data(batch_symbols)

        analyse_tasks = []
        for symbol, info in batch:
            name   = info["name"]
            sector = info.get("sector", "Others")
            stock_data = batch_data.get(symbol)
            if not stock_data:
                results.append({"symbol": symbol, "name": name, "error": "No data available"})
                continue
            analyse_tasks.append(_analyse_fresh(symbol, name, stock_data, sector=sector))

        if analyse_tasks:
            new_results = await asyncio.gather(*analyse_tasks)
            results.extend(new_results)

    return results


async def _analyse_fresh(symbol: str, name: str, stock_data: dict,
                         sector: str = "Others",
                         mode: str = "intraday") -> dict:
    result = await _agent.analyze(symbol, name, stock_data, sector=sector, mode=mode)
    result["analysed_at"] = datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%I:%M %p")
    return result


async def _analyse_positional(portfolio: int = 100_000,
                               max_positions: int = 6) -> dict:
    """
    Score all stocks in positional mode, return the top 8 BUY/STRONG BUY picks.
    Fetches all symbols in one yfinance batch (vs sequential batches of 10) so
    the full run completes in ~8s — well within the 29s API Gateway timeout.
    """
    all_symbols = list(INDIAN_STOCKS.items())

    # One batch download for all symbols — yf.download handles multi-ticker
    # efficiently in a single network round-trip.
    all_syms  = [sym for sym, _ in all_symbols]
    batch_data = await _fetcher.get_batch_stock_data(all_syms)

    tasks = []
    for symbol, info in all_symbols:
        sd = batch_data.get(symbol)
        if not sd:
            continue
        # Inject allocation params so signal_agent uses them for position sizing
        sd["_portfolio"]     = portfolio
        sd["_max_positions"] = max_positions
        tasks.append(_analyse_fresh(symbol, info["name"], sd,
                                    sector=info.get("sector", "Others"),
                                    mode="positional"))

    results = list(await asyncio.gather(*tasks)) if tasks else []

    # Filter: only BUY / STRONG BUY with score >= 55 and valid target/SL
    picks = [
        r for r in results
        if r.get("signal") in ("BUY", "STRONG BUY")
        and r.get("score", 0) >= 55
        and r.get("target_price")
        and r.get("stop_loss")
        and not r.get("error")
    ]
    # Sort by score descending, take top 8
    picks.sort(key=lambda r: r.get("score", 0), reverse=True)
    picks = picks[:8]

    # Compute R:R and per-pick invest_amount (may already be set in signal_agent)
    per_pos = round(portfolio / max_positions, 2)
    for p in picks:
        cur = p.get("current_price", 0)
        tgt = p.get("target_price", 0)
        sl  = p.get("stop_loss", 0)
        if cur and tgt and sl and (cur - sl) > 0:
            p["rr_ratio"] = round((tgt - cur) / (cur - sl), 2)
        p.setdefault("invest_amount", per_pos)

    return {
        "picks":        picks,
        "total_scored": len(results),
        "total_passed": len(picks),
        "portfolio":    portfolio,
        "max_positions": max_positions,
        "per_position": per_pos,
        "last_updated": datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%d %b %Y, %I:%M %p"),
    }


async def _analyse_page(page: int, per_page: int) -> list:
    """Analyse only the stocks for a specific page — always live data."""
    all_symbols = list(INDIAN_STOCKS.items())
    start = (page - 1) * per_page
    page_symbols = all_symbols[start : start + per_page]

    symbols_to_fetch = [sym for sym, _ in page_symbols]
    batch_data = await _fetcher.get_batch_stock_data(symbols_to_fetch)

    results = []
    analyse_tasks = []
    for symbol, info in page_symbols:
        name   = info["name"]
        sector = info.get("sector", "Others")
        stock_data = batch_data.get(symbol)
        if not stock_data:
            results.append({"symbol": symbol, "name": name, "error": "No data available"})
            continue
        analyse_tasks.append(_analyse_fresh(symbol, name, stock_data, sector=sector))

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

    # GET /api/swing/picks?portfolio=100000&max_positions=6
    if "swing/picks" in raw_path:
        portfolio     = int(qs.get("portfolio",     "100000"))
        max_positions = int(qs.get("max_positions", "6"))
        return _json(asyncio.run(_analyse_positional(portfolio, max_positions)))

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

        # AI Signal Validation — always fresh
        try:
            ai_data = validate_signal(result)
        except Exception:
            ai_data = {"ai_available": False}
        result.update(ai_data)

        return _json(result)

    # GET /api/stocks — EventBridge warmup is a no-op (no cache)
    if is_warmup:
        return _json({"warmed": 0, "message": "Caching disabled — no warmup needed"})

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
    results = asyncio.run(_analyse_all(deadline=deadline))
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
