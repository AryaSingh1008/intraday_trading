"""
Options Fetcher – fetches option chain data for Indian indices/stocks.
Primary  : NSE public API (curl_cffi TLS fingerprinting — Lambda-compatible)
Fallback : yfinance (Yahoo Finance) option chain
Last resort: synthetic chain using allIndices spot price

Playwright has been removed — it requires headless Chrome which cannot
run on AWS Lambda.  curl_cffi impersonates Chrome at the TLS layer instead.
"""

import asyncio
import logging
import math
import time
from datetime import datetime
from typing import Optional, List, Dict

try:
    from curl_cffi import requests
    _USE_CURL = True
except ImportError:
    import requests
    _USE_CURL = False

from backend.utils.greeks import compute_greeks

logger = logging.getLogger(__name__)

# NSE API endpoints
NSE_BASE      = "https://www.nseindia.com"
NSE_INDEX_URL = "https://www.nseindia.com/api/option-chain-indices?symbol={symbol}"
NSE_STOCK_URL = "https://www.nseindia.com/api/option-chain-equities?symbol={symbol}"

# Indices that use the index endpoint (vs equity endpoint)
NSE_INDICES = {"NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY"}

# Map friendly names → Yahoo Finance symbols (fallback)
OPTIONS_SYMBOLS: Dict[str, str] = {
    "NIFTY":     "^NSEI",
    "BANKNIFTY": "^NSEBANK",
    "RELIANCE":  "RELIANCE.NS",
    "TCS":       "TCS.NS",
    "INFY":      "INFY.NS",
    "HDFCBANK":  "HDFCBANK.NS",
    "ICICIBANK": "ICICIBANK.NS",
}

_HEADERS = {
    "User-Agent":      "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/122.0.0.0 Safari/537.36",
    "Accept":          "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer":         "https://www.nseindia.com/",
    "X-Requested-With": "XMLHttpRequest",
}


def _safe_float(val) -> Optional[float]:
    try:
        f = float(val)
        return None if (math.isnan(f) or math.isinf(f)) else f
    except Exception:
        return None


