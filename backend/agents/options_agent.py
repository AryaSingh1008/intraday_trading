"""
Options Agent – analyses an option chain and produces a plain-English
recommendation for a non-technical user (dad).

Signal logic:
  PCR > 1.2        → market leans BULLISH  (more PUT writers = bull sentiment)
  PCR < 0.8        → market leans BEARISH  (more CALL writers = bear sentiment)
  0.8 ≤ PCR ≤ 1.2 → NEUTRAL

  IV percentile    → HIGH IV = expensive options, advice to SELL; LOW = buy
  Max-pain strike  → strike with highest combined OI (market magnets toward it)
"""

import logging
from typing import Optional, List, Dict, Tuple

logger = logging.getLogger(__name__)


def _pcr_signal(pcr: Optional[float]) -> Tuple[str, str]:
    """Returns (signal_label, plain_english_reason)."""
    if pcr is None:
        return "NEUTRAL", "Not enough data to calculate Put-Call Ratio."
    if pcr > 1.2:
        return "BULLISH", f"Put-Call Ratio is {pcr:.2f} (above 1.2) — more traders are buying PUT protection, which usually means the market could RISE. This is a Bullish sign."
    if pcr < 0.8:
        return "BEARISH", f"Put-Call Ratio is {pcr:.2f} (below 0.8) — more traders are buying CALLs, which can mean the market is overbought and might FALL. This is a Bearish sign."
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
            s = r["strike"]
            c_oi = r.get("call_oi", 0) or 0
            p_oi = r.get("put_oi",  0) or 0
            # call buyers lose when spot (strike) < their strike
            if strike < s:
                pain += c_oi * (s - strike)
            # put buyers lose when spot (strike) > their strike
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


class OptionsAgent:

    def analyze(self, data: Dict) -> Dict:
        """
        Input : raw dict from OptionsFetcher
        Output: enriched dict with signal, explanation, score, chain rows
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
        pcr_signal, pcr_reason = _pcr_signal(pcr)

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

        if avg_iv is not None:
            if avg_iv > 25:
                iv_advice = f"Implied Volatility (IV) is HIGH at {avg_iv}% — options are expensive. Better to SELL options or wait."
            elif avg_iv < 15:
                iv_advice = f"Implied Volatility (IV) is LOW at {avg_iv}% — options are cheap. Good time to BUY options."
            else:
                iv_advice = f"Implied Volatility (IV) is moderate at {avg_iv}% — normal market conditions."

        # ── Max pain ─────────────────────────────────────────────────────────
        max_pain_strike = None
        max_pain_note   = ""
        # Only compute max pain when we have real OI data (not synthetic zeros)
        if source != "synthetic" and total_call_oi > 0 and total_put_oi > 0:
            max_pain_strike = _max_pain(chain)
            if max_pain_strike and spot:
                if max_pain_strike > spot:
                    max_pain_note = f"Max Pain is at ₹{max_pain_strike:,.0f} (above current price). Market may RISE toward this level."
                elif max_pain_strike < spot:
                    max_pain_note = f"Max Pain is at ₹{max_pain_strike:,.0f} (below current price). Market may FALL toward this level."
                else:
                    max_pain_note = f"Max Pain is at ₹{max_pain_strike:,.0f} — right at current price."

        # ── Final recommendation ──────────────────────────────────────────────
        score  = 50  # start neutral
        if pcr is not None:
            if pcr > 1.5:   score += 25
            elif pcr > 1.2: score += 15
            elif pcr < 0.6: score -= 25
            elif pcr < 0.8: score -= 15

        if avg_iv is not None:
            if avg_iv > 30: score -= 5    # very expensive; slight caution
            elif avg_iv < 12: score += 5  # cheap; slight encouragement

        score = max(0, min(100, score))

        if score >= 65:
            signal, sig_color, sig_emoji, sig_bg = "BULLISH", "#16a34a", "🟢", "#dcfce7"
        elif score >= 45:
            signal, sig_color, sig_emoji, sig_bg = "NEUTRAL", "#d97706", "🟡", "#fef9c3"
        else:
            signal, sig_color, sig_emoji, sig_bg = "BEARISH", "#dc2626", "🔴", "#fee2e2"

        # Build action suggestion
        if signal == "BULLISH":
            action = "Consider buying CALL options near the ATM strike."
        elif signal == "BEARISH":
            action = "Consider buying PUT options near the ATM strike."
        else:
            action = "Wait for a clearer signal before entering a trade."

        explanation = f"{pcr_reason} {iv_advice} {max_pain_note} {action}".strip()

        # ── Reasons list ─────────────────────────────────────────────────────
        reasons: List[str] = [pcr_reason]
        if iv_advice:       reasons.append(iv_advice)
        if max_pain_note:   reasons.append(max_pain_note)

        # Mark data source for user awareness
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
            "max_pain":        max_pain_strike,
            "total_call_oi":   total_call_oi,
            "total_put_oi":    total_put_oi,
            "explanation":     explanation,
            "reasons":         reasons,
            "chain":           chain,
            "source":          source,
        }
