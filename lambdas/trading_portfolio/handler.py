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

    # ── Route swing positions to their own handler ────────────────────────────
    if "/swing/" in raw_path or raw_path.endswith("/swing/positions"):
        return _handle_swing(method, path_params, event, user_id)

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
    """Fetch current price and previous close for a set of symbols via yfinance.
    Uses batch download with a timeout to prevent Lambda from hanging."""
    result = {sym: {"current": 0.0, "prev_close": 0.0} for sym in symbols}
    if not symbols:
        return result
    try:
        import yfinance as yf
        # Batch download all symbols at once (much faster than one-by-one)
        data = yf.download(
            list(symbols),
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
                    sym_data = data
                else:
                    sym_data = data[sym] if sym in data.columns.get_level_values(0) else None
                if sym_data is None or sym_data.empty:
                    continue
                closes = sym_data["Close"].dropna()
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


# ══════════════════════════════════════════════════════════════════════════════
# Swing Positions  — GET | POST | DELETE /api/swing/positions
# ══════════════════════════════════════════════════════════════════════════════

_swing_table = None


def _get_swing_table():
    global _swing_table
    if _swing_table is None:
        region      = os.environ.get("AWS_REGION", "us-east-1")
        db          = boto3.resource("dynamodb", region_name=region)
        _swing_table = db.Table(os.environ.get("SWING_TABLE_NAME", "trading-swing-positions"))
    return _swing_table


def _handle_swing(method: str, path_params: dict, event: dict, user_id: str) -> dict:
    """Handle all /api/swing/positions routes."""

    # ── DELETE /api/swing/positions/{position_id} ─────────────────────────────
    if method == "DELETE":
        position_id = path_params.get("position_id", "")
        if not position_id:
            return _json({"error": "position_id required"}, 400)
        body       = json.loads(event.get("body") or "{}")
        exit_price = body.get("exit_price")
        reason     = body.get("reason", "closed")

        t = _get_swing_table()
        if exit_price is not None:
            # Close the position (record exit price & P&L)
            try:
                exit_price = float(exit_price)
                resp = t.get_item(Key={"user_id": user_id, "position_id": position_id})
                item = resp.get("Item")
                if item:
                    entry = float(item.get("entry_price", 0))
                    qty   = int(item.get("quantity", 0))
                    pnl   = round((exit_price - entry) * qty, 2)
                    status = reason if reason in ("closed", "stopped_out", "target_hit") else "closed"
                    t.update_item(
                        Key={"user_id": user_id, "position_id": position_id},
                        UpdateExpression="SET #s=:s, exit_price=:ep, exit_date=:ed, pnl=:pnl",
                        ExpressionAttributeNames={"#s": "status"},
                        ExpressionAttributeValues={
                            ":s":   status,
                            ":ep":  Decimal(str(round(exit_price, 2))),
                            ":ed":  time.strftime("%Y-%m-%d", time.gmtime()),
                            ":pnl": Decimal(str(pnl)),
                        },
                    )
                    return _json({"closed": position_id, "pnl": pnl})
            except Exception as e:
                return _json({"error": str(e)}, 500)
        else:
            # Hard delete
            t.delete_item(Key={"user_id": user_id, "position_id": position_id})
            return _json({"removed": position_id})

    # ── POST /api/swing/positions ─────────────────────────────────────────────
    if method == "POST":
        body         = json.loads(event.get("body") or "{}")
        symbol       = (body.get("symbol") or "").upper().strip()
        name         = (body.get("name") or symbol).strip()
        entry_price  = body.get("entry_price")
        quantity     = body.get("quantity")
        target_price = body.get("target_price")
        stop_loss    = body.get("stop_loss")
        score        = body.get("entry_signal_score", 0)

        if not symbol:
            return _json({"error": "symbol required"}, 400)
        try:
            entry_price  = float(entry_price)
            quantity     = int(quantity)
            target_price = float(target_price)
            stop_loss    = float(stop_loss)
        except (TypeError, ValueError):
            return _json({"error": "entry_price, quantity, target_price, stop_loss must be numbers"}, 400)

        if entry_price <= 0 or quantity <= 0:
            return _json({"error": "entry_price and quantity must be positive"}, 400)

        position_id = str(uuid.uuid4())
        _get_swing_table().put_item(Item={
            "user_id":            user_id,
            "position_id":        position_id,
            "symbol":             symbol,
            "name":               name,
            "entry_price":        Decimal(str(round(entry_price, 2))),
            "quantity":           quantity,
            "target_price":       Decimal(str(round(target_price, 2))),
            "stop_loss":          Decimal(str(round(stop_loss, 2))),
            "entry_signal_score": Decimal(str(round(float(score), 1))),
            "entry_date":         time.strftime("%Y-%m-%d", time.gmtime()),
            "status":             "active",
            "added_at":           time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        })
        return _json({"added": position_id, "symbol": symbol})

    # ── GET /api/swing/positions ──────────────────────────────────────────────
    from boto3.dynamodb.conditions import Attr
    resp  = _get_swing_table().query(
        KeyConditionExpression=Key("user_id").eq(user_id),
        FilterExpression=Attr("status").eq("active"),
    )
    raw_positions = resp.get("Items", [])

    if not raw_positions:
        return _json({"positions": [], "summary": _empty_swing_summary()})

    # Fetch live prices for unique symbols
    symbols = {p["symbol"] for p in raw_positions}
    prices  = _fetch_prices(symbols)

    enriched = []
    for p in raw_positions:
        sym         = p["symbol"]
        entry_price = float(p.get("entry_price", 0))
        quantity    = int(p.get("quantity", 0))
        target_price = float(p.get("target_price", 0))
        stop_loss   = float(p.get("stop_loss", 0))
        cur         = prices.get(sym, {})
        cur_price   = cur.get("current", 0.0)
        prev_close  = cur.get("prev_close", 0.0)

        invested   = round(entry_price * quantity, 2)
        cur_value  = round(cur_price * quantity, 2) if cur_price else None
        total_gain = round(cur_value - invested, 2) if cur_value is not None else None
        total_pct  = round((total_gain / invested) * 100, 2) if (total_gain is not None and invested) else None
        day_gain   = round((cur_price - prev_close) * quantity, 2) if (cur_price and prev_close) else None

        # Entry date → days held
        entry_date = p.get("entry_date", "")
        days_held  = 0
        if entry_date:
            try:
                from datetime import date
                ed = date.fromisoformat(entry_date)
                days_held = (date.today() - ed).days
            except Exception:
                pass

        # Exit signal: compare current price to target / stop-loss
        exit_signal = "HOLD"
        if cur_price:
            if cur_price >= target_price:
                exit_signal = "TARGET_HIT"
            elif cur_price <= stop_loss:
                exit_signal = "STOP_HIT"
            elif target_price > entry_price and (cur_price - entry_price) >= 0.6 * (target_price - entry_price):
                exit_signal = "TRAIL"   # 60%+ to target — suggest trailing stop

        enriched.append({
            "position_id":        p["position_id"],
            "symbol":             sym,
            "name":               p.get("name", sym),
            "entry_price":        entry_price,
            "quantity":           quantity,
            "target_price":       target_price,
            "stop_loss":          stop_loss,
            "entry_signal_score": float(p.get("entry_signal_score", 0)),
            "entry_date":         entry_date,
            "days_held":          days_held,
            "status":             p.get("status", "active"),
            "current_price":      cur_price if cur_price else None,
            "invested":           invested,
            "current_value":      cur_value,
            "total_gain":         total_gain,
            "total_gain_pct":     total_pct,
            "day_gain":           day_gain,
            "exit_signal":        exit_signal,
        })

    summary = _compute_swing_summary(enriched)
    return _json({"positions": enriched, "summary": summary})


def _compute_swing_summary(positions: list) -> dict:
    total_invested = round(sum(p["invested"] for p in positions), 2)
    current_value  = round(sum(p["current_value"] or p["invested"] for p in positions), 2)
    total_gain     = round(current_value - total_invested, 2)
    total_gain_pct = round((total_gain / total_invested) * 100, 2) if total_invested else 0.0
    alerts         = sum(1 for p in positions if p["exit_signal"] in ("TARGET_HIT", "STOP_HIT", "TRAIL"))
    return {
        "total_invested": total_invested,
        "current_value":  current_value,
        "total_gain":     total_gain,
        "total_gain_pct": total_gain_pct,
        "position_count": len(positions),
        "alert_count":    alerts,
    }


def _empty_swing_summary() -> dict:
    return {"total_invested": 0, "current_value": 0,
            "total_gain": 0, "total_gain_pct": 0,
            "position_count": 0, "alert_count": 0}
