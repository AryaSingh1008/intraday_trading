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
                      sector: str = "Other", mode: str = "intraday") -> dict:
        """
        Full analysis pipeline for one stock.
        mode="intraday"   → standard scoring (all indicators, normal ATR stops)
        mode="positional" → swing scoring (no VWAP/ORB, wider stops, capped sentiment)
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
                hist, current_price, volume, avg_volume, intraday=intraday, mode=mode
            )

            # ── Sentiment score ───────────────────────────────────────────────
            # Positional/swing skips live sentiment: news is intraday noise for
            # multi-week holds, and skipping 80 fetches keeps the response within
            # the 29-second API Gateway timeout. Neutral (0) is used instead.
            if mode == "positional":
                sent_raw, sent_reasons = 0.0, []
            else:
                sent_raw, sent_reasons = await _sentiment_agent.get_sentiment_score(symbol, name)
            # Normalise sentiment from [-50,+50] → [0,100] via tanh S-curve.
            sent_score = self._normalize_sentiment(sent_raw)

            # ── Adaptive weights ──────────────────────────────────────────────
            sent_abs = abs(sent_raw)
            if mode == "positional":
                # Positional/swing: driven by price structure, not today's news.
                tech_w, sent_w = 0.85, 0.15
            elif sent_abs >= 25:
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
                    stock_return = float(hist["Close"].iloc[-1]) / float(hist["Close"].iloc[-30]) - 1
                    # Handle both Series (single column) and DataFrame (multi-level) from yfinance
                    nifty_s = nifty_hist.iloc[:, 0] if hasattr(nifty_hist, "iloc") and nifty_hist.ndim == 2 else nifty_hist
                    nifty_return = float(nifty_s.iloc[-1]) / float(nifty_s.iloc[-30]) - 1
                    # Use (1+stock) / (1+nifty) — correct RS formula in all market directions.
                    # Simple return ratio (stock/nifty) inverts when nifty is negative,
                    # wrongly penalising stocks that fell less than the market.
                    denom = 1 + nifty_return
                    if denom != 0:
                        rs_ratio = round((1 + stock_return) / denom, 2)
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

            # _bb_upper/_bb_lower can be None (insufficient data) — guard both None and NaN
            _bb_valid = (
                _bb_upper is not None and _bb_lower is not None
                and not math.isnan(_bb_upper) and not math.isnan(_bb_lower)
            )
            if _atr and _bb_valid:
                pivot_r1 = _pivots.get("r1") if _pivots else None
                pivot_s1 = _pivots.get("s1") if _pivots else None

                # Positional mode uses wider ATR multipliers — multi-day holds
                # need room for intra-day noise without triggering the stop.
                if mode == "positional":
                    tgt_strong, sl_strong = 3.0, 2.0   # was 2.5 / 1.5
                    tgt_buy,    sl_buy    = 2.0, 1.5    # was 1.5 / 1.0
                else:
                    tgt_strong, sl_strong = 2.5, 1.5
                    tgt_buy,    sl_buy    = 1.5, 1.0

                def _safe_min(*vals):
                    """min() over candidates, ignoring None and NaN. Falls back to last arg."""
                    candidates = [v for v in vals if v is not None and not (isinstance(v, float) and math.isnan(v))]
                    return min(candidates) if candidates else vals[-1]

                def _safe_max(*vals):
                    """max() over candidates, ignoring None and NaN. Falls back to last arg."""
                    candidates = [v for v in vals if v is not None and not (isinstance(v, float) and math.isnan(v))]
                    return max(candidates) if candidates else vals[-1]

                if signal == "STRONG BUY":
                    raw_target = current_price + tgt_strong * _atr
                    raw_stop   = current_price - sl_strong  * _atr
                    _t = _safe_min(_bb_upper, pivot_r1, raw_target)
                    _s = _safe_max(_bb_lower, pivot_s1, raw_stop)
                    target_price = round(_t if _t > current_price else raw_target, 2)
                    stop_loss    = round(_s if _s < current_price else raw_stop, 2)
                elif signal == "BUY":
                    raw_target = current_price + tgt_buy * _atr
                    raw_stop   = current_price - sl_buy   * _atr
                    _t = _safe_min(_bb_upper, pivot_r1, raw_target)
                    _s = _safe_max(_bb_lower, pivot_s1, raw_stop)
                    target_price = round(_t if _t > current_price else raw_target, 2)
                    stop_loss    = round(_s if _s < current_price else raw_stop, 2)
                elif signal == "SELL":
                    raw_target = current_price - tgt_buy * _atr
                    _t = _safe_max(_bb_lower, pivot_s1, raw_target)
                    target_buy_price = round(_t if _t < current_price else raw_target, 2)
                elif signal == "STRONG SELL":
                    raw_target = current_price - tgt_strong * _atr
                    _t = _safe_max(_bb_lower, pivot_s1, raw_target)
                    target_buy_price = round(_t if _t < current_price else raw_target, 2)

            # ── Position sizing (2% risk rule) ────────────────────────────────
            # For positional mode, max_per_position = portfolio / max_positions
            # (passed via stock_data so the handler can customise per-request).
            suggested_qty = None
            risk_amount   = None
            invest_amount = None
            if stop_loss and stop_loss < current_price and current_price > 0:
                try:
                    portfolio     = stock_data.get("_portfolio", 100_000)
                    max_positions = stock_data.get("_max_positions", 10)
                    risk_pct      = 0.02
                    max_risk      = portfolio * risk_pct
                    max_per_pos   = portfolio / max_positions
                    risk_per_share = current_price - stop_loss
                    if risk_per_share > 0:
                        qty_by_risk  = int(max_risk / risk_per_share)
                        qty_by_cap   = int(max_per_pos / current_price)
                        # Don't force 1 share — if 2% risk rule gives 0, it means
                        # the stock is too volatile relative to portfolio size.
                        suggested_qty = min(qty_by_risk, qty_by_cap) if qty_by_risk > 0 else None
                        if suggested_qty:
                            risk_amount   = round(suggested_qty * risk_per_share, 2)
                            invest_amount = round(suggested_qty * current_price, 2)
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
                "invest_amount":    invest_amount,
                "vwap":             tech_extras.get("vwap"),
                "support_level":    tech_extras.get("support_level"),
                "resistance_level": tech_extras.get("resistance_level"),
                "orb_high":         tech_extras.get("orb_high"),
                "orb_low":          tech_extras.get("orb_low"),
                "day_high":         stock_data.get("day_high"),
                "day_low":          stock_data.get("day_low"),
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
            "invest_amount":    None,
            "vwap":             None,
            "support_level":    None,
            "resistance_level": None,
        }
