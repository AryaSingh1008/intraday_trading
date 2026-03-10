"""
====================================================
  Signal Agent  –  Master orchestrator
  ─────────────────────────────────────────────────
  Combines:
    • Technical Analysis Score  (adaptive weight)
    • News Sentiment Score      (adaptive weight)

  Adaptive weighting by sentiment signal strength:
    |sent_raw| ≥ 25 → tech 55 % / sentiment 45 %
    |sent_raw| ≥ 12 → tech 65 % / sentiment 35 %
    |sent_raw| <  12 → tech 75 % / sentiment 25 %

  Sentiment normalization: tanh S-curve instead of
  linear mapping — amplifies moderate signals while
  capping extreme ones (avoids VADER over-scoring).

  Final Score 0 – 100
  ─────────────────────────────────────────────────
    > 70  →  STRONG BUY  🟢🟢
    55-70 →  BUY         🟢
    40-55 →  HOLD        🟡
    25-40 →  SELL        🔴
    < 25  →  STRONG SELL 🔴🔴
====================================================
"""

import math
import logging
from typing import Optional

from backend.agents.technical_agent import TechnicalAgent
from backend.agents.sentiment_agent  import SentimentAgent

logger = logging.getLogger(__name__)

_tech_agent      = TechnicalAgent()
_sentiment_agent = SentimentAgent()


