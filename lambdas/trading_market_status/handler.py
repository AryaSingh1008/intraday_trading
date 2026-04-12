"""
Lambda handler: GET /api/market-status
Returns IST market open/closed status + NIFTY 50, BANKNIFTY, India VIX.
Uses Yahoo Finance v8 chart API directly (no yfinance) — faster and avoids timeouts.
"""
import json
import logging
import urllib.request
import urllib.error
from datetime import datetime
from zoneinfo import ZoneInfo

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

IST = ZoneInfo("Asia/Kolkata")

_INDICES = {
    "%5ENSEI":     "NIFTY 50",
    "%5ENSEBANK":  "BANKNIFTY",
    "%5EINDIAVIX": "India VIX",
}

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Accept": "application/json",
}


def _fetch_one(encoded_sym: str) -> dict:
    url = (
        f"https://query1.finance.yahoo.com/v8/finance/chart/{encoded_sym}"
        f"?interval=1d&range=5d"
    )
    req = urllib.request.Request(url, headers=_HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
        result = data["chart"]["result"][0]
        closes = result["indicators"]["quote"][0]["close"]
        closes = [c for c in closes if c is not None]
        if not closes:
            return {"price": None, "change_pct": None}
        price      = round(closes[-1], 2)
        prev_close = closes[-2] if len(closes) >= 2 else closes[-1]
        change_pct = round(((price - prev_close) / prev_close) * 100, 2) if prev_close else None
        return {"price": price, "change_pct": change_pct}
    except Exception as e:
        log.error("Error fetching %s: %s", encoded_sym, e)
        return {"price": None, "change_pct": None}


def _fetch_indices() -> dict:
    return {label: _fetch_one(sym) for sym, label in _INDICES.items()}


def handler(event, context):
    now_ist = datetime.now(IST)
    weekday = now_ist.weekday()
    hour    = now_ist.hour
    minute  = now_ist.minute

    is_open = (
        weekday < 5 and
        (hour > 9 or (hour == 9 and minute >= 15)) and
        (hour < 15 or (hour == 15 and minute <= 30))
    )

    indices = _fetch_indices()
    log.info("indices result: %s", indices)

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
