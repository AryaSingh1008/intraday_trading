"""
Lambda handler: GET /api/market-status
Returns IST market open/closed status + live NIFTY 50, BANKNIFTY, India VIX index data.
"""
import json
from datetime import datetime
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")

_INDICES = {
    "^NSEI":   "NIFTY 50",
    "^NSEBANK": "BANKNIFTY",
    "^INDIAVIX": "India VIX",
}


def _fetch_indices() -> dict:
    """Fetch live NIFTY 50, BANKNIFTY, India VIX via yfinance."""
    result = {}
    try:
        import yfinance as yf
        tickers = yf.Tickers(" ".join(_INDICES.keys()))
        for ticker_sym, label in _INDICES.items():
            try:
                info = tickers.tickers[ticker_sym].fast_info
                price     = float(info.last_price)    if info.last_price    else None
                prev_close= float(info.previous_close) if info.previous_close else None
                change_pct = round(((price - prev_close) / prev_close) * 100, 2) if (price and prev_close) else None
                result[label] = {
                    "price":      round(price, 2) if price else None,
                    "change_pct": change_pct,
                }
            except Exception:
                result[label] = {"price": None, "change_pct": None}
    except Exception:
        pass
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
