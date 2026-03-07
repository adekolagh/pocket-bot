"""
indicators.py — Technical indicators (pure numpy, no TA-Lib required)
RSI(14), Stochastic(5,3,3), Parabolic SAR
Cross-platform: Windows & macOS
"""

import numpy as np
from typing import Tuple, Optional


# ─── RSI ──────────────────────────────────────────────────────────────────────

def rsi(closes: np.ndarray, period: int = 14) -> np.ndarray:
    """
    Wilder's RSI.  Returns array same length as closes (first `period` values = NaN).
    """
    closes = np.asarray(closes, dtype=float)
    n = len(closes)
    result = np.full(n, np.nan)

    if n < period + 1:
        return result

    deltas = np.diff(closes)
    gains  = np.where(deltas > 0, deltas, 0.0)
    losses = np.where(deltas < 0, -deltas, 0.0)

    # Seed first average
    avg_gain = np.mean(gains[:period])
    avg_loss = np.mean(losses[:period])

    for i in range(period, n):
        avg_gain = (avg_gain * (period - 1) + gains[i - 1]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i - 1]) / period
        if avg_loss == 0:
            result[i] = 100.0
        else:
            rs = avg_gain / avg_loss
            result[i] = 100.0 - (100.0 / (1.0 + rs))

    return result


# ─── STOCHASTIC ───────────────────────────────────────────────────────────────

def stochastic(
    highs:  np.ndarray,
    lows:   np.ndarray,
    closes: np.ndarray,
    k_period: int = 5,
    d_period: int = 3,
    smooth:   int = 3,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Stochastic Oscillator (5,3,3) — smoothed.
    Returns (%K, %D) arrays, same length as input (NaNs at start).

    Process:
      raw_k[i] = 100 * (close[i] - lowest_low[i-k+1:i+1]) /
                        (highest_high[i-k+1:i+1] - lowest_low[i-k+1:i+1])
      smooth_k = SMA(raw_k, smooth)   ← this is the displayed %K
      pct_d    = SMA(smooth_k, d_period)
    """
    highs  = np.asarray(highs,  dtype=float)
    lows   = np.asarray(lows,   dtype=float)
    closes = np.asarray(closes, dtype=float)
    n = len(closes)

    raw_k = np.full(n, np.nan)
    for i in range(k_period - 1, n):
        h = np.max(highs[i - k_period + 1 : i + 1])
        l = np.min(lows [i - k_period + 1 : i + 1])
        rng = h - l
        if rng == 0:
            raw_k[i] = 50.0
        else:
            raw_k[i] = 100.0 * (closes[i] - l) / rng

    # Smooth %K
    pct_k = _sma(raw_k, smooth)
    # %D = SMA of smoothed %K
    pct_d = _sma(pct_k, d_period)

    return pct_k, pct_d


def _sma(arr: np.ndarray, period: int) -> np.ndarray:
    """Simple moving average, NaN-aware."""
    result = np.full_like(arr, np.nan)
    for i in range(len(arr)):
        window = arr[max(0, i - period + 1) : i + 1]
        valid  = window[~np.isnan(window)]
        if len(valid) >= period:
            result[i] = np.mean(valid)
    return result


def stoch_cross_up(k: np.ndarray, d: np.ndarray) -> bool:
    """
    True if %K just crossed ABOVE %D on the last two candles.
    k[-2] <= d[-2]  AND  k[-1] > d[-1]
    """
    if len(k) < 2 or np.isnan(k[-2]) or np.isnan(d[-2]):
        return False
    return (k[-2] <= d[-2]) and (k[-1] > d[-1])


def stoch_cross_down(k: np.ndarray, d: np.ndarray) -> bool:
    """
    True if %K just crossed BELOW %D on the last two candles.
    k[-2] >= d[-2]  AND  k[-1] < d[-1]
    """
    if len(k) < 2 or np.isnan(k[-2]) or np.isnan(d[-2]):
        return False
    return (k[-2] >= d[-2]) and (k[-1] < d[-1])


# ─── PARABOLIC SAR ────────────────────────────────────────────────────────────

def parabolic_sar(
    highs:    np.ndarray,
    lows:     np.ndarray,
    af_start: float = 0.02,
    af_step:  float = 0.02,
    af_max:   float = 0.20,
) -> np.ndarray:
    """
    Parabolic SAR.  Returns array of SAR values.
    sar[i] < close[i]  → bullish (SAR below price)
    sar[i] > close[i]  → bearish (SAR above price)
    """
    highs = np.asarray(highs, dtype=float)
    lows  = np.asarray(lows,  dtype=float)
    n = len(highs)
    sar = np.full(n, np.nan)

    if n < 2:
        return sar

    # Initial trend: bullish if second high > first high
    bull       = highs[1] > highs[0]
    af         = af_start
    ep         = highs[1] if bull else lows[1]
    sar[0]     = lows[0]  if bull else highs[0]
    sar[1]     = sar[0]

    for i in range(2, n):
        prev_sar = sar[i - 1]

        if bull:
            sar[i] = prev_sar + af * (ep - prev_sar)
            sar[i] = min(sar[i], lows[i - 1], lows[i - 2] if i >= 2 else lows[i - 1])

            if lows[i] < sar[i]:           # reversal
                bull   = False
                sar[i] = ep
                ep     = lows[i]
                af     = af_start
            else:
                if highs[i] > ep:
                    ep = highs[i]
                    af = min(af + af_step, af_max)
        else:
            sar[i] = prev_sar - af * (prev_sar - ep)
            sar[i] = max(sar[i], highs[i - 1], highs[i - 2] if i >= 2 else highs[i - 1])

            if highs[i] > sar[i]:          # reversal
                bull   = True
                sar[i] = ep
                ep     = highs[i]
                af     = af_start
            else:
                if lows[i] < ep:
                    ep = lows[i]
                    af = min(af + af_step, af_max)

    return sar


def sar_is_bullish(sar: np.ndarray, closes: np.ndarray) -> bool:
    """SAR below latest close → bullish."""
    if np.isnan(sar[-1]):
        return False
    return sar[-1] < closes[-1]


def sar_is_bearish(sar: np.ndarray, closes: np.ndarray) -> bool:
    """SAR above latest close → bearish."""
    if np.isnan(sar[-1]):
        return False
    return sar[-1] > closes[-1]
