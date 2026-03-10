"""
Black-Scholes Greeks Calculator
================================
Computes Delta, Gamma, Theta, Vega for European-style options.
Suitable for Indian index options (NIFTY, BANKNIFTY) which are
cash-settled European options.

Note: American-style exercise, dividends, and volatility smile
are NOT modelled. Values are approximate but suitable for
directional trading guidance.
"""

import math
from typing import Optional, Dict

try:
    from scipy.stats import norm as _norm
    _HAS_SCIPY = True
except ImportError:
    _HAS_SCIPY = False


# ── Constants ─────────────────────────────────────────────────────────────────
# India 10-year Govt bond / RBI repo rate proxy (update periodically)
DEFAULT_RISK_FREE_RATE = 0.067   # 6.7%


# ── Fallback normal CDF (if scipy not available) ─────────────────────────────
def _ncdf(x: float) -> float:
    """Standard normal CDF using math.erfc for scipy-free fallback."""
    return 0.5 * math.erfc(-x / math.sqrt(2))


def _npdf(x: float) -> float:
    """Standard normal PDF."""
    return math.exp(-0.5 * x * x) / math.sqrt(2 * math.pi)


def _N(x: float) -> float:
    if _HAS_SCIPY:
        return float(_norm.cdf(x))
    return _ncdf(x)


def _n(x: float) -> float:
    if _HAS_SCIPY:
        return float(_norm.pdf(x))
    return _npdf(x)


# ── Main function ─────────────────────────────────────────────────────────────

def compute_greeks(
    spot: float,
    strike: float,
    days_to_expiry: int,
    iv_pct: float,
    option_type: str,
    risk_free_rate: float = DEFAULT_RISK_FREE_RATE,
) -> Optional[Dict[str, float]]:
    """
    Compute Black-Scholes Greeks for a single option.

    Parameters
    ----------
    spot            : current underlying price (e.g. 24400.0)
    strike          : option strike price (e.g. 24400.0)
    days_to_expiry  : calendar days until expiry (e.g. 7)
    iv_pct          : implied volatility as a percentage (e.g. 14.5 for 14.5%)
    option_type     : "CE" (call) or "PE" (put)
    risk_free_rate  : annualised risk-free rate as decimal (default 6.7%)

    Returns
    -------
    dict with keys: delta, gamma, theta, vega
        delta : directional exposure (-1 to +1)
        gamma : rate of change of delta (per ₹1 move)
        theta : time decay (₹ per day)
        vega  : sensitivity to 1% IV change (₹)
    None if inputs are invalid / insufficient.
    """
    # ── Validation ────────────────────────────────────────────────────────────
    try:
        spot   = float(spot)
        strike = float(strike)
        dte    = int(days_to_expiry)
        iv_pct = float(iv_pct)
    except (TypeError, ValueError):
        return None

    if dte <= 0 or iv_pct <= 0 or spot <= 0 or strike <= 0:
        return None

    opt = option_type.upper()
    if opt not in ("CE", "PE"):
        return None

    # ── Black-Scholes variables ───────────────────────────────────────────────
    S     = spot
    K     = strike
    T     = dte / 365.0          # time in years
    r     = risk_free_rate
    sigma = iv_pct / 100.0       # convert % to decimal

    sqrt_T = math.sqrt(T)

    try:
        d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * sqrt_T)
        d2 = d1 - sigma * sqrt_T
    except (ValueError, ZeroDivisionError):
        return None

    # ── Greeks ────────────────────────────────────────────────────────────────
    n_d1  = _n(d1)
    disc  = math.exp(-r * T)     # discount factor

    # Gamma (same for call and put)
    gamma = n_d1 / (S * sigma * sqrt_T)

    # Delta
    if opt == "CE":
        delta = _N(d1)
        theta = (
            -(S * n_d1 * sigma) / (2 * sqrt_T)
            - r * K * disc * _N(d2)
        ) / 365.0
    else:
        delta = _N(d1) - 1.0
        theta = (
            -(S * n_d1 * sigma) / (2 * sqrt_T)
            + r * K * disc * _N(-d2)
        ) / 365.0

    # Vega: ₹ change per 1% move in IV
    vega = S * n_d1 * sqrt_T / 100.0

    # ── Clamp & round ─────────────────────────────────────────────────────────
    delta = max(-1.0, min(1.0, delta))

    return {
        "delta": round(delta, 4),
        "gamma": round(gamma, 6),
        "theta": round(theta, 2),   # ₹ per day
        "vega":  round(vega,  2),   # ₹ per 1% IV
    }
