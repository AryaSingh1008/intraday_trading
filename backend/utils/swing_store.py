"""
Swing Position Store — persists the user's active swing/positional trades.

Storage: DynamoDB  trading-swing-positions  (on AWS)
         data/swing_positions.json          (local dev fallback)

DynamoDB schema:
  PK: user_id     (String) — Cognito sub
  SK: position_id (String) — UUID
  Attributes:
    symbol             (String)   e.g. "RELIANCE.NS"
    name               (String)   e.g. "Reliance Industries"
    entry_price        (Number)   price when position was opened
    quantity           (Number)   number of shares
    target_price       (Number)   ATR-based take-profit level
    stop_loss          (Number)   ATR-based stop-loss level
    entry_signal_score (Number)   positional score at time of entry (0-100)
    entry_date         (String)   "YYYY-MM-DD"
    status             (String)   "active" | "closed" | "stopped_out" | "target_hit"
    exit_price         (Number)   optional — set on close
    exit_date          (String)   optional — set on close
    pnl                (Number)   optional — computed on close
    added_at           (String)   ISO 8601 timestamp
"""

import json
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

_TABLE_NAME = os.environ.get("SWING_TABLE_NAME", "trading-swing-positions")

# ── Detect runtime environment ────────────────────────────────────────────────
def _use_dynamo() -> bool:
    """True when running on AWS Lambda."""
    return bool(os.environ.get("AWS_EXECUTION_ENV") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME"))


# ── DynamoDB backend ──────────────────────────────────────────────────────────
def _table():
    import boto3
    return boto3.resource("dynamodb").Table(_TABLE_NAME)


def _dynamo_get_active(user_id: str) -> List[Dict]:
    from boto3.dynamodb.conditions import Key, Attr
    response = _table().query(
        KeyConditionExpression=Key("user_id").eq(user_id),
        FilterExpression=Attr("status").eq("active"),
    )
    return [_to_python(i) for i in response.get("Items", [])]


def _dynamo_get_all(user_id: str) -> List[Dict]:
    from boto3.dynamodb.conditions import Key
    response = _table().query(
        KeyConditionExpression=Key("user_id").eq(user_id),
    )
    return [_to_python(i) for i in response.get("Items", [])]


def _dynamo_add(user_id: str, symbol: str, name: str,
                entry_price: float, quantity: int,
                target_price: float, stop_loss: float,
                entry_signal_score: float) -> str:
    from decimal import Decimal
    position_id = str(uuid.uuid4())
    _table().put_item(Item={
        "user_id":            user_id,
        "position_id":        position_id,
        "symbol":             symbol.upper(),
        "name":               name,
        "entry_price":        Decimal(str(round(entry_price, 2))),
        "quantity":           int(quantity),
        "target_price":       Decimal(str(round(target_price, 2))),
        "stop_loss":          Decimal(str(round(stop_loss, 2))),
        "entry_signal_score": Decimal(str(round(entry_signal_score, 1))),
        "entry_date":         datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "status":             "active",
        "added_at":           datetime.now(timezone.utc).isoformat(),
    })
    return position_id


def _dynamo_close(user_id: str, position_id: str,
                  exit_price: float, reason: str) -> bool:
    from decimal import Decimal
    t    = _table()
    resp = t.get_item(Key={"user_id": user_id, "position_id": position_id})
    item = resp.get("Item")
    if not item:
        return False
    entry  = float(item.get("entry_price", 0))
    qty    = int(item.get("quantity", 0))
    pnl    = round((exit_price - entry) * qty, 2)
    status = reason if reason in ("closed", "stopped_out", "target_hit") else "closed"
    t.update_item(
        Key={"user_id": user_id, "position_id": position_id},
        UpdateExpression="SET #s=:s, exit_price=:ep, exit_date=:ed, pnl=:pnl",
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={
            ":s":  status,
            ":ep": Decimal(str(round(exit_price, 2))),
            ":ed": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            ":pnl": Decimal(str(pnl)),
        },
    )
    return True


def _dynamo_remove(user_id: str, position_id: str) -> bool:
    t    = _table()
    resp = t.get_item(Key={"user_id": user_id, "position_id": position_id})
    if not resp.get("Item"):
        return False
    t.delete_item(Key={"user_id": user_id, "position_id": position_id})
    return True


# ── File backend (local dev) ──────────────────────────────────────────────────
_DATA_DIR   = os.path.join(os.path.dirname(__file__), "..", "..", "data")
_SWING_FILE = os.path.join(_DATA_DIR, "swing_positions.json")


def _ensure_dir():
    os.makedirs(_DATA_DIR, exist_ok=True)


def _file_read() -> List[Dict]:
    _ensure_dir()
    if not os.path.exists(_SWING_FILE):
        return []
    try:
        with open(_SWING_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return []


def _file_write(items: List[Dict]):
    _ensure_dir()
    with open(_SWING_FILE, "w") as f:
        json.dump(items, f, indent=2)


# ── Decimal → float conversion (DynamoDB returns Decimal) ────────────────────
def _to_python(item: dict) -> dict:
    from decimal import Decimal
    return {k: float(v) if isinstance(v, Decimal) else v for k, v in item.items()}


# ── Public API ────────────────────────────────────────────────────────────────

def get_active(user_id: str) -> List[Dict]:
    """Return all positions with status='active' for this user."""
    try:
        if _use_dynamo():
            return _dynamo_get_active(user_id)
        return [p for p in _file_read()
                if p.get("user_id") == user_id and p.get("status") == "active"]
    except Exception as e:
        logger.warning(f"swing_store.get_active error: {e}")
        return []


def get_all(user_id: str) -> List[Dict]:
    """Return all positions (active + closed) for this user."""
    try:
        if _use_dynamo():
            return _dynamo_get_all(user_id)
        return [p for p in _file_read() if p.get("user_id") == user_id]
    except Exception as e:
        logger.warning(f"swing_store.get_all error: {e}")
        return []


def add_position(user_id: str, symbol: str, name: str,
                 entry_price: float, quantity: int,
                 target_price: float, stop_loss: float,
                 entry_signal_score: float = 0.0) -> Optional[str]:
    """
    Open a new swing position. Returns position_id on success, None on error.
    """
    try:
        if _use_dynamo():
            return _dynamo_add(user_id, symbol, name,
                               entry_price, quantity,
                               target_price, stop_loss,
                               entry_signal_score)
        # File backend
        position_id = str(uuid.uuid4())
        items = _file_read()
        items.append({
            "user_id":            user_id,
            "position_id":        position_id,
            "symbol":             symbol.upper(),
            "name":               name,
            "entry_price":        round(entry_price, 2),
            "quantity":           int(quantity),
            "target_price":       round(target_price, 2),
            "stop_loss":          round(stop_loss, 2),
            "entry_signal_score": round(entry_signal_score, 1),
            "entry_date":         datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "status":             "active",
            "added_at":           datetime.now(timezone.utc).isoformat(),
        })
        _file_write(items)
        return position_id
    except Exception as e:
        logger.warning(f"swing_store.add_position error: {e}")
        return None


def close_position(user_id: str, position_id: str,
                   exit_price: float, reason: str = "closed") -> bool:
    """
    Close a position. reason = "closed" | "stopped_out" | "target_hit"
    """
    try:
        if _use_dynamo():
            return _dynamo_close(user_id, position_id, exit_price, reason)
        items  = _file_read()
        status = reason if reason in ("closed", "stopped_out", "target_hit") else "closed"
        changed = False
        for p in items:
            if p.get("user_id") == user_id and p.get("position_id") == position_id:
                pnl = round((exit_price - p.get("entry_price", 0)) * p.get("quantity", 0), 2)
                p.update({
                    "status":     status,
                    "exit_price": round(exit_price, 2),
                    "exit_date":  datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                    "pnl":        pnl,
                })
                changed = True
                break
        if changed:
            _file_write(items)
        return changed
    except Exception as e:
        logger.warning(f"swing_store.close_position error: {e}")
        return False


def remove_position(user_id: str, position_id: str) -> bool:
    """Hard-delete a position (regardless of status)."""
    try:
        if _use_dynamo():
            return _dynamo_remove(user_id, position_id)
        items = _file_read()
        new   = [p for p in items
                 if not (p.get("user_id") == user_id and p.get("position_id") == position_id)]
        if len(new) == len(items):
            return False
        _file_write(new)
        return True
    except Exception as e:
        logger.warning(f"swing_store.remove_position error: {e}")
        return False
