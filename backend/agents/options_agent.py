"""
Options Agent – analyses an option chain and produces a plain-English
recommendation.

Signal logic:
  PCR > 1.3        → market leans BULLISH  (index-tuned threshold)
  PCR < 0.7        → market leans BEARISH
  else             → NEUTRAL

  IV Percentile    → HIGH (>80%) = expensive, advice to SELL;
                     LOW  (<20%) = cheap,     advice to BUY
  Max-pain strike  → strike where combined OI loss is maximum
"""

import logging
from typing import Optional, List, Dict, Tuple

from backend.utils import iv_history_store

logger = logging.getLogger(__name__)


def _pcr_signal(pcr: Optional[float], symbol: str = "") -> Tuple[str, str]:
    """Returns (signal_label, plain_english_reason).
    Uses slightly higher thresholds for indices (NIFTY/BANKNIFTY run hotter).
    """
    if pcr is None:
        return "NEUTRAL", "Not enough data to calculate Put-Call Ratio."

    # Indices historically run with a higher PCR baseline
    is_index = symbol in ("NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY")
    bull_thr  = 1.3 if is_index else 1.2
    bear_thr  = 0.7 if is_index else 0.8

    if pcr > bull_thr:
        return "BULLISH", (
            f"Put-Call Ratio is {pcr:.2f} (above {bull_thr}) — more traders are "
            f"buying PUT protection, which usually means the market could RISE. Bullish sign."
        )
    if pcr < bear_thr:
        return "BEARISH", (
            f"Put-Call Ratio is {pcr:.2f} (below {bear_thr}) — more traders are "
            f"buying CALLs, which can mean the market is overbought and might FALL. Bearish sign."
        )
    return "NEUTRAL", f"Put-Call Ratio is {pcr:.2f} — balanced. Market is undecided. Hold and watch."


def _max_pain(chain: List[Dict]) -> Optional[float]:
    """Strike where total option loss (to buyers) is maximum."""
    if not chain:
        return None
    best_strike = None
    best_pain   = float("inf")
    for row in chain:
        strike = row["strike"]
        pain = 0
        for r in chain:
            s    = r["strike"]
            c_oi = r.get("call_oi", 0) or 0
            p_oi = r.get("put_oi",  0) or 0
            if strike < s:
                pain += c_oi * (s - strike)
            if strike > s:
                pain += p_oi * (strike - s)
        if pain < best_pain:
            best_pain   = pain
            best_strike = strike
    return best_strike


def _avg_iv(chain: List[Dict], side: str) -> Optional[float]:
    ivs = [r[f"{side}_iv"] for r in chain if r.get(f"{side}_iv") is not None]
    if not ivs:
        return None
    return round(sum(ivs) / len(ivs), 1)


def _iv_advice_from_percentile(iv_pct: float, avg_iv: Optional[float]) -> str:
    """Return iv_advice string using percentile context when available."""
    iv_str = f" (avg IV {avg_iv}%)" if avg_iv else ""
    if iv_pct > 80:
        return (
            f"IV Percentile is {iv_pct:.0f}%{iv_str} — options are VERY EXPENSIVE "
            f"historically. Strong signal to sell premium (sell straddles/strangles) or wait."
        )
    if iv_pct > 60:
        return (
            f"IV Percentile is {iv_pct:.0f}%{iv_str} — options are elevated. "
            f"Favour option-selling strategies."
        )
    if iv_pct < 20:
        return (
            f"IV Percentile is {iv_pct:.0f}%{iv_str} — options are VERY CHEAP "
            f"historically. Good time to BUY options (debit strategies)."
        )
    if iv_pct < 40:
        return (
            f"IV Percentile is {iv_pct:.0f}%{iv_str} — options are below-average cost. "
            f"Slight edge to buyers."
        )
    return (
        f"IV Percentile is {iv_pct:.0f}%{iv_str} — options are normally priced. "
        f"No volatility edge either way."
    )


def _iv_advice_absolute(avg_iv: float) -> str:
    """Fallback advice when percentile history isn't available yet."""
    if avg_iv > 25:
        return f"IV is HIGH at {avg_iv}% — options are expensive. Better to SELL options or wait."
    if avg_iv < 15:
        return f"IV is LOW at {avg_iv}% — options are cheap. Good time to BUY options."
    return f"IV is moderate at {avg_iv}% — normal market conditions."


