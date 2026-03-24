"""
====================================================
  Stock Fetcher  –  pulls real-time & historical
  data from Yahoo Finance using yfinance (FREE)
====================================================
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional

import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)


class StockFetcher:
    """Fetches stock price data and historical OHLCV from Yahoo Finance."""

    async def get_stock_data(self, symbol: str) -> Optional[dict]:
        """
        Returns a dict with:
          - current_price, prev_close, change_pct
          - hist: last 60 days of OHLCV as a DataFrame
          - info: company meta-data dict
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._fetch, symbol)

    async def get_batch_stock_data(self, symbols: list[str]) -> dict[str, Optional[dict]]:
        """
        Fetch all symbols in one batched yf.download() call.
        Returns {symbol: stock_data_dict or None}.
        Much faster than individual fetches (~1-2 requests vs ~100).
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._fetch_batch, symbols)

    def _fetch_batch(self, symbols: list[str]) -> dict[str, Optional[dict]]:
        """Batch-download historical + intraday data for all symbols at once."""
        results = {}

        # --- Batch download: 1y daily history (for 200-day SMA) ---
        try:
            hist_all = yf.download(
                symbols, period="1y", interval="1d",
                group_by="ticker", threads=True, progress=False,
            )
        except Exception as e:
            logger.error(f"Batch history download failed: {e}")
            hist_all = pd.DataFrame()

        # --- Batch download: 1d intraday (for mini-charts) ---
        try:
            intra_all = yf.download(
                symbols, period="1d", interval="15m",
                group_by="ticker", threads=True, progress=False,
            )
        except Exception as e:
            logger.error(f"Batch intraday download failed: {e}")
            intra_all = pd.DataFrame()

        for symbol in symbols:
            try:
                # Extract per-ticker history
                if len(symbols) == 1:
                    hist = hist_all.copy()
                else:
                    hist = hist_all[symbol].copy() if symbol in hist_all.columns.get_level_values(0) else pd.DataFrame()

                # Drop rows where Close is NaN (ticker had no data)
                if not hist.empty and "Close" in hist.columns:
                    hist = hist.dropna(subset=["Close"])

                if hist.empty or len(hist) < 20:
                    logger.warning(f"{symbol}: Not enough historical data in batch")
                    results[symbol] = None
                    continue

                current_price = round(float(hist["Close"].iloc[-1]), 2)
                prev_close    = round(float(hist["Close"].iloc[-2]), 2)

                if current_price <= 0:
                    results[symbol] = None
                    continue

                change_pct = round(((current_price - prev_close) / prev_close * 100), 2) if prev_close else 0.0

                # Extract per-ticker intraday
                intraday = []
                try:
                    if len(symbols) == 1:
                        intra = intra_all.copy()
                    else:
                        intra = intra_all[symbol].copy() if symbol in intra_all.columns.get_level_values(0) else pd.DataFrame()
                    if not intra.empty and "Close" in intra.columns:
                        intra = intra.dropna(subset=["Close"])
                        intraday = [
                            {"time": str(t), "price": round(float(p), 2)}
                            for t, p in zip(intra.index, intra["Close"])
                        ]
                except Exception:
                    pass

                results[symbol] = {
                    "symbol":        symbol,
                    "current_price": current_price,
                    "prev_close":    prev_close,
                    "change_pct":    change_pct,
                    "volume":        int(hist["Volume"].iloc[-1]) if "Volume" in hist.columns else 0,
                    "avg_volume":    int(hist["Volume"].mean())   if "Volume" in hist.columns else 1,
                    "high_52w":      round(float(hist["High"].max()), 2),
                    "low_52w":       round(float(hist["Low"].min()),  2),
                    "hist":          hist,
                    "intraday":      intraday,
                }

            except Exception as e:
                logger.error(f"Batch parse error for {symbol}: {e}")
                results[symbol] = None

        return results

    # ── Sync worker (runs in thread-pool) ──────────────────
    def _fetch(self, symbol: str) -> Optional[dict]:
        """
        Try symbol as-is, then auto-append .NS / .BO for bare Indian tickers.
        Always returns data identified by the *original* symbol so the
        wishlist store (which saved the original) stays consistent.
        """
        has_suffix = any(symbol.upper().endswith(s) for s in (".NS", ".BO", ".BSE"))
        candidates = [symbol] if has_suffix else [symbol, symbol + ".NS", symbol + ".BO"]

        for candidate in candidates:
            result = self._fetch_candidate(candidate)
            if result:
                if candidate != symbol:
                    logger.info(f"Auto-resolved '{symbol}' → '{candidate}'")
                result["symbol"] = symbol   # keep original as identifier
                return result

        return None

    def _fetch_candidate(self, symbol: str) -> Optional[dict]:
        """Fetch data for a single exact symbol. Returns None if unavailable."""
        try:
            ticker = yf.Ticker(symbol)

            # --- Historical data (1 year for 200-day SMA) ---
            hist = ticker.history(period="1y", interval="1d")
            if hist.empty or len(hist) < 20:
                logger.warning(f"{symbol}: Not enough historical data")
                return None

            # --- Fast info (current price) ---
            info = {}
            try:
                info = ticker.fast_info or {}
            except Exception:
                pass

            current_price = self._safe(info, "last_price") or float(hist["Close"].iloc[-1])
            prev_close    = self._safe(info, "previous_close") or float(hist["Close"].iloc[-2])

            if current_price <= 0:
                return None

            change_pct = ((current_price - prev_close) / prev_close * 100) if prev_close else 0.0

            # --- Intraday data (for today's mini-chart) ---
            intraday = []
            try:
                today = ticker.history(period="1d", interval="15m")
                if not today.empty:
                    intraday = [
                        {"time": str(t), "price": round(float(p), 2)}
                        for t, p in zip(today.index, today["Close"])
                    ]
            except Exception:
                pass

            return {
                "symbol":        symbol,
                "current_price": round(current_price, 2),
                "prev_close":    round(prev_close, 2),
                "change_pct":    round(change_pct, 2),
                "volume":        int(hist["Volume"].iloc[-1]) if "Volume" in hist.columns else 0,
                "avg_volume":    int(hist["Volume"].mean())   if "Volume" in hist.columns else 1,
                "high_52w":      round(float(hist["High"].max()), 2),
                "low_52w":       round(float(hist["Low"].min()),  2),
                "hist":          hist,        # DataFrame used by agents
                "intraday":      intraday,    # list of dicts for chart
            }

        except Exception as e:
            logger.error(f"StockFetcher._fetch_candidate({symbol}): {e}")
            return None

    @staticmethod
    def _safe(obj, key):
        """Safely read from dict or object attribute."""
        try:
            if isinstance(obj, dict):
                return obj.get(key)
            return getattr(obj, key, None)
        except Exception:
            return None
