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

  Relative Strength modifier (vs NIFTY 50):
    RS > 1.2 → +5 pts  (outperforming market)
    RS < 0.8 → -5 pts  (underperforming market)

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

    async def analyze(self, symbol: str, name: str, stock_data: dict,
                      sector: str = "Other") -> dict:
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
            intraday      = stock_data.get("intraday", [])

            # ── Technical score (now includes VWAP, support/resistance) ───────
            tech_score, tech_reasons, tech_extras = _tech_agent.analyze(
                hist, current_price, volume, avg_volume, intraday=intraday
            )

            # ── Sentiment score ───────────────────────────────────────────────
            sent_raw, sent_reasons = await _sentiment_agent.get_sentiment_score(symbol, name)
            # Normalise sentiment from [-50,+50] → [0,100] via tanh S-curve.
            sent_score = self._normalize_sentiment(sent_raw)

            # ── Adaptive weights ──────────────────────────────────────────────
            sent_abs = abs(sent_raw)
            if sent_abs >= 25:
                tech_w, sent_w = 0.55, 0.45
            elif sent_abs >= 12:
                tech_w, sent_w = 0.65, 0.35
            else:
                tech_w, sent_w = 0.75, 0.25

            # ── Combined score (weighted) ─────────────────────────────────────
            final_score = round(tech_score * tech_w + sent_score * sent_w, 1)

            # ── Relative Strength vs NIFTY 50 ─────────────────────────────────
            rs_ratio = None
            nifty_hist = stock_data.get("nifty_hist")
            if nifty_hist is not None and len(nifty_hist) >= 30:
                try:
                    stock_return = float(hist["Close"].iloc[-1])      / float(hist["Close"].iloc[-30])      - 1
                    nifty_return = float(nifty_hist.iloc[-1].iloc[0] if hasattr(nifty_hist.iloc[-1], 'iloc') else nifty_hist.iloc[-1]) / float(nifty_hist.iloc[-30].iloc[0] if hasattr(nifty_hist.iloc[-30], 'iloc') else nifty_hist.iloc[-30]) - 1
                    if nifty_return != 0:
                        rs_ratio = round(stock_return / nifty_return, 2)
                        if rs_ratio > 1.2:
                            final_score = min(100, final_score + 5)
                        elif rs_ratio < 0.8:
                            final_score = max(0,   final_score - 5)
                except Exception:
                    pass

            final_score = round(final_score, 1)

            # ── Signal label ──────────────────────────────────────────────────
            signal, signal_color, signal_emoji, signal_bg = self._classify(final_score)

            # ── Risk level ────────────────────────────────────────────────────
            risk_label, risk_color = self._risk(hist, change_pct)

            # ── Plain-English explanation ─────────────────────────────────────
            explanation = self._explain(signal, tech_reasons + sent_reasons, name)

            # ── Target / stop-loss prices (enhanced with pivot points) ─────────
            _close    = hist["Close"]
            _high     = hist["High"]
            _low      = hist["Low"]
            _bb_upper, _bb_mid, _bb_lower = TechnicalAgent._bollinger(_close)
            _atr      = tech_extras.get("atr") or TechnicalAgent._atr(_high, _low, _close)
            _pivots   = TechnicalAgent._pivot_points(_high, _low, _close)

            target_price     = None
            stop_loss        = None
            target_buy_price = None

            if _atr and _bb_upper and _bb_lower:
                pivot_r1 = _pivots.get("r1") if _pivots else None
                pivot_s1 = _pivots.get("s1") if _pivots else None

                if signal == "STRONG BUY":
                    raw_target = current_price + 2.5 * _atr
                    target_price = round(min(filter(None, [_bb_upper, pivot_r1, raw_target])), 2)
                    raw_stop     = current_price - 1.5 * _atr
                    stop_loss    = round(max(filter(None, [_bb_lower, pivot_s1, raw_stop])), 2)
                elif signal == "BUY":
                    raw_target = current_price + 1.5 * _atr
                    target_price = round(min(filter(None, [_bb_upper, pivot_r1, raw_target])), 2)
                    raw_stop     = current_price - 1.0 * _atr
                    stop_loss    = round(max(filter(None, [_bb_lower, pivot_s1, raw_stop])), 2)
                elif signal == "SELL":
                    raw_target = current_price - 1.5 * _atr
                    target_buy_price = round(max(filter(None, [_bb_lower, pivot_s1, raw_target])), 2)
                elif signal == "STRONG SELL":
                    raw_target = current_price - 2.5 * _atr
                    target_buy_price = round(max(filter(None, [_bb_lower, pivot_s1, raw_target])), 2)

            # ── Position sizing (2% risk rule, Rs 1 lakh default portfolio) ────
            suggested_qty = None
            risk_amount   = None
            if stop_loss and stop_loss < current_price and current_price > 0:
                try:
                    portfolio     = 100_000
                    risk_pct      = 0.02
                    max_risk      = portfolio * risk_pct
                    risk_per_share = current_price - stop_loss
                    if risk_per_share > 0:
                        qty_by_risk  = int(max_risk / risk_per_share)
                        qty_by_cap   = int((portfolio * 0.10) / current_price)
                        suggested_qty = max(1, min(qty_by_risk, qty_by_cap))
                        risk_amount   = round(suggested_qty * risk_per_share, 2)
                except Exception:
                    pass

            # ── Daily chart data (last 250 days for multi-TF modal chart) ─────
            daily_chart = []
            try:
                close_series = hist["Close"]
                for dt, price in zip(close_series.index[-250:], close_series.values[-250:]):
                    daily_chart.append({"date": str(dt)[:10], "price": round(float(price), 2)})
            except Exception:
                pass

            return {
                "symbol":           symbol,
                "name":             name,
                "sector":           sector,
                "current_price":    current_price,
                "prev_close":       prev_close,
                "change_pct":       change_pct,
                "change_dir":       "up" if change_pct >= 0 else "down",
                "volume":           volume,
                "avg_volume":       avg_volume,
                "high_52w":         stock_data.get("high_52w"),
                "low_52w":          stock_data.get("low_52w"),
                "signal":           signal,
                "signal_color":     signal_color,
                "signal_emoji":     signal_emoji,
                "signal_bg":        signal_bg,
                "score":            final_score,
                "tech_score":       tech_score,
                "sent_score":       round(sent_raw, 1),
                "tech_weight":      tech_w,
                "sent_weight":      sent_w,
                "rs_ratio":         rs_ratio,
                "risk":             risk_label,
                "risk_color":       risk_color,
                "explanation":      explanation,
                "reasons":          (tech_reasons + sent_reasons)[:6],
                "intraday":         intraday,
                "daily_chart":      daily_chart,
                "target_price":     target_price,
                "stop_loss":        stop_loss,
                "target_buy_price": target_buy_price,
                "suggested_qty":    suggested_qty,
                "risk_amount":      risk_amount,
                "vwap":             tech_extras.get("vwap"),
                "support_level":    tech_extras.get("support_level"),
                "resistance_level": tech_extras.get("resistance_level"),
            }

        except Exception as e:
            logger.error(f"SignalAgent.analyze({symbol}): {e}")
            return self._error_result(symbol, name, stock_data, sector)

    # ── Helpers ──────────────────────────────────────────────────────────────

    @staticmethod
    def _normalize_sentiment(raw: float) -> float:
        """
        Maps raw sentiment score [-50, +50] → [0, 100] via tanh S-curve.
        tanh amplifies mid-range signals while capping extremes.
        """
        compressed = math.tanh(raw / 30.0)
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
            volatility = float(returns.std() * 100)

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
    def _error_result(symbol: str, name: str, stock_data: dict,
                      sector: str = "Other") -> dict:
        return {
            "symbol":           symbol,
            "name":             name,
            "sector":           sector,
            "current_price":    stock_data.get("current_price", 0),
            "prev_close":       stock_data.get("prev_close", 0),
            "change_pct":       stock_data.get("change_pct", 0),
            "change_dir":       "up",
            "volume":           0,
            "avg_volume":       1,
            "high_52w":         None,
            "low_52w":          None,
            "signal":           "HOLD",
            "signal_color":     "#856404",
            "signal_emoji":     "🟡",
            "signal_bg":        "#fff3cd",
            "score":            50.0,
            "tech_score":       50.0,
            "sent_score":       0.0,
            "rs_ratio":         None,
            "risk":             "MEDIUM",
            "risk_color":       "#fd7e14",
            "explanation":      f"Could not fully analyse {name}. Please refresh.",
            "reasons":          [],
            "intraday":         [],
            "daily_chart":      [],
            "target_price":     None,
            "stop_loss":        None,
            "target_buy_price": None,
            "suggested_qty":    None,
            "risk_amount":      None,
            "vwap":             None,
            "support_level":    None,
            "resistance_level": None,
        }
