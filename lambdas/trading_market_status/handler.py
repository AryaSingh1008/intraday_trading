"""
Lambda handler: GET /api/market-status
Returns IST market open/closed status + NIFTY 50, BANKNIFTY, India VIX.
Fetches each index individually via Ticker.history() — more reliable than batch download.
Shows last closing price when market is closed, live price during market hours.
"""
import json
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

IST = ZoneInfo("Asia/Kolkata")

_INDICES = {
    "^NSEI":     "NIFTY 50",
    "^NSEBANK":  "BANKNIFTY",
    "^INDIAVIX": "India VIX",
}


def _fetch_indices() -> dict:
    """
    Fetch each index independently using Ticker.history(period='5d').
    Takes the most recent Close — works during market hours AND after close.
    """
    result = {label: {"price": None, "change_pct": None, "error": None} for label in _INDICES.values()}
    try:
        import yfinance as yf
        log.info("yfinance imported successfully, version: %s", getattr(yf, "__version__", "unknown"))
    except Exception as e:
        log.error("Failed to import yfinance: %s", e)
        for label in _INDICES.values():
            result[label]["error"] = f"import_error: {e}"
        return result

    for sym, label in _INDICES.items():
        try:
            log.info("Fetching %s (%s)", label, sym)
            hist = yf.Ticker(sym).history(period="5d", interval="1d")
            log.info("%s rows returned: %d", sym, len(hist))
            if hist.empty:
                result[label]["error"] = "empty_response"
                continue
            closes = hist["Close"].dropna()
            if len(closes) < 1:
                result[label]["error"] = "no_close_data"
                continue
            price      = float(closes.iloc[-1])
            prev_close = float(closes.iloc[-2]) if len(closes) >= 2 else price
            change_pct = round(((price - prev_close) / prev_close) * 100, 2) if prev_close else None
            result[label] = {
                "price":      round(price, 2),
                "change_pct": change_pct,
                "error":      None,
            }
            log.info("%s price=%.2f change_pct=%s", label, price, change_pct)
        except Exception as e:
            log.error("Error fetching %s: %s", sym, e)
            result[label]["error"] = str(e)

    return result


def handler(event, context):
    now_ist = datetime.now(IST)
    weekday = now_ist.weekday()   # 0=Mon … 6=Sun
    hour    = now_ist.hour
    minute  = now_ist.minute

    is_open = (
        weekday < 5 and
        (hour > 9 or (hour == 9 and minute >= 15)) and
        (hour < 15 or (hour == 15 and minute <= 30))
    )

    indices = _fetch_indices()

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps({
            "is_open":  is_open,
            "time_ist": now_ist.strftime("%I:%M %p IST"),
            "date_ist": now_ist.strftime("%d %b %Y"),
            "status":   "OPEN" if is_open else "CLOSED",
            "timezone": "Asia/Kolkata",
            "indices":  indices,
        }),
    }
