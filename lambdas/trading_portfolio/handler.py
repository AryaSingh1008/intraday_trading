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
from datetime import date
from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Key

_table = None


def _get_table():
    global _table
    if _table is None:
        region = os.environ.get("AWS_REGION", "us-east-1")
        db     = boto3.resource("dynamodb", region_name=region)
        _table = db.Table(os.environ["PORTFOLIO_TABLE_NAME"])
    return _table


def _get_user_id(event: dict) -> str:
    """Extract the Cognito user's unique sub from the JWT authorizer context."""
    try:
        return event["requestContext"]["authorizer"]["jwt"]["claims"]["sub"]
    except (KeyError, TypeError):
        return "default"  # fallback for local dev / unit tests


def handler(event, context):
    method      = event.get("requestContext", {}).get("http", {}).get("method", "GET")
    raw_path    = event.get("rawPath", "")
    path_params = event.get("pathParameters") or {}
    user_id     = _get_user_id(event)

    table = _get_table()

    # ── DELETE /api/portfolio/{holding_id} ────────────────────────────────────
    if method == "DELETE":
        holding_id = path_params.get("holding_id", "")
        if not holding_id:
            return _json({"error": "holding_id required"}, 400)
        table.delete_item(Key={"user_id": user_id, "holding_id": holding_id})
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
            "user_id":    user_id,
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
        KeyConditionExpression=Key("user_id").eq(user_id)
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

        invested       = round(buy_price * quantity, 2)
        price_ok       = cur_price and cur_price > 0
        cur_value      = round(cur_price * quantity, 2) if price_ok else None
        total_gain     = round(cur_value - invested, 2) if cur_value is not None else None
        total_gain_pct = round((total_gain / invested) * 100, 2) if (total_gain is not None and invested) else None
        day_gain       = round((cur_price - prev_close) * quantity, 2) if (price_ok and prev_close) else None
        day_gain_pct   = round(((cur_price - prev_close) / prev_close) * 100, 2) if (prev_close and price_ok) else None

        # Days held since buy date
        days_held = None
        buy_date_str = h.get("buy_date", "")
        if buy_date_str:
            try:
                buy_dt   = date.fromisoformat(buy_date_str)
                days_held = (date.today() - buy_dt).days
            except Exception:
                pass

        enriched.append({
            "holding_id":     h["holding_id"],
            "symbol":         sym,
            "name":           h.get("name", sym),
            "buy_price":      buy_price,
            "quantity":       quantity,
            "buy_date":       buy_date_str,
            "days_held":      days_held,
            "current_price":  cur_price if price_ok else None,
            "prev_close":     prev_close if prev_close else None,
            "invested":       invested,
            "current_value":  cur_value,
            "total_gain":     total_gain,
            "total_gain_pct": total_gain_pct,
            "day_gain":       day_gain,
            "day_gain_pct":   day_gain_pct,
            "price_available": price_ok,
        })

    summary = _compute_summary(enriched)
    return _json({"holdings": enriched, "summary": summary})


def _fetch_prices(symbols: set) -> dict:
    """Fetch current price and previous close for a set of symbols via yfinance.
    Uses batch download with a timeout to prevent Lambda from hanging."""
    result = {sym: {"current": 0.0, "prev_close": 0.0} for sym in symbols}
    if not symbols:
        return result
    try:
        import yfinance as yf
        sym_list = list(symbols)
        # Batch download all symbols at once (much faster than one-by-one)
        data = yf.download(
            sym_list,
            period="2d",
            group_by="ticker",
            threads=True,
            timeout=10,       # 10-second timeout per request
            progress=False,
        )
        if data.empty:
            return result

        for sym in symbols:
            try:
                if len(symbols) == 1:
                    # Single-ticker: newer yfinance still returns MultiIndex columns
                    # e.g. ("Close", "RELIANCE.NS") — flatten to a plain Series
                    if hasattr(data.columns, "levels"):
                        sym_data = data.xs("Close", axis=1, level=0) if "Close" in data.columns.get_level_values(0) else None
                        if sym_data is not None and hasattr(sym_data, "squeeze"):
                            sym_data = sym_data.squeeze()  # DataFrame → Series
                    else:
                        sym_data = data["Close"] if "Close" in data.columns else None
                else:
                    sym_data = data[sym]["Close"] if sym in data.columns.get_level_values(0) else None
                if sym_data is None or (hasattr(sym_data, "empty") and sym_data.empty):
                    continue
                closes = sym_data.dropna()
                if len(closes) >= 2:
                    result[sym] = {"current": float(closes.iloc[-1]), "prev_close": float(closes.iloc[-2])}
                elif len(closes) == 1:
                    result[sym] = {"current": float(closes.iloc[-1]), "prev_close": float(closes.iloc[-1])}
            except Exception:
                pass
    except Exception:
        pass
    return result


def _compute_summary(holdings: list) -> dict:
    total_invested  = round(sum(h["invested"] for h in holdings), 2)
    # Only include holdings where we actually got a live price — don't substitute
    # invested cost for missing price (that hides real gains/losses on outages).
    priced = [h for h in holdings if h.get("price_available")]
    unpriced_count  = len(holdings) - len(priced)
    current_value   = round(sum(h["current_value"] for h in priced), 2) if priced else None
    priced_invested = round(sum(h["invested"]       for h in priced), 2)
    total_gain      = round(current_value - priced_invested, 2) if current_value is not None else None
    total_gain_pct  = round((total_gain / priced_invested) * 100, 2) if (total_gain is not None and priced_invested) else None
    day_gain        = round(sum(h["day_gain"] or 0 for h in priced), 2) if priced else None
    return {
        "total_invested":   total_invested,
        "current_value":    current_value,
        "total_gain":       total_gain,
        "total_gain_pct":   total_gain_pct,
        "day_gain":         day_gain,
        "unpriced_count":   unpriced_count,   # UI can show "N holdings unavailable"
    }


def _empty_summary() -> dict:
    return {"total_invested": 0, "current_value": 0,
            "total_gain": 0, "total_gain_pct": 0, "day_gain": 0,
            "unpriced_count": 0}


def _json(data: dict, status: int = 200):
    return {
        "statusCode": status,
        "headers": {
            "Content-Type":                "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(data, default=str),
    }


