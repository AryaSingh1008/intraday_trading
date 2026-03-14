"""
Lambda handler: GET /api/market-status
Thin wrapper — reuses the exact logic from backend/app.py market_status route.
"""
import json
from datetime import datetime
from zoneinfo import ZoneInfo   # stdlib in Python 3.9+; Lambda 3.12 includes IANA tz data

IST = ZoneInfo("Asia/Kolkata")


def handler(event, context):
    now_ist = datetime.now(IST)
    weekday = now_ist.weekday()          # 0=Mon … 6=Sun
    hour    = now_ist.hour
    minute  = now_ist.minute

    is_open = (
        weekday < 5 and
        (hour > 9 or (hour == 9 and minute >= 15)) and
        (hour < 15 or (hour == 15 and minute <= 30))
    )

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps({
            "is_open":    is_open,
            "time_ist":   now_ist.strftime("%I:%M %p IST"),
            "date_ist":   now_ist.strftime("%d %b %Y"),
            "status":     "OPEN" if is_open else "CLOSED",
            "timezone":   "Asia/Kolkata",
        }),
    }
