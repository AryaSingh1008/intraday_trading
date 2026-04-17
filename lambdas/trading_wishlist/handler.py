"""
Lambda handler: GET|POST|DELETE /api/wishlist and GET /api/wishlist/check/{symbol}
Replaces backend/utils/wishlist_store.py (file-based) with DynamoDB.
"""
import json
import os
import time
import boto3

_dynamodb = None
_table    = None


def _get_table():
    global _dynamodb, _table
    if _table is None:
        _dynamodb = boto3.resource("dynamodb", region_name=os.environ.get("AWS_REGION", "us-east-1"))
        _table = _dynamodb.Table(os.environ["WISHLIST_TABLE_NAME"])
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

    user_id = _get_user_id(event)
    table   = _get_table()

    # GET /api/wishlist/check/{symbol}
    if "check" in raw_path and path_params.get("symbol"):
        symbol = path_params["symbol"].upper()
        resp   = table.get_item(Key={"user_id": user_id, "symbol": symbol})
        return _json({"in_wishlist": "Item" in resp})

    # DELETE /api/wishlist/{symbol}
    if method == "DELETE" and path_params.get("symbol"):
        symbol = path_params["symbol"].upper()
        table.delete_item(Key={"user_id": user_id, "symbol": symbol})
        return _json({"removed": symbol})

    # POST /api/wishlist
    if method == "POST":
        body   = json.loads(event.get("body") or "{}")
        symbol = (body.get("symbol") or "").upper().strip()
        name   = (body.get("name") or symbol).strip()
        if not symbol:
            return _json({"error": "symbol required"}, 400)
        table.put_item(Item={
            "user_id":  user_id,
            "symbol":   symbol,
            "name":     name,
            "added_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        })
        return _json({"added": symbol})

    # GET /api/wishlist
    response = table.query(
        KeyConditionExpression=boto3.dynamodb.conditions.Key("user_id").eq(user_id)
    )
    raw_items = response.get("Items", [])
    items     = [{"symbol": i["symbol"], "name": i.get("name", i["symbol"])}
                 for i in raw_items]

    # Enrich with live price data (best-effort — silent on failure)
    if items:
        prices = _fetch_prices({i["symbol"] for i in items})
        for item in items:
            p = prices.get(item["symbol"], {})
            cur        = p.get("current")
            prev_close = p.get("prev_close")
            item["current_price"] = cur
            item["prev_close"]    = prev_close
            if cur and prev_close and prev_close > 0:
                item["change_pct"] = round((cur - prev_close) / prev_close * 100, 2)
            else:
                item["change_pct"] = None

    return _json({"wishlist": items})


def _fetch_prices(symbols: set) -> dict:
    """Fetch current price and previous close for a set of symbols.
    Returns {symbol: {current, prev_close}} — zeros on any failure."""
    result = {sym: {"current": None, "prev_close": None} for sym in symbols}
    if not symbols:
        return result
    try:
        import yfinance as yf
        sym_list = list(symbols)
        data = yf.download(
            sym_list,
            period="2d",
            group_by="ticker",
            threads=True,
            timeout=8,
            progress=False,
        )
        if data.empty:
            return result
        for sym in symbols:
            try:
                if len(symbols) == 1:
                    # Single ticker — newer yfinance returns MultiIndex columns
                    if hasattr(data.columns, "levels"):
                        col_data = data.xs("Close", axis=1, level=0) if "Close" in data.columns.get_level_values(0) else None
                        closes   = col_data.squeeze().dropna() if col_data is not None else None
                    else:
                        closes = data["Close"].dropna() if "Close" in data.columns else None
                else:
                    closes = data[sym]["Close"].dropna() if sym in data.columns.get_level_values(0) else None
                if closes is None or len(closes) == 0:
                    continue
                result[sym] = {
                    "current":    float(closes.iloc[-1]),
                    "prev_close": float(closes.iloc[-2]) if len(closes) >= 2 else float(closes.iloc[-1]),
                }
            except Exception:
                pass
    except Exception:
        pass
    return result


def _json(data: dict, status: int = 200):
    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(data),
    }
