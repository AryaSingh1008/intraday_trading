"""
IV History Store
================
Persists a rolling 30-day history of ATM Implied Volatility per symbol.
Used to compute IV Percentile — essential context for options pricing.

Storage: DynamoDB  trading-iv-history  (on AWS)
         data/iv_history.json          (local dev fallback)

Format : PK=symbol, SK=date "YYYY-MM-DD",  iv=float, expires_at=TTL

Functions
---------
append_iv(symbol, iv_value)
    Record today's IV reading.  Deduplicated by date, max 30 entries kept.

get_iv_percentile(symbol, current_iv)
    Rank-based IV Percentile (0–100).  Returns None if < 5 historical points.
"""

import json
import logging
import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)

# ── Storage config ─────────────────────────────────────────────────────────────
_TABLE_NAME   = os.environ.get("IV_HISTORY_TABLE_NAME", "trading-iv-history")
_MAX_DAYS     = 30
_MIN_READINGS = 5   # minimum before we return a percentile

# ── Detect runtime environment ────────────────────────────────────────────────
def _use_dynamo() -> bool:
    """True when running on AWS Lambda (AWS_EXECUTION_ENV set)."""
    return bool(os.environ.get("AWS_EXECUTION_ENV") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME"))


# ── DynamoDB backend ───────────────────────────────────────────────────────────
def _dynamo_client():
    import boto3
    return boto3.resource("dynamodb").Table(_TABLE_NAME)


def _dynamo_append(symbol: str, iv_value: float) -> None:
    table = _dynamo_client()
    today = datetime.utcnow().strftime("%Y-%m-%d")
    # TTL = 31 days from now
    expires_at = int((datetime.utcnow() + timedelta(days=31)).timestamp())
    table.put_item(Item={
        "symbol":     symbol,
        "date":       today,
        "iv":         str(round(float(iv_value), 2)),   # DynamoDB Decimal-safe
        "expires_at": expires_at,
    })


def _dynamo_get_history(symbol: str) -> List[dict]:
    """Query the last 30 days of IV readings for symbol."""
    from boto3.dynamodb.conditions import Key
    table     = _dynamo_client()
    cutoff    = (datetime.utcnow() - timedelta(days=_MAX_DAYS)).strftime("%Y-%m-%d")
    response  = table.query(
        KeyConditionExpression=Key("symbol").eq(symbol) & Key("date").gte(cutoff)
    )
    items = response.get("Items", [])
    return [{"date": i["date"], "iv": float(i["iv"])} for i in items]


# ── File backend (local dev) ───────────────────────────────────────────────────
_DIR  = os.path.join(os.path.dirname(__file__), "..", "..", "data")
_FILE = os.path.join(_DIR, "iv_history.json")


def _ensure_dir() -> None:
    os.makedirs(_DIR, exist_ok=True)


def _file_load() -> Dict[str, List[dict]]:
    _ensure_dir()
    if not os.path.exists(_FILE):
        return {}
    try:
        with open(_FILE, "r") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception as e:
        logger.warning(f"iv_history_store: load error: {e}")
        return {}


def _file_save(data: Dict[str, List[dict]]) -> None:
    _ensure_dir()
    try:
        with open(_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.warning(f"iv_history_store: save error: {e}")


def _file_append(symbol: str, iv_value: float) -> None:
    today = datetime.now().strftime("%Y-%m-%d")
    data  = _file_load()
    hist  = data.get(symbol, [])
    hist  = [h for h in hist if h.get("date") != today]
    hist.append({"date": today, "iv": round(float(iv_value), 2)})
    cutoff = (datetime.now() - timedelta(days=_MAX_DAYS)).strftime("%Y-%m-%d")
    hist   = [h for h in hist if h.get("date", "") >= cutoff]
    hist   = sorted(hist, key=lambda h: h["date"])
    data[symbol] = hist
    _file_save(data)


def _file_get_history(symbol: str) -> List[dict]:
    return _file_load().get(symbol, [])


# ── Public API ────────────────────────────────────────────────────────────────

def append_iv(symbol: str, iv_value: Optional[float]) -> None:
    """
    Record today's ATM IV for *symbol*.
    Call this once per successful options fetch (not for synthetic data).
    """
    if iv_value is None or iv_value <= 0:
        return
    try:
        if _use_dynamo():
            _dynamo_append(symbol, iv_value)
        else:
            _file_append(symbol, iv_value)
    except Exception as e:
        logger.warning(f"iv_history_store.append_iv error: {e}")


def get_iv_percentile(symbol: str, current_iv: Optional[float]) -> Optional[float]:
    """
    Return the IV Percentile (0–100) of *current_iv* relative to the
    30-day historical distribution.

    Returns None if:
    - current_iv is None or zero
    - fewer than _MIN_READINGS historical data points exist
    """
    if current_iv is None or current_iv <= 0:
        return None
    try:
        if _use_dynamo():
            hist = _dynamo_get_history(symbol)
        else:
            hist = _file_get_history(symbol)
    except Exception as e:
        logger.warning(f"iv_history_store.get_iv_percentile error: {e}")
        return None

    if len(hist) < _MIN_READINGS:
        return None

    historical_ivs = [h["iv"] for h in hist if isinstance(h.get("iv"), (int, float))]
    if len(historical_ivs) < _MIN_READINGS:
        return None

    below = sum(1 for iv in historical_ivs if iv < current_iv)
    pct   = (below / len(historical_ivs)) * 100.0
    return round(pct, 1)


def get_history(symbol: str) -> List[dict]:
    """Return the raw history list for *symbol* (for debugging / display)."""
    try:
        if _use_dynamo():
            return _dynamo_get_history(symbol)
        else:
            return _file_get_history(symbol)
    except Exception as e:
        logger.warning(f"iv_history_store.get_history error: {e}")
        return []