def _days_to_expiry(expiry_str: str) -> int:
    """
    Parse NSE expiry string like '27-Mar-2025' or '2025-03-27' and
    return calendar days remaining from today.  Returns 1 on any parse error
    (avoids division-by-zero in Black-Scholes).
    """
    for fmt in ("%d-%b-%Y", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            exp_dt = datetime.strptime(expiry_str.strip(), fmt)
            dte    = (exp_dt.date() - datetime.now().date()).days
            return max(1, dte)
        except ValueError:
            continue
    return 1


def _nse_session():
    """Create a Session with NSE cookies, using curl_cffi if available."""
    if _USE_CURL:
        s = requests.Session(impersonate="chrome120")
    else:
        s = requests.Session()
        s.headers.update(_HEADERS)
    try:
        s.get(NSE_BASE, timeout=10)
        time.sleep(0.5)
    except Exception as e:
        logger.warning(f"NSE homepage fetch failed: {e}")
    return s


class OptionsFetcher:

    # OI snapshot from the previous fetch — used to compute OI change
    _prev_oi: Dict[str, Dict[float, dict]] = {}

    def __init__(self):
        self._session: Optional[requests.Session] = None
        self._session_ts: float = 0

    def _get_session(self) -> requests.Session:
        # Refresh session every 5 minutes
        if self._session is None or (time.time() - self._session_ts) > 300:
            self._session = _nse_session()
            self._session_ts = time.time()
        return self._session

    async def get_option_chain(self, symbol: str) -> Optional[Dict]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._fetch, symbol.upper())

    # ── private ──────────────────────────────────────────────────────────────

    def _fetch_real_spot(self, symbol: str) -> Optional[float]:
        """Get real spot price from NSE allIndices (this endpoint works without JS)."""
        INDEX_MAP = {
            "NIFTY":     "NIFTY 50",
            "BANKNIFTY": "NIFTY BANK",
            "FINNIFTY":  "NIFTY FIN SERVICE",
        }
        try:
            session = self._get_session()
            r = session.get("https://www.nseindia.com/api/allIndices", timeout=10)
            if r.status_code == 200:
                data = r.json()
                target = INDEX_MAP.get(symbol)
                for item in data.get("data", []):
                    if target and item.get("index") == target:
                        return _safe_float(item.get("last"))
                    if not target and item.get("indexSymbol") == symbol:
                        return _safe_float(item.get("last"))
        except Exception as e:
            logger.debug(f"allIndices spot lookup failed: {e}")
        return None

    def _fetch(self, symbol: str) -> Optional[Dict]:
        """
        Fetch priority:
        1. Direct NSE API (curl_cffi TLS fingerprinting — works on Lambda)
        2. yfinance (works for some stock options, not Indian indices)
        3. Synthetic chain with real spot from allIndices (last resort)

        Note: Playwright (headless Chrome) is not used — it cannot run on
        AWS Lambda.  curl_cffi is the primary NSE data path.
        """
        # ── 1. Direct NSE API ─────────────────────────────────────────────────
        result = self._fetch_nse(symbol)
        if result:
            return result

        # ── 2. yfinance ───────────────────────────────────────────────────────
        logger.info(f"NSE fetch failed for {symbol}, trying yfinance...")
        result = self._fetch_yfinance(symbol)
        if result:
            return result

        # ── 3. Synthetic with real spot ───────────────────────────────────────
        spot = self._fetch_real_spot(symbol)
        return self._synthetic_chain(symbol, spot)

    # ── Greeks + OI change helpers ────────────────────────────────────────────

    def _enrich_rows(
        self,
        symbol: str,
        chain_rows: List[Dict],
        spot: Optional[float],
        expiry: str,
    ) -> None:
        """
        Mutates each row in *chain_rows* in-place:
        - Adds call/put Greeks (delta, gamma, theta, vega)
        - Adds call_oi_change / put_oi_change vs previous fetch snapshot
        """
        dte  = _days_to_expiry(expiry)
        prev = OptionsFetcher._prev_oi.get(symbol, {})

        for row in chain_rows:
            strike = row["strike"]

            # ── Greeks ──────────────────────────────────────────────────────
            if spot:
                c_g = compute_greeks(spot, strike, dte, row.get("call_iv"), "CE")
                p_g = compute_greeks(spot, strike, dte, row.get("put_iv"),  "PE")
            else:
                c_g = p_g = None

            row["call_delta"] = c_g["delta"] if c_g else None
            row["call_gamma"] = c_g["gamma"] if c_g else None
            row["call_theta"] = c_g["theta"] if c_g else None
            row["call_vega"]  = c_g["vega"]  if c_g else None
            row["put_delta"]  = p_g["delta"] if p_g else None
            row["put_gamma"]  = p_g["gamma"] if p_g else None
            row["put_theta"]  = p_g["theta"] if p_g else None
            row["put_vega"]   = p_g["vega"]  if p_g else None

            # ── OI Change ────────────────────────────────────────────────────
            prev_strike = prev.get(strike, {})
            # On first fetch prev_strike is empty → change = 0 (correct)
            row["call_oi_change"] = row["call_oi"] - prev_strike.get("call_oi", row["call_oi"])
            row["put_oi_change"]  = row["put_oi"]  - prev_strike.get("put_oi",  row["put_oi"])

        # Update OI snapshot for next fetch
        OptionsFetcher._prev_oi[symbol] = {
            r["strike"]: {"call_oi": r["call_oi"], "put_oi": r["put_oi"]}
            for r in chain_rows
        }

    # ── NSE API ──────────────────────────────────────────────────────────────

    def _fetch_nse(self, symbol: str) -> Optional[Dict]:
        try:
            session = self._get_session()
            if symbol in NSE_INDICES:
                url = NSE_INDEX_URL.format(symbol=symbol)
            else:
                url = NSE_STOCK_URL.format(symbol=symbol)

            resp = session.get(url, timeout=15)
            if resp.status_code != 200:
                logger.warning(f"NSE API returned {resp.status_code} for {symbol}")
                # Force session refresh on next call
                self._session = None
                return None

            data = resp.json()
            return self._parse_nse(symbol, data)

        except Exception as e:
            logger.warning(f"NSE fetch error for {symbol}: {e}")
            self._session = None
            return None

    def _parse_nse(self, symbol: str, data: dict) -> Optional[Dict]:
        try:
            records = data.get("records", {})
            spot    = _safe_float(records.get("underlyingValue"))
            expiry_dates = records.get("expiryDates", [])
            if not expiry_dates:
                return None

            # Use nearest expiry
            expiry = expiry_dates[0]

            # Filter for nearest expiry
            raw_chain = [
                r for r in records.get("data", [])
                if r.get("expiryDate") == expiry
            ]
            if not raw_chain:
                return None

            # Determine ATM strike
            all_strikes = sorted({r["strikePrice"] for r in raw_chain})
            atm_strike  = min(all_strikes, key=lambda x: abs(x - spot)) if spot else None

            # Keep ±5 strikes around ATM
            if atm_strike and len(all_strikes) > 11:
                idx = all_strikes.index(atm_strike)
                lo  = max(0, idx - 5)
                hi  = min(len(all_strikes), idx + 6)
                all_strikes = all_strikes[lo:hi]

            # Build lookup by strike
            calls_by_strike: Dict[float, dict] = {}
            puts_by_strike:  Dict[float, dict] = {}
            for r in raw_chain:
                s = r["strikePrice"]
                if "CE" in r:
                    calls_by_strike[s] = r["CE"]
                if "PE" in r:
                    puts_by_strike[s] = r["PE"]

            chain_rows: List[Dict] = []
            total_call_oi = 0
            total_put_oi  = 0

            for strike in all_strikes:
                c = calls_by_strike.get(strike, {})
                p = puts_by_strike.get(strike, {})

                c_oi  = int(_safe_float(c.get("openInterest",  0)) or 0)
                p_oi  = int(_safe_float(p.get("openInterest",  0)) or 0)
                c_ltp = _safe_float(c.get("lastPrice"))
                p_ltp = _safe_float(p.get("lastPrice"))
                c_iv  = _safe_float(c.get("impliedVolatility"))
                p_iv  = _safe_float(p.get("impliedVolatility"))

                total_call_oi += c_oi
                total_put_oi  += p_oi

                chain_rows.append({
                    "strike":   strike,
                    "call_oi":  c_oi,
                    "call_ltp": c_ltp,
                    "call_iv":  round(c_iv, 1) if c_iv else None,
                    "put_oi":   p_oi,
                    "put_ltp":  p_ltp,
                    "put_iv":   round(p_iv, 1) if p_iv else None,
                    "is_atm":   (strike == atm_strike),
                })

            # Enrich with Greeks + OI change
            self._enrich_rows(symbol, chain_rows, spot, expiry)

            pcr = round(total_put_oi / total_call_oi, 2) if total_call_oi > 0 else None

            return {
                "symbol":         symbol,
                "spot":           round(spot, 2) if spot else None,
                "expiry":         expiry,
                "atm_strike":     atm_strike,
                "chain":          chain_rows,
                "total_call_oi":  total_call_oi,
                "total_put_oi":   total_put_oi,
                "pcr":            pcr,
                "source":         "nse",
            }

        except Exception as e:
            logger.warning(f"NSE parse error for {symbol}: {e}")
            return None

    # ── yfinance fallback ─────────────────────────────────────────────────────

    def _fetch_yfinance(self, symbol: str) -> Optional[Dict]:
        try:
            import yfinance as yf
        except ImportError:
            logger.error("yfinance not installed")
            return self._synthetic_chain(symbol, None)

        yf_sym = OPTIONS_SYMBOLS.get(symbol, symbol)

        try:
            ticker = yf.Ticker(yf_sym)

            info = ticker.fast_info
            spot = _safe_float(getattr(info, "last_price", None))
            if spot is None:
                hist = ticker.history(period="1d", interval="1m")
                spot = _safe_float(hist["Close"].iloc[-1]) if not hist.empty else None

            try:
                expiries = ticker.options
            except Exception:
                expiries = []

            if not expiries:
                return self._synthetic_chain(symbol, spot)

            expiry = expiries[0]
            chain  = ticker.option_chain(expiry)
            calls  = chain.calls
            puts   = chain.puts

            if calls.empty or puts.empty:
                return self._synthetic_chain(symbol, spot)

            if spot:
                all_strikes = sorted(set(calls["strike"].tolist()))
                atm_strike  = min(all_strikes, key=lambda x: abs(x - spot))
            else:
                atm_strike = None

            calls_dict = {row["strike"]: row for _, row in calls.iterrows()}
            puts_dict  = {row["strike"]: row for _, row in puts.iterrows()}

            all_strikes = sorted(set(list(calls_dict.keys()) + list(puts_dict.keys())))
            if atm_strike and len(all_strikes) > 10:
                atm_idx = min(range(len(all_strikes)),
                              key=lambda i: abs(all_strikes[i] - atm_strike))
                lo = max(0, atm_idx - 5)
                hi = min(len(all_strikes), atm_idx + 6)
                all_strikes = all_strikes[lo:hi]

            chain_rows: List[Dict] = []
            total_call_oi = 0
            total_put_oi  = 0

            for strike in all_strikes:
                c = calls_dict.get(strike, {})
                p = puts_dict.get(strike, {})

                c_oi  = int(_safe_float(c.get("openInterest",  0)) or 0)
                p_oi  = int(_safe_float(p.get("openInterest",  0)) or 0)
                c_ltp = _safe_float(c.get("lastPrice"))
                p_ltp = _safe_float(p.get("lastPrice"))
                # yfinance returns IV as decimal (0.20) → convert to percent (20.0)
                c_iv  = _safe_float(c.get("impliedVolatility"))
                p_iv  = _safe_float(p.get("impliedVolatility"))

                total_call_oi += c_oi
                total_put_oi  += p_oi

                chain_rows.append({
                    "strike":   strike,
                    "call_oi":  c_oi,
                    "call_ltp": c_ltp,
                    "call_iv":  round(c_iv * 100, 1) if c_iv else None,
                    "put_oi":   p_oi,
                    "put_ltp":  p_ltp,
                    "put_iv":   round(p_iv * 100, 1) if p_iv else None,
                    "is_atm":   (abs(strike - atm_strike) < 1e-9) if atm_strike else False,
                })

            # Enrich with Greeks + OI change
            self._enrich_rows(symbol, chain_rows, spot, expiry)

            pcr = round(total_put_oi / total_call_oi, 2) if total_call_oi > 0 else None

            return {
                "symbol":         symbol,
                "spot":           round(spot, 2) if spot else None,
                "expiry":         expiry,
                "atm_strike":     atm_strike,
                "chain":          chain_rows,
                "total_call_oi":  total_call_oi,
                "total_put_oi":   total_put_oi,
                "pcr":            pcr,
                "source":         "yfinance",
            }

        except Exception as e:
            logger.warning(f"yfinance options error for {symbol}: {e}")
            return self._synthetic_chain(symbol, None)

    # ── synthetic last-resort fallback ────────────────────────────────────────

    def _synthetic_chain(self, symbol: str, spot: Optional[float]) -> Dict:
        if spot is None:
            spot = 22500.0 if symbol == "NIFTY" else 48000.0 if symbol == "BANKNIFTY" else 1000.0

        step   = 50 if symbol == "NIFTY" else 100 if symbol == "BANKNIFTY" else 10
        atm    = round(spot / step) * step
        strikes = [atm + step * i for i in range(-5, 6)]

        chain_rows = [
            {
                "strike":         s,
                "call_oi":        0, "call_ltp": None, "call_iv": None,
                "put_oi":         0, "put_ltp":  None, "put_iv":  None,
                "is_atm":         (s == atm),
                "call_oi_change": 0, "put_oi_change": 0,
                "call_delta": None, "call_gamma": None,
                "call_theta": None, "call_vega":  None,
                "put_delta":  None, "put_gamma":  None,
                "put_theta":  None, "put_vega":   None,
            }
            for s in strikes
        ]

        return {
            "symbol":        symbol,
            "spot":          round(spot, 2),
            "expiry":        "N/A",
            "atm_strike":    atm,
            "chain":         chain_rows,
            "total_call_oi": 0,
            "total_put_oi":  0,
            "pcr":           None,
            "source":        "synthetic",
        }
