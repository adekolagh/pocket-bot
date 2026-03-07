"""
strategy.py — 2M / 1M Wilder Strategy
═══════════════════════════════════════════════════════════════════════════════

STEP 1 — 2M LOCK
  BUY  lock : RSI(14) > 40  AND  Stoch(5,3,3) K crosses D upward   AND  SAR below price
  SELL lock : RSI(14) < 60  AND  Stoch(5,3,3) K crosses D downward  AND  SAR above price

STEP 2 — 1M ENTRY  (requires matching 2M lock)
  BUY  entry : RSI(14) > 40  AND  K crosses D upward   AND  SAR below price  (MUST)
  SELL entry : RSI(14) > 60  AND  K crosses D downward  AND  SAR above price  (MUST)

Expiry = 1 minute countdown.
═══════════════════════════════════════════════════════════════════════════════
"""

from __future__ import annotations

import numpy as np
import logging
from typing import Optional, Dict, Any

from indicators import (
    rsi, stochastic, parabolic_sar,
    stoch_cross_up, stoch_cross_down,
    sar_is_bullish, sar_is_bearish,
)
from config import (
    RSI_PERIOD, STOCH_K, STOCH_D, STOCH_SMOOTH,
    RSI_BUY_MIN_2M, RSI_SELL_MAX_2M,
    RSI_BUY_MIN_1M, RSI_SELL_MIN_1M,
)

log = logging.getLogger(__name__)

# Per-pair 2M lock cache: {"EURUSD_otc": "BUY" | "SELL" | None}
_lock_cache: Dict[str, Optional[str]] = {}


def clear_lock(pair: str) -> None:
    """Clear the 2M lock for a pair after a trade fires."""
    _lock_cache[pair] = None


def _extract_ohlc(candles: list) -> tuple[np.ndarray, ...]:
    """
    Convert candle list → (opens, highs, lows, closes) numpy arrays.
    Candles can be dicts with keys open/high/low/close
    or lists/tuples in [time, open, high, low, close] order.
    """
    opens, highs, lows, closes = [], [], [], []
    for c in candles:
        if isinstance(c, dict):
            opens.append(float(c.get("open",  c.get("o", 0))))
            highs.append(float(c.get("high",  c.get("h", 0))))
            lows.append( float(c.get("low",   c.get("l", 0))))
            closes.append(float(c.get("close", c.get("c", 0))))
        else:
            # list/tuple: [time, open, high, low, close]
            opens.append(float(c[1]))
            highs.append(float(c[2]))
            lows.append( float(c[3]))
            closes.append(float(c[4]))
    return (
        np.array(opens),
        np.array(highs),
        np.array(lows),
        np.array(closes),
    )


def _compute_indicators(candles: list) -> Optional[Dict[str, Any]]:
    """
    Run all indicators on a candle list.
    Returns dict or None if not enough data.
    """
    if len(candles) < 30:
        return None

    _, highs, lows, closes = _extract_ohlc(candles)

    rsi_vals  = rsi(closes, period=RSI_PERIOD)
    k, d      = stochastic(highs, lows, closes, STOCH_K, STOCH_D, STOCH_SMOOTH)
    sar_vals  = parabolic_sar(highs, lows)

    # Need at least 2 valid K/D values for cross detection
    if np.isnan(k[-1]) or np.isnan(d[-1]) or np.isnan(rsi_vals[-1]):
        return None

    return {
        "rsi":       float(rsi_vals[-1]),
        "k":         k,
        "d":         d,
        "sar":       sar_vals,
        "closes":    closes,
        "cross_up":  stoch_cross_up(k, d),
        "cross_dn":  stoch_cross_down(k, d),
        "sar_bull":  sar_is_bullish(sar_vals, closes),
        "sar_bear":  sar_is_bearish(sar_vals, closes),
    }


# ─── PUBLIC API ───────────────────────────────────────────────────────────────

def evaluate_2m_lock(pair: str, candles_2m: list) -> Optional[str]:
    """
    Evaluate 2M timeframe and update lock cache.
    Returns "BUY", "SELL", or None.

    BUY  lock: RSI > 40  AND  K crosses D up    AND  SAR below
    SELL lock: RSI < 60  AND  K crosses D down   AND  SAR above
    """
    ind = _compute_indicators(candles_2m)
    if ind is None:
        _lock_cache[pair] = None
        return None

    rsi_val   = ind["rsi"]
    cross_up  = ind["cross_up"]
    cross_dn  = ind["cross_dn"]
    sar_bull  = ind["sar_bull"]
    sar_bear  = ind["sar_bear"]

    lock: Optional[str] = None

    if rsi_val > RSI_BUY_MIN_2M and cross_up and sar_bull:
        lock = "BUY"
        log.debug(
            f"[2M BUY LOCK] {pair} | RSI={rsi_val:.1f} >40, "
            f"K/D cross up, SAR below"
        )

    elif rsi_val < RSI_SELL_MAX_2M and cross_dn and sar_bear:
        lock = "SELL"
        log.debug(
            f"[2M SELL LOCK] {pair} | RSI={rsi_val:.1f} <60, "
            f"K/D cross down, SAR above"
        )

    _lock_cache[pair] = lock
    return lock


def evaluate_1m_entry(pair: str, candles_1m: list) -> Optional[str]:
    """
    Evaluate 1M timeframe for trade entry.
    Only fires if a matching 2M lock exists for this pair.
    Returns "BUY", "SELL", or None.

    BUY  entry: RSI > 40  AND  K crosses D up    AND  SAR below  (MUST)
    SELL entry: RSI > 60  AND  K crosses D down   AND  SAR above  (MUST)
    """
    lock_2m = _lock_cache.get(pair)
    if lock_2m is None:
        return None

    ind = _compute_indicators(candles_1m)
    if ind is None:
        return None

    rsi_val  = ind["rsi"]
    cross_up = ind["cross_up"]
    cross_dn = ind["cross_dn"]
    sar_bull = ind["sar_bull"]
    sar_bear = ind["sar_bear"]

    signal: Optional[str] = None

    if lock_2m == "BUY":
        if rsi_val > RSI_BUY_MIN_1M and cross_up and sar_bull:
            signal = "BUY"
            log.info(
                f"✅ [1M BUY ENTRY] {pair} | RSI={rsi_val:.1f} >40, "
                f"K/D cross up, SAR below — 2M lock confirmed"
            )

    elif lock_2m == "SELL":
        if rsi_val > RSI_SELL_MIN_1M and cross_dn and sar_bear:
            signal = "SELL"
            log.info(
                f"✅ [1M SELL ENTRY] {pair} | RSI={rsi_val:.1f} >60, "
                f"K/D cross down, SAR above — 2M lock confirmed"
            )

    return signal


def get_signal(pair: str, candles_2m: list, candles_1m: list) -> Optional[str]:
    """
    Full signal evaluation for a pair.
    1. Evaluates / refreshes 2M lock.
    2. Checks 1M entry if lock exists.
    Returns "BUY", "SELL", or None.
    """
    evaluate_2m_lock(pair, candles_2m)
    return evaluate_1m_entry(pair, candles_1m)


def get_lock_status(pair: str) -> Optional[str]:
    """Return current 2M lock for a pair (for dashboard display)."""
    return _lock_cache.get(pair)


def get_all_locks() -> Dict[str, Optional[str]]:
    """Return full lock cache (for dashboard)."""
    return dict(_lock_cache)
