"""
====================================================
  Technical Analysis Agent
  ─────────────────────────────────────────────────
  Calculates classic technical indicators and
  returns a score between 0 (very bearish) and
  100 (very bullish), plus a list of plain-English
  reason strings, plus an extras dict.

  Indicators used (all FREE, from 'ta' library):
    • RSI            – momentum oscillator (ADX-aware)
    • Stochastic RSI – refined momentum (K/D crossovers)
    • MACD           – trend/momentum
    • ADX            – trend strength (+DI / -DI)
    • Bollinger Bands – volatility
    • SMA 20, 50 & 200 – trend direction + long-term filter
    • EMA 9 & 21     – short-term crossover
    • Golden/Death Cross – 50-day vs 200-day SMA (20-day lookback + volume confirm)
    • Volume z-score – confirms moves
    • ATR            – volatility context
    • VWAP           – intraday fair value (from 15m OHLCV)
    • Support/Resistance – pivot points + swing levels
====================================================
"""

import logging
from typing import Tuple, List, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class TechnicalAgent:

    def analyze(self, hist: pd.DataFrame, current_price: float,
                volume: int, avg_volume: int,
                intraday: list = None) -> Tuple[float, List[str], dict]:
        """
        Returns (score 0-100, list_of_reasons, extras_dict).
        score > 65  →  BUY territory
        score 35-65 →  HOLD territory
        score < 35  →  SELL territory

        extras_dict contains: vwap, support_level, resistance_level, atr
        """
        score   = 50.0   # neutral starting point
        reasons = []
        extras  = {"vwap": None, "support_level": None, "resistance_level": None, "atr": None}

        try:
            close  = hist["Close"].astype(float)
            high   = hist["High"].astype(float)
            low    = hist["Low"].astype(float)
            vol    = hist["Volume"].astype(float)

            # ── 0. ADX (computed FIRST — used to context RSI scoring) ──────────
            adx_val, plus_di, minus_di = self._adx(high, low, close)

            # ── 1.  RSI (14) — ADX-aware ──────────────────────────────────────
            rsi = self._rsi(close, 14)
            if rsi is not None:
                strong_uptrend   = adx_val is not None and adx_val > 30 and plus_di  > minus_di
                strong_downtrend = adx_val is not None and adx_val > 30 and minus_di > plus_di
                weak_trend       = adx_val is None or adx_val < 25

                if rsi < 30:
                    if strong_downtrend:
                        # Oversold in a strong downtrend — bearish confirmation, not a buy
                        score -= 5
                        reasons.append(f"RSI is {rsi:.0f} — oversold but strong downtrend (ADX {adx_val:.0f}) confirms selling pressure")
                    else:
                        score += 20
                        reasons.append(f"RSI is {rsi:.0f} — oversold zone (below 30)")
                elif rsi < 40:
                    score += 10
                    reasons.append(f"RSI is {rsi:.0f} — slightly oversold (30–40)")
                elif rsi > 70:
                    if strong_uptrend:
                        # Overbought in a strong uptrend — bullish confirmation, NOT a sell
                        score += 5
                        reasons.append(f"RSI is {rsi:.0f} — overbought but strong uptrend (ADX {adx_val:.0f}) confirms buying strength")
                    else:
                        score -= 20
                        reasons.append(f"RSI is {rsi:.0f} — overbought zone (above 70)")
                elif rsi > 60:
                    score -= 10
                    reasons.append(f"RSI is {rsi:.0f} — slightly overbought (60–70)")
                else:
                    reasons.append(f"RSI is {rsi:.0f} — neutral zone")

            # ── 1b. RSI Divergence ────────────────────────────────────────────
            div_type, div_reason = self._detect_divergence(close)
            if div_type == "bullish":
                score += 12
                reasons.append(div_reason)
            elif div_type == "bearish":
                score -= 12
                reasons.append(div_reason)

            # ── 1c. Stochastic RSI ────────────────────────────────────────────
            stoch_k, stoch_d, stoch_reason = self._stoch_rsi(close)
            if stoch_k is not None:
                if stoch_k < 20 and stoch_d < 20:
                    score += 8
                    reasons.append(stoch_reason)
                elif stoch_k > 80 and stoch_d > 80:
                    score -= 8
                    reasons.append(stoch_reason)
                elif stoch_k > stoch_d and stoch_k < 50:   # bullish crossover below midline
                    score += 4
                    reasons.append(stoch_reason)
                elif stoch_k < stoch_d and stoch_k > 50:   # bearish crossover above midline
                    score -= 4
                    reasons.append(stoch_reason)

            # ── 2.  MACD (12, 26, 9) ──────────────────────────────────────────
            macd_line, signal_line = self._macd(close)
            if macd_line is not None and signal_line is not None:
                if macd_line > signal_line:
                    score += 15
                    reasons.append("MACD crossed above signal line — upward momentum building")
                else:
                    score -= 15
                    reasons.append("MACD is below signal line — downward momentum")

            # ── 3.  Bollinger Bands (20, 2σ) ──────────────────────────────────
            upper, middle, lower = self._bollinger(close, 20)
            if upper is not None:
                band_width = upper - lower
                if band_width > 0:
                    pos = (current_price - lower) / band_width   # 0 = at lower, 1 = at upper
                    if current_price <= lower:
                        score += 15
                        reasons.append("Price is at/below lower Bollinger Band — at lower support")
                    elif current_price >= upper:
                        score -= 15
                        reasons.append("Price is at/above upper Bollinger Band — at upper resistance")
                    elif pos < 0.3:
                        score += 8
                        reasons.append("Price is near lower Bollinger Band — close to lower support")
                    elif pos > 0.7:
                        score -= 8
                        reasons.append("Price is near upper Bollinger Band — close to upper resistance")

            # ── 4.  Moving Averages (SMA 20 & SMA 50) ─────────────────────────
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

            # ── 4a-ii.  200-day SMA (long-term trend filter) ──────────────────
            if len(close) >= 200:
                sma200 = float(close.rolling(200).mean().iloc[-1])
                if current_price > sma200:
                    score += 8
                    reasons.append("Price is above 200-day SMA — long-term uptrend intact")
                else:
                    score -= 8
                    reasons.append("Price is below 200-day SMA — long-term downtrend warning")

                # Golden Cross / Death Cross — 20-day lookback + volume confirmation
                if len(close) >= 220:
                    sma50_now   = float(close.rolling(50).mean().iloc[-1])
                    sma50_prev  = float(close.rolling(50).mean().iloc[-20])
                    sma200_prev = float(close.rolling(200).mean().iloc[-20])

                    # Volume confirmation: was yesterday's volume z-score elevated?
                    vol_zscore_cross = 0.0
                    if len(vol) >= 20:
                        vol_mean = float(vol.rolling(20).mean().iloc[-1])
                        vol_std  = float(vol.rolling(20).std().iloc[-1])
                        if vol_std > 0:
                            vol_zscore_cross = (float(vol.iloc[-1]) - vol_mean) / vol_std

                    cross_pts = 12 if vol_zscore_cross > 1.0 else 6  # full pts if confirmed by volume

                    if sma50_now > sma200 and sma50_prev <= sma200_prev:
                        score += cross_pts
                        reasons.append(
                            "Golden Cross detected — 50-day SMA crossed above 200-day SMA (strong bullish)"
                            + (" — volume confirmed" if vol_zscore_cross > 1.0 else "")
                        )
                    elif sma50_now < sma200 and sma50_prev >= sma200_prev:
                        score -= cross_pts
                        reasons.append(
                            "Death Cross detected — 50-day SMA crossed below 200-day SMA (strong bearish)"
                            + (" — volume confirmed" if vol_zscore_cross > 1.0 else "")
                        )

            # ── 4b. EMA 9 & EMA 21 Crossover ──────────────────────────────────
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

            # ── 5.  Volume confirmation (z-score) ──────────────────────────────
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

            # ── 5b. ADX – trend strength (scoring block, after RSI uses it above) ──
            if adx_val is not None:
                if adx_val > 25:
                    if plus_di > minus_di:
                        score += 8
                        reasons.append(
                            f"ADX {adx_val:.0f} (strong trend) with +DI {plus_di:.0f} > "
                            f"-DI {minus_di:.0f} — uptrend has real conviction"
                        )
                    else:
                        score -= 8
                        reasons.append(
                            f"ADX {adx_val:.0f} (strong trend) with -DI {minus_di:.0f} > "
                            f"+DI {plus_di:.0f} — downtrend has real conviction"
                        )
                elif adx_val < 20:
                    reasons.append(
                        f"ADX {adx_val:.0f} — weak trend, market is ranging. "
                        f"RSI and Stochastic signals more reliable than trend-following here."
                    )

            # ── 6.  ATR volatility context ──────────────────────────────────────
            atr = self._atr(high, low, close)
            extras["atr"] = atr
            if atr is not None and current_price > 0:
                atr_pct = round((atr / current_price) * 100, 2)
                if atr_pct > 3.0:
                    reasons.append(f"High volatility stock (ATR: {atr_pct}% of price) — use wider stop-losses")
                elif atr_pct < 1.0:
                    reasons.append(f"Low volatility stock (ATR: {atr_pct}% of price) — tight, stable moves expected")

            # ── 7.  VWAP — intraday fair value ─────────────────────────────────
            vwap_val = self._vwap(intraday) if intraday else None
            extras["vwap"] = vwap_val
            if vwap_val is not None and current_price > 0:
                diff_pct = (current_price - vwap_val) / vwap_val * 100
                if current_price > vwap_val:
                    score += 8
                    reasons.append(f"Price ₹{current_price:.0f} is above VWAP ₹{vwap_val:.0f} (+{diff_pct:.1f}%) — intraday bullish bias")
                else:
                    score -= 8
                    reasons.append(f"Price ₹{current_price:.0f} is below VWAP ₹{vwap_val:.0f} ({diff_pct:.1f}%) — intraday bearish bias")

            # ── 8.  Support & Resistance (pivot points) ────────────────────────
            pivots = self._pivot_points(high, low, close)
            if pivots:
                s1 = pivots.get("s1")
                s2 = pivots.get("s2")
                r1 = pivots.get("r1")
                r2 = pivots.get("r2")
                extras["support_level"]    = s1
                extras["resistance_level"] = r1

                # Check proximity (within 1.5%)
                threshold = 0.015
                near_support = (
                    (s1 and abs(current_price - s1) / current_price < threshold) or
                    (s2 and abs(current_price - s2) / current_price < threshold)
                )
                near_resistance = (
                    (r1 and abs(current_price - r1) / current_price < threshold) or
                    (r2 and abs(current_price - r2) / current_price < threshold)
                )

                if near_support:
                    nearest = s1 if (s1 and abs(current_price - s1) < abs(current_price - (s2 or s1))) else s2
                    score += 5
                    reasons.append(f"Price near pivot support ₹{nearest:.0f} — potential bounce zone")
                elif near_resistance:
                    nearest = r1 if (r1 and abs(current_price - r1) < abs(current_price - (r2 or r1))) else r2
                    score -= 5
                    reasons.append(f"Price near pivot resistance ₹{nearest:.0f} — potential rejection zone")

        except Exception as e:
            logger.error(f"TechnicalAgent.analyze error: {e}")

        score = max(0.0, min(100.0, score))
        return round(score, 1), reasons, extras

    # ── Indicator helpers ────────────────────────────────────────────────────

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
    def _stoch_rsi(close: pd.Series, window: int = 14,
                   smooth_k: int = 3, smooth_d: int = 3):
        """
        Stochastic RSI — applies the Stochastic formula to RSI values.
        Returns (k_pct, d_pct, reason_str) or (None, None, None).
        k_pct / d_pct are in 0–100 scale.
        """
        min_len = window * 2 + smooth_k + smooth_d
        if len(close) < min_len:
            return None, None, None
        try:
            from ta.momentum import StochRSIIndicator
            ind = StochRSIIndicator(
                close=close, window=window, smooth1=smooth_k, smooth2=smooth_d
            )
            k = float(ind.stochrsi_k().iloc[-1]) * 100
            d = float(ind.stochrsi_d().iloc[-1]) * 100
            if np.isnan(k) or np.isnan(d):
                return None, None, None

            if k < 20 and d < 20:
                label = f"Stochastic RSI K={k:.0f}, D={d:.0f} — deeply OVERSOLD, strong buy momentum"
            elif k > 80 and d > 80:
                label = f"Stochastic RSI K={k:.0f}, D={d:.0f} — deeply OVERBOUGHT, caution"
            elif k > d and k < 50:
                label = f"Stochastic RSI bullish crossover below 50 (K={k:.0f} > D={d:.0f}) — early buy signal"
            elif k < d and k > 50:
                label = f"Stochastic RSI bearish crossover above 50 (K={k:.0f} < D={d:.0f}) — early sell signal"
            else:
                label = f"Stochastic RSI K={k:.0f}, D={d:.0f} — neutral"
            return round(k, 1), round(d, 1), label
        except Exception:
            return None, None, None

    @staticmethod
    def _adx(high: pd.Series, low: pd.Series, close: pd.Series,
             window: int = 14):
        """
        Average Directional Index — measures trend strength (NOT direction).
        Returns (adx, plus_di, minus_di) or (None, None, None).
        ADX > 25 = trending; ADX < 20 = ranging.
        """
        if len(close) < window * 2:
            return None, None, None
        try:
            from ta.trend import ADXIndicator
            ind     = ADXIndicator(high=high, low=low, close=close, window=window)
            adx     = float(ind.adx().iloc[-1])
            plus_di = float(ind.adx_pos().iloc[-1])
            minus_di= float(ind.adx_neg().iloc[-1])
            if np.isnan(adx):
                return None, None, None
            return round(adx, 1), round(plus_di, 1), round(minus_di, 1)
        except Exception:
            return None, None, None

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

    @staticmethod
    def _vwap(intraday_data: list) -> Optional[float]:
        """
        Volume Weighted Average Price from 15m intraday bars.
        Requires bars with high, low, close, volume keys.
        Returns the VWAP value or None if data insufficient.
        """
        if not intraday_data:
            return None
        try:
            cum_tp_vol = 0.0
            cum_vol    = 0.0
            for bar in intraday_data:
                h = bar.get("high", bar.get("price", 0))
                l = bar.get("low",  bar.get("price", 0))
                c = bar.get("close", bar.get("price", 0))
                v = bar.get("volume", 0)
                if v > 0:
                    typical_price = (h + l + c) / 3.0
                    cum_tp_vol += typical_price * v
                    cum_vol    += v
            if cum_vol > 0:
                return round(cum_tp_vol / cum_vol, 2)
        except Exception:
            pass
        return None

    @staticmethod
    def _pivot_points(high: pd.Series, low: pd.Series,
                      close: pd.Series) -> Optional[dict]:
        """
        Standard pivot points from the most recent completed day.
        Returns dict with pivot, s1, s2, r1, r2 or None if insufficient data.
        """
        if len(close) < 2:
            return None
        try:
            prev_h = float(high.iloc[-2])
            prev_l = float(low.iloc[-2])
            prev_c = float(close.iloc[-2])

            pivot = (prev_h + prev_l + prev_c) / 3.0
            r1    = 2 * pivot - prev_l
            r2    = pivot + (prev_h - prev_l)
            s1    = 2 * pivot - prev_h
            s2    = pivot - (prev_h - prev_l)

            return {
                "pivot": round(pivot, 2),
                "r1":    round(r1, 2),
                "r2":    round(r2, 2),
                "s1":    round(s1, 2),
                "s2":    round(s2, 2),
            }
        except Exception:
            return None
