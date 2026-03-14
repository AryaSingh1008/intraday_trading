"""
Lambda handler: GET | POST | DELETE /api/portfolio
My Portfolio dashboard — tracks user stock holdings with live P&L.

Routes:
  GET    /api/portfolio                  → list all holdings + live P&L
  POST   /api/portfolio                  → add a holding
  DELETE /api/portfolio/{holding_id}     → remove one holding
"""

import json
import os
import time
import uuid
from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Key

USER_ID = "default"   # Single-user mode; extend to Cognito sub for multi-user

_table = None


def _get_table():
    global _table
    if _table is None:
        region = os.environ.get("AWS_REGION", "us-east-1")
        db     = boto3.resource("dynamodb", region_name=region)
        _table = db.Table(os.environ["PORTFOLIO_TABLE_NAME"])
    return _table


def handler(event, context):
    method      = event.get("requestContext", {}).get("http", {}).get("method", "GET")
    path_params = event.get("pathParameters") or {}
    table       = _get_table()

    # ── DELETE /api/portfolio/{holding_id} ────────────────────────────────────
    if method == "DELETE":
        holding_id = path_params.get("holding_id", "")
        if not holding_id:
            return _json({"error": "holding_id required"}, 400)
        table.delete_item(Key={"user_id": USER_ID, "holding_id": holding_id})
        return _json({"removed": holding_id})

    # ── POST /api/portfolio ───────────────────────────────────────────────────
    if method == "POST":
        body      = json.loads(event.get("body") or "{}")
        symbol    = (body.get("symbol") or "").upper().strip()
        name      = (body.get("name") or symbol).strip()
        buy_price = body.get("buy_price")
        quantity  = body.get("quantity")
        buy_date  = body.get("buy_date") or time.strftime("%Y-%m-%d", time.gmtime())

        if not symbol:
            return _json({"error": "symbol required"}, 400)
        try:
            buy_price = Decimal(str(float(buy_price)))
            quantity  = int(quantity)
        except (TypeError, ValueError):
            return _json({"error": "buy_price and quantity must be valid numbers"}, 400)

        if buy_price <= 0 or quantity <= 0:
            return _json({"error": "buy_price and quantity must be positive"}, 400)

        holding_id = str(uuid.uuid4())
        table.put_item(Item={
            "user_id":    USER_ID,
            "holding_id": holding_id,
            "symbol":     symbol,
            "name":       name,
            "buy_price":  buy_price,
            "quantity":   quantity,
            "buy_date":   buy_date,
            "added_at":   time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        })
        return _json({"added": holding_id, "symbol": symbol})

    # ── GET /api/portfolio ────────────────────────────────────────────────────
    resp     = table.query(
        KeyConditionExpression=Key("user_id").eq(USER_ID)
    )
    holdings = resp.get("Items", [])

    if not holdings:
        return _json({"holdings": [], "summary": _empty_summary()})

    # Fetch live prices for every unique symbol (one yfinance call per symbol)
    prices = _fetch_prices({h["symbol"] for h in holdings})

    enriched = []
    for h in holdings:
        sym         = h["symbol"]
        buy_price   = float(h.get("buy_price", 0))
        quantity    = int(h.get("quantity", 0))
        cur         = prices.get(sym, {})
        cur_price   = cur.get("current", 0.0)
        prev_close  = cur.get("prev_close", 0.0)

        invested      = round(buy_price * quantity, 2)
        cur_value     = round(cur_price * quantity, 2) if cur_price else None
        total_gain    = round(cur_value - invested, 2) if cur_value is not None else None
        total_gain_pct= round((total_gain / invested) * 100, 2) if (total_gain is not None and invested) else None
        day_gain      = round((cur_price - prev_close) * quantity, 2) if (cur_price and prev_close) else None
        day_gain_pct  = round(((cur_price - prev_close) / prev_close) * 100, 2) if (prev_close and cur_price) else None

        enriched.append({
            "holding_id":     h["holding_id"],
            "symbol":         sym,
            "name":           h.get("name", sym),
            "buy_price":      buy_price,
            "quantity":       quantity,
            "buy_date":       h.get("buy_date", ""),
            "current_price":  cur_price if cur_price else None,
            "prev_close":     prev_close if prev_close else None,
            "invested":       invested,
            "current_value":  cur_value,
            "total_gain":     total_gain,
            "total_gain_pct": total_gain_pct,
            "day_gain":       day_gain,
            "day_gain_pct":   day_gain_pct,
        })

    summary = _compute_summary(enriched)
    return _json({"holdings": enriched, "summary": summary})


def _fetch_prices(symbols: set) -> dict:
    """Fetch current price and previous close for a set of symbols via yfinance."""
    result = {}
    try:
        import yfinance as yf
        for sym in symbols:
            try:
                fi = yf.Ticker(sym).fast_info
                cur  = float(fi.get("last_price")      or 0)
                prev = float(fi.get("previous_close")   or 0)
                result[sym] = {"current": cur, "prev_close": prev}
            except Exception:
                result[sym] = {"current": 0.0, "prev_close": 0.0}
    except Exception:
        pass
    return result


def _compute_summary(holdings: list) -> dict:
    total_invested = round(sum(h["invested"] for h in holdings), 2)
    current_value  = round(sum(h["current_value"] or h["invested"] for h in holdings), 2)
    total_gain     = round(current_value - total_invested, 2)
    total_gain_pct = round((total_gain / total_invested) * 100, 2) if total_invested else 0.0
    day_gain       = round(sum(h["day_gain"] or 0 for h in holdings), 2)
    return {
        "total_invested":  total_invested,
        "current_value":   current_value,
        "total_gain":      total_gain,
        "total_gain_pct":  total_gain_pct,
        "day_gain":        day_gain,
    }


def _empty_summary() -> dict:
    return {"total_invested": 0, "current_value": 0,
            "total_gain": 0, "total_gain_pct": 0, "day_gain": 0}


def _json(data: dict, status: int = 200):
    return {
        "statusCode": status,
        "headers": {
            "Content-Type":                "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(data, default=str),
    }
