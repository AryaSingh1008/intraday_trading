"""
====================================================
  AI Intraday Trading Assistant - Main FastAPI App
====================================================
Serves both the API and the frontend from one server.
Access at: http://localhost:8000
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import logging
import os
from datetime import datetime
from typing import Optional
import pytz

from backend.agents.signal_agent import SignalAgent
from backend.data.stock_fetcher import StockFetcher
from backend.data.options_fetcher import OptionsFetcher
from backend.agents.options_agent import OptionsAgent
from backend.utils.excel_exporter import ExcelExporter
from backend.utils import wishlist_store
from backend.data import playwright_fetcher

# ── Logging ──────────────────────────────────────────────
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s  %(levelname)s  %(message)s")
logger = logging.getLogger(__name__)

# ── App setup ────────────────────────────────────────────
app = FastAPI(title="AI Intraday Trading Assistant", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Playwright background refresh ─────────────────────────
_playwright_task = None

async def _playwright_refresh_loop():
    """Background task: refresh NSE option chain data every 150 seconds."""
    logger.info("Playwright background refresh loop started.")
    while True:
        try:
            await playwright_fetcher.refresh_all()
        except Exception as e:
            logger.error(f"Playwright refresh loop error: {e}")
        await asyncio.sleep(150)   # refresh every 2.5 minutes


@app.on_event("startup")
async def startup_event():
    global _playwright_task
    if playwright_fetcher.is_available():
        logger.info("Starting Playwright NSE option chain background fetcher…")
        _playwright_task = asyncio.create_task(_playwright_refresh_loop())
    else:
        logger.warning("Playwright not available — using fallback options data sources.")


@app.on_event("shutdown")
async def shutdown_event():
    global _playwright_task
    if _playwright_task:
        _playwright_task.cancel()
    await playwright_fetcher.shutdown()

# ── Services ─────────────────────────────────────────────
stock_fetcher   = StockFetcher()
signal_agent    = SignalAgent()
options_fetcher = OptionsFetcher()
options_agent   = OptionsAgent()
excel_exporter  = ExcelExporter()

# ── Indian Stock List ─────────────────────────────────────
INDIAN_STOCKS = {
    "RELIANCE.NS":   "Reliance Industries",
    "TCS.NS":        "TCS",
    "INFY.NS":       "Infosys",
    "HDFCBANK.NS":   "HDFC Bank",
    "ICICIBANK.NS":  "ICICI Bank",
    "WIPRO.NS":      "Wipro",
    "TATAMOTORS.NS": "Tata Motors",
    "SBIN.NS":       "SBI",
    "AXISBANK.NS":   "Axis Bank",
    "KOTAKBANK.NS":  "Kotak Bank",
    "BAJFINANCE.NS": "Bajaj Finance",
    "SUNPHARMA.NS":  "Sun Pharma",
    "MARUTI.NS":     "Maruti Suzuki",
    "LT.NS":         "L&T",
    "ONGC.NS":       "ONGC",
}

# ── Options instruments ────────────────────────────────────
OPTIONS_INSTRUMENTS = {
    "NIFTY":     "Nifty 50",
    "BANKNIFTY": "Bank Nifty",
    "RELIANCE":  "Reliance Industries",
    "TCS":       "TCS",
    "INFY":      "Infosys",
    "HDFCBANK":  "HDFC Bank",
    "ICICIBANK": "ICICI Bank",
}

# ── In-memory cache (refreshes every 5 min) ──────────────
_cache: dict = {}
_cache_ts: dict = {}
CACHE_TTL = 900  # seconds (15 minutes)


def _is_cached(key: str) -> bool:
    if key not in _cache:
        return False
    return (datetime.now().timestamp() - _cache_ts.get(key, 0)) < CACHE_TTL


# ── Routes ────────────────────────────────────────────────

@app.get("/")
async def serve_frontend():
    return FileResponse("frontend/index.html")


@app.get("/api/stocks")
async def get_stocks(page: int = 0, per_page: int = 0):
    """Return Indian stocks with AI-generated BUY / SELL / HOLD signals.
    Optional pagination: ?page=1&per_page=10 returns only that page of stocks.
    """
    stock_items = list(INDIAN_STOCKS.items())

    # If paginated, only process the requested slice
    if page > 0 and per_page > 0:
        start = (page - 1) * per_page
        stock_items = stock_items[start : start + per_page]

    results = []

    for symbol, name in stock_items:
        cache_key = symbol
        try:
            if _is_cached(cache_key):
                results.append(_cache[cache_key])
                continue

            stock_data = await stock_fetcher.get_stock_data(symbol)
            if stock_data:
                signal = await signal_agent.analyze(symbol, name, stock_data)
                _cache[cache_key] = signal
                _cache_ts[cache_key] = datetime.now().timestamp()
                results.append(signal)
        except Exception as e:
            logger.warning(f"Skipping {symbol}: {e}")

    # Sort: STRONG BUY first, STRONG SELL last
    order = {"STRONG BUY": 0, "BUY": 1, "HOLD": 2, "SELL": 3, "STRONG SELL": 4}
    results.sort(key=lambda x: order.get(x.get("signal", "HOLD"), 2))

    response = {
        "stocks":       results,
        "last_updated": datetime.now().strftime("%d %b %Y, %I:%M %p"),
        "count":        len(results),
    }
    if page > 0 and per_page > 0:
        response["total"] = len(INDIAN_STOCKS)
        response["page"] = page
        response["per_page"] = per_page
    return response


@app.get("/api/stock/{symbol}")
async def get_stock_detail(symbol: str):
    """Return detailed analysis for one Indian stock."""
    try:
        stock_data = await stock_fetcher.get_stock_data(symbol.upper())
        if not stock_data:
            raise HTTPException(status_code=404, detail=f"No data for {symbol}")
        name = INDIAN_STOCKS.get(symbol.upper(), symbol.upper())
        return await signal_agent.analyze(symbol.upper(), name, stock_data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/options")
async def get_options(symbol: str = "NIFTY"):
    """Return option chain analysis for an Indian index or stock."""
    sym = symbol.upper()
    cache_key = f"options_{sym}"
    try:
        if _is_cached(cache_key):
            return _cache[cache_key]

        raw = await options_fetcher.get_option_chain(sym)
        if not raw:
            raise HTTPException(status_code=404, detail=f"No options data for {sym}")

        result = options_agent.analyze(raw)
        result["last_updated"] = datetime.now().strftime("%d %b %Y, %I:%M %p")
        _cache[cache_key]    = result
        _cache_ts[cache_key] = datetime.now().timestamp()
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Options error for {sym}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/news")
async def get_news(symbol: Optional[str] = None):
    """Return latest market news with sentiment scores."""
    from backend.agents.sentiment_agent import SentimentAgent
    sa = SentimentAgent()
    try:
        news = await sa.get_news(symbol)
        return {"news": news, "last_updated": datetime.now().strftime("%d %b %Y, %I:%M %p")}
    except Exception as e:
        logger.error(f"News error: {e}")
        return {"news": [], "last_updated": datetime.now().strftime("%d %b %Y, %I:%M %p")}


@app.get("/api/export")
async def export_excel():
    """Download an Excel file with all current signals."""
    stocks_data = await get_stocks()
    filename = await excel_exporter.export(stocks_data["stocks"], "IN")
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return FileResponse(
        filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=f"trading_signals_{ts}.xlsx",
    )


@app.get("/api/stocks/list")
async def list_stocks():
    """Return the full known-stock list for autocomplete."""
    return {
        "stocks": [
            {"symbol": sym, "name": name}
            for sym, name in INDIAN_STOCKS.items()
        ]
    }


@app.get("/api/market-status")
async def market_status():
    """Return whether the Indian market is open right now."""
    now_ist = datetime.now(pytz.timezone("Asia/Kolkata"))

    def mins(dt):
        return dt.hour * 60 + dt.minute

    in_open = now_ist.weekday() < 5 and (9 * 60 + 15) <= mins(now_ist) <= (15 * 60 + 30)

    return {
        "indian": {
            "open":  in_open,
            "time":  now_ist.strftime("%I:%M %p IST"),
            "label": "OPEN" if in_open else "CLOSED",
        },
    }


@app.delete("/api/cache")
async def clear_cache():
    """Force-refresh all cached data."""
    _cache.clear()
    _cache_ts.clear()
    return {"message": "Cache cleared. Next request will fetch fresh data."}


# ── Wishlist helpers ──────────────────────────────────────

def _unavailable_entry(symbol: str, name: str) -> dict:
    """Placeholder returned when yfinance cannot fetch data for a symbol."""
    hint = ""
    if not any(symbol.endswith(s) for s in (".NS", ".BO", ".BSE")):
        hint = " Try adding the exchange suffix, e.g. " + symbol + ".NS for NSE."
    return {
        "symbol":      symbol,
        "name":        name,
        "wishlisted":  True,
        "unavailable": True,
        "explanation": f"Could not load data for '{symbol}'.{hint}",
    }


# ── Wishlist routes ───────────────────────────────────────

class WishlistItem(BaseModel):
    symbol: str
    name: str


@app.get("/api/wishlist")
async def get_wishlist():
    """Return wishlist stocks with live AI signals."""
    items   = wishlist_store.get_all()
    results = []

    for item in items:
        symbol = item["symbol"]
        name   = item.get("name") or INDIAN_STOCKS.get(symbol, symbol)
        cache_key = symbol
        try:
            if _is_cached(cache_key):
                entry = dict(_cache[cache_key])
                entry["wishlisted"] = True
                results.append(entry)
                continue

            stock_data = await stock_fetcher.get_stock_data(symbol)
            if stock_data:
                signal = await signal_agent.analyze(symbol, name, stock_data)
                _cache[cache_key]    = signal
                _cache_ts[cache_key] = datetime.now().timestamp()
                entry = dict(signal)
                entry["wishlisted"] = True
                results.append(entry)
            else:
                # Symbol not found — still include it so the user can see and remove it
                results.append(_unavailable_entry(symbol, name))
        except Exception as e:
            logger.warning(f"Wishlist: {symbol}: {e}")
            results.append(_unavailable_entry(symbol, name))

    return {
        "stocks":       results,
        "last_updated": datetime.now().strftime("%d %b %Y, %I:%M %p"),
        "count":        len(results),
    }


@app.post("/api/wishlist")
async def add_to_wishlist(item: WishlistItem):
    """Add a stock to the wishlist."""
    name = item.name or INDIAN_STOCKS.get(item.symbol.upper(), item.symbol.upper())
    added = wishlist_store.add(item.symbol, name)
    if not added:
        return {"message": f"{item.symbol} is already in your wishlist.", "already_exists": True}
    return {"message": f"{name} added to wishlist!", "already_exists": False}


@app.delete("/api/wishlist/{symbol}")
async def remove_from_wishlist(symbol: str):
    """Remove a stock from the wishlist."""
    removed = wishlist_store.remove(symbol)
    if not removed:
        raise HTTPException(status_code=404, detail=f"{symbol} not found in wishlist.")
    return {"message": f"{symbol} removed from wishlist."}


@app.get("/api/wishlist/check/{symbol}")
async def check_wishlist(symbol: str):
    """Check if a symbol is already wishlisted."""
    return {"symbol": symbol.upper(), "wishlisted": wishlist_store.exists(symbol)}


# ── Static files (CSS / JS) ──────────────────────────────
app.mount("/css", StaticFiles(directory="frontend/css"), name="css")
app.mount("/js",  StaticFiles(directory="frontend/js"),  name="js")