class SignalAgent:

    async def analyze(self, symbol: str, name: str, stock_data: dict) -> dict:
        """
        Full analysis pipeline for one stock.
        Returns a rich dict that the frontend renders.
        """
        try:
            hist          = stock_data["hist"]
            current_price = stock_data["current_price"]
            prev_close    = stock_data["prev_close"]
            change_pct    = stock_data["change_pct"]
            volume        = stock_data["volume"]
            avg_volume    = stock_data["avg_volume"]

            # ── Technical score ───────────────────────────
            tech_score, tech_reasons = _tech_agent.analyze(
                hist, current_price, volume, avg_volume
            )

            # ── Sentiment score ───────────────────────────
            sent_raw, sent_reasons = await _sentiment_agent.get_sentiment_score(symbol, name)
            # Normalise sentiment from [-50,+50] → [0,100] via tanh S-curve.
            # Compared to a plain linear shift (50 + sent_raw), tanh amplifies
            # moderate signals (±12–30) while softening extremes, reflecting
            # that VADER compound scores cluster near zero.
            sent_score = self._normalize_sentiment(sent_raw)

            # ── Adaptive weights ──────────────────────────
            # Strong news shifts weight toward sentiment;
            # quiet/neutral news lets technicals dominate.
            sent_abs = abs(sent_raw)
            if sent_abs >= 25:        # strong news signal
                tech_w, sent_w = 0.55, 0.45
            elif sent_abs >= 12:      # moderate news signal
                tech_w, sent_w = 0.65, 0.35
            else:                     # weak / neutral news
                tech_w, sent_w = 0.75, 0.25

            # ── Combined score (weighted) ─────────────────
            final_score = round(tech_score * tech_w + sent_score * sent_w, 1)

            # ── Signal label ──────────────────────────────
            signal, signal_color, signal_emoji, signal_bg = self._classify(final_score)

            # ── Risk level ────────────────────────────────
            risk_label, risk_color = self._risk(hist, change_pct)

            # ── Plain-English explanation ─────────────────
            explanation = self._explain(signal, tech_reasons + sent_reasons, name)

            # ── Intraday chart data ───────────────────────
            intraday = stock_data.get("intraday", [])

            return {
                "symbol":        symbol,
                "name":          name,
                "current_price": current_price,
                "prev_close":    prev_close,
                "change_pct":    change_pct,
                "change_dir":    "up" if change_pct >= 0 else "down",
                "volume":        volume,
                "avg_volume":    avg_volume,
                "high_52w":      stock_data.get("high_52w"),
                "low_52w":       stock_data.get("low_52w"),
                "signal":        signal,
                "signal_color":  signal_color,
                "signal_emoji":  signal_emoji,
                "signal_bg":     signal_bg,
                "score":         final_score,
                "tech_score":    tech_score,
                "sent_score":    round(sent_raw, 1),
                "tech_weight":   tech_w,
                "sent_weight":   sent_w,
                "risk":          risk_label,
                "risk_color":    risk_color,
                "explanation":   explanation,
                "reasons":       (tech_reasons + sent_reasons)[:6],
                "intraday":      intraday,
            }

        except Exception as e:
            logger.error(f"SignalAgent.analyze({symbol}): {e}")
            return self._error_result(symbol, name, stock_data)

    # ── Helpers ──────────────────────────────────────────

    @staticmethod
    def _normalize_sentiment(raw: float) -> float:
        """
        Maps raw sentiment score [-50, +50] → [0, 100] via tanh S-curve.

        Why tanh instead of plain linear (50 + raw)?
        • VADER compound scores cluster near 0; plain linear under-rewards
          moderate positive/negative news (e.g. raw=20 → linear 70 vs tanh 79).
        • tanh amplifies mid-range signals while capping extremes — a raw score
          of ±50 (perfect VADER) maps to ~96/4 rather than 100/0.
        """
        compressed = math.tanh(raw / 30.0)   # S-curve: domain [-50,+50] → ~[-0.93, +0.93]
        return round(50.0 + compressed * 50.0, 1)

    @staticmethod
    def _classify(score: float):
        if score > 70:
            return "STRONG BUY",  "#155724", "🟢🟢", "#d4edda"
        if score > 55:
            return "BUY",         "#155724", "🟢",   "#d4edda"
        if score > 40:
            return "HOLD",        "#856404", "🟡",   "#fff3cd"
        if score > 25:
            return "SELL",        "#721c24", "🔴",   "#f8d7da"
        return     "STRONG SELL", "#721c24", "🔴🔴", "#f8d7da"

    @staticmethod
    def _risk(hist, change_pct: float):
        """Simple volatility-based risk level."""
        try:
            returns    = hist["Close"].pct_change().dropna()
            volatility = float(returns.std() * 100)   # daily std in %

            if volatility < 1.5 and abs(change_pct) < 2:
                return "LOW",    "#28a745"
            if volatility < 3.0 or abs(change_pct) < 4:
                return "MEDIUM", "#fd7e14"
            return         "HIGH",   "#dc3545"
        except Exception:
            return "MEDIUM", "#fd7e14"

    @staticmethod
    def _explain(signal: str, reasons: list, name: str) -> str:
        top = reasons[:3] if reasons else []
        bullet_str = "; ".join(top) if top else "no specific signal"

        templates = {
            "STRONG BUY": (
                f"{name} looks like a strong buying opportunity right now. "
                f"Multiple indicators are positive: {bullet_str}. "
                "Consider buying, but always use a stop-loss."
            ),
            "BUY": (
                f"{name} shows a buying signal. {bullet_str}. "
                "Conditions are favourable but keep your risk in mind."
            ),
            "HOLD": (
                f"{name} is in a wait-and-watch zone. {bullet_str}. "
                "No clear direction yet — it is best to hold your current position."
            ),
            "SELL": (
                f"{name} is showing selling signals. {bullet_str}. "
                "Consider reducing your position or placing a stop-loss order."
            ),
            "STRONG SELL": (
                f"{name} has strong selling signals. {bullet_str}. "
                "Most indicators point downward. Consider exiting to protect your money."
            ),
        }
        return templates.get(signal, f"{name}: {bullet_str}")

    @staticmethod
    def _error_result(symbol: str, name: str, stock_data: dict) -> dict:
        return {
            "symbol":        symbol,
            "name":          name,
            "current_price": stock_data.get("current_price", 0),
            "prev_close":    stock_data.get("prev_close", 0),
            "change_pct":    stock_data.get("change_pct", 0),
            "change_dir":    "up",
            "volume":        0,
            "avg_volume":    1,
            "high_52w":      None,
            "low_52w":       None,
            "signal":        "HOLD",
            "signal_color":  "#856404",
            "signal_emoji":  "🟡",
            "signal_bg":     "#fff3cd",
            "score":         50.0,
            "tech_score":    50.0,
            "sent_score":    0.0,
            "risk":          "MEDIUM",
            "risk_color":    "#fd7e14",
            "explanation":   f"Could not fully analyse {name}. Please refresh.",
            "reasons":       [],
            "intraday":      [],
        }