class OptionsAgent:

    def analyze(self, data: Dict) -> Dict:
        """
        Input : raw dict from OptionsFetcher (includes Greeks + OI change per row)
        Output: enriched dict with signal, explanation, score, iv_percentile, chain rows
        """
        symbol        = data.get("symbol", "?")
        spot          = data.get("spot")
        pcr           = data.get("pcr")
        atm_strike    = data.get("atm_strike")
        chain         = data.get("chain", [])
        total_call_oi = data.get("total_call_oi", 0)
        total_put_oi  = data.get("total_put_oi", 0)
        expiry        = data.get("expiry", "N/A")
        source        = data.get("source", "?")

        # ── PCR signal ───────────────────────────────────────────────────────
        pcr_signal, pcr_reason = _pcr_signal(pcr, symbol)

        # ── IV analysis ──────────────────────────────────────────────────────
        avg_call_iv = _avg_iv(chain, "call")
        avg_put_iv  = _avg_iv(chain, "put")
        avg_iv      = None
        iv_advice   = ""

        if avg_call_iv and avg_put_iv:
            avg_iv = round((avg_call_iv + avg_put_iv) / 2, 1)
        elif avg_call_iv:
            avg_iv = avg_call_iv
        elif avg_put_iv:
            avg_iv = avg_put_iv

        # ── IV Percentile ─────────────────────────────────────────────────────
        iv_percentile: Optional[float] = None
        if avg_iv is not None and source != "synthetic":
            iv_percentile = iv_history_store.get_iv_percentile(symbol, avg_iv)
            # Record today's reading for future percentile calculations
            iv_history_store.append_iv(symbol, avg_iv)

        # Build IV advice (use percentile if we have enough history, else absolute)
        if iv_percentile is not None:
            iv_advice = _iv_advice_from_percentile(iv_percentile, avg_iv)
        elif avg_iv is not None:
            iv_advice = _iv_advice_absolute(avg_iv)

        # ── Max pain ─────────────────────────────────────────────────────────
        max_pain_strike = None
        max_pain_note   = ""
        # Only compute when we have real OI data (not synthetic zeros)
        if source != "synthetic" and total_call_oi > 0 and total_put_oi > 0:
            max_pain_strike = _max_pain(chain)
            if max_pain_strike and spot:
                if max_pain_strike > spot:
                    max_pain_note = (
                        f"Max Pain is at ₹{max_pain_strike:,.0f} "
                        f"(above current price ₹{spot:,.0f}). Market may RISE toward this level."
                    )
                elif max_pain_strike < spot:
                    max_pain_note = (
                        f"Max Pain is at ₹{max_pain_strike:,.0f} "
                        f"(below current price ₹{spot:,.0f}). Market may FALL toward this level."
                    )
                else:
                    max_pain_note = f"Max Pain is at ₹{max_pain_strike:,.0f} — right at current price."

        # ── OI build / unwind note ────────────────────────────────────────────
        oi_change_note = ""
        if source != "synthetic":
            total_call_chg = sum(r.get("call_oi_change", 0) or 0 for r in chain)
            total_put_chg  = sum(r.get("put_oi_change",  0) or 0 for r in chain)
            if total_call_chg != 0 or total_put_chg != 0:
                c_dir = "building ↑" if total_call_chg > 0 else "unwinding ↓"
                p_dir = "building ↑" if total_put_chg  > 0 else "unwinding ↓"
                oi_change_note = (
                    f"Since last refresh — Call OI {c_dir} ({total_call_chg:+,}), "
                    f"Put OI {p_dir} ({total_put_chg:+,})."
                )

        # ── Scoring ───────────────────────────────────────────────────────────
        score = 50  # neutral baseline

        if pcr is not None:
            if pcr > 1.5:   score += 25
            elif pcr > 1.3: score += 15
            elif pcr < 0.5: score -= 25
            elif pcr < 0.7: score -= 15

        # Use IV percentile for scoring if available, else use absolute IV
        if iv_percentile is not None:
            if iv_percentile < 20:   score += 5   # cheap options → slight bullish edge
            elif iv_percentile > 80: score -= 5   # expensive → caution
        elif avg_iv is not None:
            if avg_iv > 30: score -= 5
            elif avg_iv < 12: score += 5

        score = max(0, min(100, score))

        if score >= 65:
            signal, sig_color, sig_emoji, sig_bg = "BULLISH", "#16a34a", "🟢", "#dcfce7"
        elif score >= 45:
            signal, sig_color, sig_emoji, sig_bg = "NEUTRAL", "#d97706", "🟡", "#fef9c3"
        else:
            signal, sig_color, sig_emoji, sig_bg = "BEARISH", "#dc2626", "🔴", "#fee2e2"

        if signal == "BULLISH":
            action = "Consider buying CALL options near the ATM strike."
        elif signal == "BEARISH":
            action = "Consider buying PUT options near the ATM strike."
        else:
            action = "Wait for a clearer signal before entering a trade."

        explanation = " ".join(
            p for p in [pcr_reason, iv_advice, max_pain_note, oi_change_note, action] if p
        ).strip()

        # ── Reasons list ─────────────────────────────────────────────────────
        reasons: List[str] = [pcr_reason]
        if iv_advice:        reasons.append(iv_advice)
        if max_pain_note:    reasons.append(max_pain_note)
        if oi_change_note:   reasons.append(oi_change_note)

        # IV Percentile disclaimer when history is still being built
        if avg_iv is not None and source != "synthetic" and iv_percentile is None:
            reasons.append(
                "ℹ️ IV Percentile will appear after 5+ days of data are recorded. "
                "Currently using absolute IV thresholds."
            )

        if source == "synthetic":
            reasons.append(
                "⚠️ Live NSE option chain data is currently unavailable. "
                "NSE's website blocks automated access — this is a known limitation. "
                "For real options data, visit nseindia.com/option-chain directly, "
                "or connect a broker API (Zerodha Kite / Upstox / Angel One)."
            )

        return {
            "symbol":          symbol,
            "spot":            spot,
            "expiry":          expiry,
            "atm_strike":      atm_strike,
            "signal":          signal,
            "signal_color":    sig_color,
            "signal_emoji":    sig_emoji,
            "signal_bg":       sig_bg,
            "score":           score,
            "pcr":             pcr,
            "avg_iv":          avg_iv,
            "iv_percentile":   iv_percentile,
            "max_pain":        max_pain_strike,
            "total_call_oi":   total_call_oi,
            "total_put_oi":    total_put_oi,
            "explanation":     explanation,
            "reasons":         reasons,
            "chain":           chain,
            "source":          source,
        }
