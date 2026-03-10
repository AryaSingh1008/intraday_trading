"""
====================================================
  Technical Analysis Agent
  ─────────────────────────────────────────────────
  Calculates classic technical indicators and
  returns a score between 0 (very bearish) and
  100 (very bullish), plus a list of plain-English
  reason strings.

  Indicators used (all FREE, from 'ta' library):
    • RSI   – momentum oscillator
    • MACD  – trend/momentum
    • Bollinger Bands – volatility
    • SMA 20 & 50    – trend direction
    • Volume ratio   – confirms moves
====================================================
"""

import logging
from typing import Tuple, List, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class TechnicalAgent:

    def analyze(self, hist: pd.DataFrame, current_price: float,
                volume: int, avg_volume: int) -> Tuple[float, List[str]]:
        """
        Returns (score 0-100, list_of_reasons).
        score > 65  →  BUY territory
        score 35-65 →  HOLD territory
        score < 35  →  SELL territory
        """
        score   = 50.0   # neutral starting point
        reasons = []

        try:
            close  = hist["Close"].astype(float)
            high   = hist["High"].astype(float)
            low    = hist["Low"].astype(float)
            vol    = hist["Volume"].astype(float)

            # ── 1.  RSI (14) ─────────────────────────────────
            rsi = self._rsi(close, 14)
            if rsi is not None:
                if rsi < 30:
                    score += 20
                    reasons.append(f"RSI is {rsi:.0f} — stock is oversold (good buying opportunity)")
                elif rsi < 40:
                    score += 10
                    reasons.append(f"RSI is {rsi:.0f} — slightly oversold (mild buy signal)")
                elif rsi > 70:
                    score -= 20
                    reasons.append(f"RSI is {rsi:.0f} — stock is overbought (consider selling)")
                elif rsi > 60:
                    score -= 10
                    reasons.append(f"RSI is {rsi:.0f} — slightly overbought (mild sell signal)")
                else:
                    reasons.append(f"RSI is {rsi:.0f} — neutral zone")

            # ── 1b. RSI Divergence ────────────────────────────
            div_type, div_reason = self._detect_divergence(close)
            if div_type == "bullish":
                score += 12
                reasons.append(div_reason)
            elif div_type == "bearish":
                score -= 12
                reasons.append(div_reason)

            # ── 2.  MACD (12, 26, 9) ─────────────────────────
            macd_line, signal_line = self._macd(close)
            if macd_line is not None and signal_line is not None:
                if macd_line > signal_line:
                    score += 15
                    reasons.append("MACD crossed above signal line — upward momentum building")
                else:
                    score -= 15
                    reasons.append("MACD is below signal line — downward momentum")

            # ── 3.  Bollinger Bands (20, 2σ) ─────────────────
            upper, middle, lower = self._bollinger(close, 20)
            if upper is not None:
                band_width = upper - lower
                if band_width > 0:
                    pos = (current_price - lower) / band_width   # 0 = at lower, 1 = at upper
                    if current_price <= lower:
                        score += 15
                        reasons.append("Price is at/below lower Bollinger Band — potential bounce up")
                    elif current_price >= upper:
                        score -= 15
                        reasons.append("Price is at/above upper Bollinger Band — potential pullback")
                    elif pos < 0.3:
                        score += 8
                        reasons.append("Price is near lower Bollinger Band — mild buy signal")
                    elif pos > 0.7:
                        score -= 8
                        reasons.append("Price is near upper Bollinger Band — mild sell signal")

            # ── 4.  Moving Averages (SMA 20 & SMA 50) ────────
            if len(close) >= 50:
                sma20 = float(close.rolling(20).mean().iloc[-1])
                sma50 = float(close.rolling(50).mean().iloc[-1])

                if sma20 > sma50:
                    score += 10
                    reasons.append("20-day average is above 50-day average — uptrend confirmed")
                else:
                    score -= 10
                    reasons.append("20-day average is below 50-day average — downtrend in place")

                if current_price > sma20:
                    score += 5
                    reasons.append("Current price is above 20-day average — positive momentum")
                else:
                    score -= 5
                    reasons.append("Current price is below 20-day average — negative momentum")

            # ── 4b. EMA 9 & EMA 21 Crossover ─────────────────
            if len(close) >= 21:
                ema9  = close.ewm(span=9,  adjust=False).mean()
                ema21 = close.ewm(span=21, adjust=False).mean()
                curr_diff = float(ema9.iloc[-1] - ema21.iloc[-1])
                prev_diff = float(ema9.iloc[-4] - ema21.iloc[-4]) if len(close) > 4 else curr_diff

                if curr_diff > 0:
                    if prev_diff <= 0:
                        score += 15
                        reasons.append("EMA 9 just crossed above EMA 21 — fresh bullish crossover signal")
                    else:
                        score += 8
                        reasons.append("EMA 9 is above EMA 21 — short-term uptrend confirmed")
                else:
                    if prev_diff >= 0:
                        score -= 15
                        reasons.append("EMA 9 just crossed below EMA 21 — fresh bearish crossover signal")
                    else:
                        score -= 8
                        reasons.append("EMA 9 is below EMA 21 — short-term downtrend confirmed")

            # ── 5.  Volume confirmation (z-score) ─────────────
            if len(vol) >= 20 and avg_volume > 0:
                vol_mean   = float(vol.rolling(20).mean().iloc[-1])
                vol_std    = float(vol.rolling(20).std().iloc[-1])
                vol_zscore = (volume - vol_mean) / vol_std if vol_std > 0 else 0.0

                prev_close = float(close.iloc[-2]) if len(close) >= 2 else current_price
                price_up   = current_price >= prev_close

                if vol_zscore >= 2.0:
                    if price_up:
                        score += 10
                        reasons.append(f"Volume surge ({vol_zscore:.1f}σ above average) on an up-move — strong conviction buy")
                    else:
                        score -= 10
                        reasons.append(f"Volume surge ({vol_zscore:.1f}σ above average) on a down-move — strong conviction sell")
                elif vol_zscore >= 1.0:
                    if price_up:
                        score += 5
                        reasons.append("Above-average volume with rising price — buy signal confirmed")
                    else:
                        score -= 5
                        reasons.append("Above-average volume with falling price — sell signal confirmed")
                elif vol_zscore <= -1.0:
                    reasons.append("Below-average volume — move lacks conviction, treat signals with caution")

            # ── 6.  ATR volatility context ─────────────────────
            atr = self._atr(high, low, close)
            if atr is not None and current_price > 0:
                atr_pct = round((atr / current_price) * 100, 2)
                if atr_pct > 3.0:
                    reasons.append(f"High volatility stock (ATR: {atr_pct}% of price) — use wider stop-losses")
                elif atr_pct < 1.0:
                    reasons.append(f"Low volatility stock (ATR: {atr_pct}% of price) — tight, stable moves expected")

        except Exception as e:
            logger.error(f"TechnicalAgent.analyze error: {e}")

        score = max(0.0, min(100.0, score))
        return round(score, 1), reasons

    # ── Indicator helpers ────────────────────────────────────

    @staticmethod
    def _rsi(series: pd.Series, period: int = 14) -> Optional[float]:
        if len(series) < period + 1:
            return None
        delta = series.diff().dropna()
        gain  = delta.clip(lower=0).rolling(period).mean()
        loss  = (-delta.clip(upper=0)).rolling(period).mean()
        rs    = gain / loss.replace(0, np.nan)
        rsi   = 100 - (100 / (1 + rs))
        val   = rsi.iloc[-1]
        return round(float(val), 1) if not np.isnan(val) else None

    @staticmethod
    def _macd(series: pd.Series, fast=12, slow=26, signal=9):
        if len(series) < slow + signal:
            return None, None
        ema_fast   = series.ewm(span=fast,   adjust=False).mean()
        ema_slow   = series.ewm(span=slow,   adjust=False).mean()
        macd_line  = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        return float(macd_line.iloc[-1]), float(signal_line.iloc[-1])

    @staticmethod
    def _bollinger(series: pd.Series, window=20, num_std=2):
        if len(series) < window:
            return None, None, None
        rolling = series.rolling(window)
        middle  = rolling.mean()
        std     = rolling.std()
        upper   = middle + num_std * std
        lower   = middle - num_std * std
        return float(upper.iloc[-1]), float(middle.iloc[-1]), float(lower.iloc[-1])

    @staticmethod
    def _atr(high: pd.Series, low: pd.Series, close: pd.Series,
             period: int = 14) -> Optional[float]:
        """Average True Range — volatility measure that accounts for gap openings."""
        if len(close) < period + 1:
            return None
        prev_close = close.shift(1)
        tr = pd.concat([
            high - low,
            (high - prev_close).abs(),
            (low  - prev_close).abs(),
        ], axis=1).max(axis=1)
        atr = tr.rolling(period).mean()
        val = atr.iloc[-1]
        return round(float(val), 4) if not np.isnan(val) else None

    @staticmethod
    def _detect_divergence(close: pd.Series,
                           lookback: int = 20) -> Tuple[Optional[str], Optional[str]]:
        """
        Detects bullish/bearish RSI divergence over the last `lookback` candles.
        Bullish : price makes lower low  but RSI makes higher low  → buy signal
        Bearish : price makes higher high but RSI makes lower high → sell signal
        Returns (divergence_type, reason_string) or (None, None).
        """
        if len(close) < lookback + 15:
            return None, None

        window = close.iloc[-(lookback + 14):]
        delta  = window.diff().dropna()
        gain   = delta.clip(lower=0).rolling(14).mean()
        loss   = (-delta.clip(upper=0)).rolling(14).mean()
        rs     = gain / loss.replace(0, np.nan)
        rsi_s  = 100 - (100 / (1 + rs))

        mid       = lookback // 2
        price_old = float(window.iloc[14 + mid // 2])
        price_new = float(window.iloc[-1])
        rsi_old   = float(rsi_s.iloc[14 + mid // 2])
        rsi_new   = float(rsi_s.iloc[-1])

        if np.isnan(rsi_old) or np.isnan(rsi_new):
            return None, None

        # Bullish divergence: price down, RSI up (5-pt threshold avoids noise)
        if price_new < price_old and rsi_new > rsi_old + 5:
            return "bullish", (
                f"Bullish RSI divergence — price falling but RSI rising "
                f"({rsi_old:.0f} → {rsi_new:.0f}), potential upward reversal"
            )
        # Bearish divergence: price up, RSI down
        if price_new > price_old and rsi_new < rsi_old - 5:
            return "bearish", (
                f"Bearish RSI divergence — price rising but RSI falling "
                f"({rsi_old:.0f} → {rsi_new:.0f}), potential downward reversal"
            )
        return None, None
