"""
Wishlist Store  –  persists the user's watchlist to a local JSON file.
Location: data/wishlist.json  (created automatically on first use)
"""

import json
import logging
import os
from typing import List, Dict

logger = logging.getLogger(__name__)

_DATA_DIR  = os.path.join(os.path.dirname(__file__), "..", "..", "data")
_WISH_FILE = os.path.join(_DATA_DIR, "wishlist.json")


def _ensure_dir():
    os.makedirs(_DATA_DIR, exist_ok=True)


def _read() -> List[Dict]:
    _ensure_dir()
    if not os.path.exists(_WISH_FILE):
        return []
    try:
        with open(_WISH_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return []


def _write(items: List[Dict]):
    _ensure_dir()
    with open(_WISH_FILE, "w") as f:
        json.dump(items, f, indent=2)


def get_all() -> List[Dict]:
    return _read()


def add(symbol: str, name: str) -> bool:
    """Add a stock. Returns False if already present."""
    items = _read()
    if any(i["symbol"] == symbol.upper() for i in items):
        return False
    items.append({"symbol": symbol.upper(), "name": name})
    _write(items)
    return True


def remove(symbol: str) -> bool:
    """Remove a stock. Returns False if not found."""
    items = _read()
    new = [i for i in items if i["symbol"] != symbol.upper()]
    if len(new) == len(items):
        return False
    _write(new)
    return True


def exists(symbol: str) -> bool:
    return any(i["symbol"] == symbol.upper() for i in _read())
