"""
Wishlist Store — persists the user's watchlist.

Storage: DynamoDB  trading-wishlist  (on AWS)
         data/wishlist.json          (local dev fallback)

DynamoDB schema:
  PK: user_id (String) — hardcoded "default" for single-user mode
  SK: symbol  (String)
  Attributes: name (String), added_at (String)
"""

import json
import logging
import os
from datetime import datetime, timezone
from typing import List, Dict

logger = logging.getLogger(__name__)

_TABLE_NAME = os.environ.get("WISHLIST_TABLE_NAME", "trading-wishlist")
_USER_ID    = "default"   # single-user; extend later with Cognito

# ── Detect runtime environment ────────────────────────────────────────────────
def _use_dynamo() -> bool:
    """True when running on AWS Lambda."""
    return bool(os.environ.get("AWS_EXECUTION_ENV") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME"))


# ── DynamoDB backend ───────────────────────────────────────────────────────────
def _table():
    import boto3
    return boto3.resource("dynamodb").Table(_TABLE_NAME)


def _dynamo_get_all() -> List[Dict]:
    from boto3.dynamodb.conditions import Key
    response = _table().query(
        KeyConditionExpression=Key("user_id").eq(_USER_ID)
    )
    return [
        {"symbol": i["symbol"], "name": i.get("name", i["symbol"])}
        for i in response.get("Items", [])
    ]


def _dynamo_add(symbol: str, name: str) -> bool:
    t = _table()
    resp = t.get_item(Key={"user_id": _USER_ID, "symbol": symbol.upper()})
    if resp.get("Item"):
        return False
    t.put_item(Item={
        "user_id":  _USER_ID,
        "symbol":   symbol.upper(),
        "name":     name,
        "added_at": datetime.now(timezone.utc).isoformat(),
    })
    return True


def _dynamo_remove(symbol: str) -> bool:
    t    = _table()
    resp = t.get_item(Key={"user_id": _USER_ID, "symbol": symbol.upper()})
    if not resp.get("Item"):
        return False
    t.delete_item(Key={"user_id": _USER_ID, "symbol": symbol.upper()})
    return True


def _dynamo_exists(symbol: str) -> bool:
    resp = _table().get_item(Key={"user_id": _USER_ID, "symbol": symbol.upper()})
    return bool(resp.get("Item"))


# ── File backend (local dev) ───────────────────────────────────────────────────
_DATA_DIR  = os.path.join(os.path.dirname(__file__), "..", "..", "data")
_WISH_FILE = os.path.join(_DATA_DIR, "wishlist.json")


def _ensure_dir():
    os.makedirs(_DATA_DIR, exist_ok=True)


def _file_read() -> List[Dict]:
    _ensure_dir()
    if not os.path.exists(_WISH_FILE):
        return []
    try:
        with open(_WISH_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return []


def _file_write(items: List[Dict]):
    _ensure_dir()
    with open(_WISH_FILE, "w") as f:
        json.dump(items, f, indent=2)


# ── Public API ────────────────────────────────────────────────────────────────

def get_all() -> List[Dict]:
    try:
        if _use_dynamo():
            return _dynamo_get_all()
        return _file_read()
    except Exception as e:
        logger.warning(f"wishlist_store.get_all error: {e}")
        return []


def add(symbol: str, name: str) -> bool:
    """Add a stock. Returns False if already present."""
    try:
        if _use_dynamo():
            return _dynamo_add(symbol, name)
        items = _file_read()
        if any(i["symbol"] == symbol.upper() for i in items):
            return False
        items.append({"symbol": symbol.upper(), "name": name})
        _file_write(items)
        return True
    except Exception as e:
        logger.warning(f"wishlist_store.add error: {e}")
        return False


def remove(symbol: str) -> bool:
    """Remove a stock. Returns False if not found."""
    try:
        if _use_dynamo():
            return _dynamo_remove(symbol)
        items = _file_read()
        new = [i for i in items if i["symbol"] != symbol.upper()]
        if len(new) == len(items):
            return False
        _file_write(new)
        return True
    except Exception as e:
        logger.warning(f"wishlist_store.remove error: {e}")
        return False


def exists(symbol: str) -> bool:
    try:
        if _use_dynamo():
            return _dynamo_exists(symbol)
        return any(i["symbol"] == symbol.upper() for i in _file_read())
    except Exception as e:
        logger.warning(f"wishlist_store.exists error: {e}")
        return False
