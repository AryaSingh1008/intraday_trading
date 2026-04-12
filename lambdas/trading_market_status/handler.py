"""
Lambda handler: GET /api/market-status
Returns IST market open/closed status + NIFTY 50, BANKNIFTY, India VIX.
Uses last 5 days of history so values are always available even when closed.
"""
import json
from datetime import datetime
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")

_INDICES = {
    "^NSEI":     "NIFTY 50",
    "^NSEBANK":  "BANKNIFTY",
    "^INDIAVIX": "India VIX",
}


def _fetch_indices() -> dict:
    """
    Fetch last close + previous close for each index.
    Downloads 5 days of daily history so the most recent close is always
    available regardless of whether the market is currently open or closed.
    """
    result = {label: {"price": None, "change_pct": None} for label in _INDICES.values()}
    try:
        import yfinance as yf
        syms = list(_INDICES.keys())
        data = yf.download(
            syms,
            period="5d",
            interval="1d",
            group_by="ticker",
            progress=False,
            auto_adjust=True,
        )
        if data.empty:
            return result

        for sym, label in _INDICES.items():
            try:
                if len(syms) == 1:
                    closes = data["Close"].dropna()
                else:
                    closes = data[sym]["Close"].dropna()

                if len(closes) < 1:
                    continue

                price      = float(closes.iloc[-1])
                prev_close = float(closes.iloc[-2]) if len(closes) >= 2 else price
                change_pct = round(((price - prev_close) / prev_close) * 100, 2) if prev_close else None

                result[label] = {
                    "price":      round(price, 2),
                    "change_pct": change_pct,
                }
            except Exception:
                pass
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
