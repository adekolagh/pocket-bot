"""
risk_manager.py — Trade sizing, concurrent trade limits, session stats
Cross-platform: Windows & macOS
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, Set

from config import TRADE_AMOUNT, MAX_CONCURRENT

log = logging.getLogger(__name__)


@dataclass
class SessionStats:
    total_trades: int   = 0
    wins:         int   = 0
    losses:       int   = 0
    total_profit: float = 0.0
    start_balance: float = 0.0

    @property
    def win_rate(self) -> float:
        if self.total_trades == 0:
            return 0.0
        return self.wins / self.total_trades * 100

    @property
    def net_profit(self) -> float:
        return self.total_profit


class RiskManager:
    """
    Manages:
      - How many trades can be open at once (MAX_CONCURRENT)
      - Per-pair cooldown (no re-entry on same pair while trade is live)
      - Session profit/loss tracking
    """

    def __init__(self, start_balance: float = 0.0) -> None:
        self.stats             = SessionStats(start_balance=start_balance)
        self._active_pairs:    Set[str] = set()
        self._open_trade_count: int     = 0

    # ─── TRADE GATE ───────────────────────────────────────────────────────────

    def can_trade(self, pair: str) -> bool:
        """Return True if a new trade is permitted."""
        if pair in self._active_pairs:
            log.debug(f"⏳ {pair} — already in active trade, skipping")
            return False
        if self._open_trade_count >= MAX_CONCURRENT:
            log.debug(f"⛔ Max concurrent trades ({MAX_CONCURRENT}) reached")
            return False
        return True

    def register_trade(self, pair: str) -> None:
        """Call when a trade is placed."""
        self._active_pairs.add(pair)
        self._open_trade_count += 1
        self.stats.total_trades += 1
        log.debug(f"📌 Trade registered: {pair} (open={self._open_trade_count})")

    def close_trade(self, pair: str, profit: float) -> None:
        """Call when a trade result is confirmed."""
        self._active_pairs.discard(pair)
        self._open_trade_count = max(0, self._open_trade_count - 1)
        self.stats.total_profit += profit
        if profit > 0:
            self.stats.wins += 1
        else:
            self.stats.losses += 1
        log.debug(
            f"✅ Trade closed: {pair} profit={profit:+.2f} "
            f"(W={self.stats.wins} L={self.stats.losses})"
        )

    # ─── SIZING ───────────────────────────────────────────────────────────────

    def trade_amount(self) -> float:
        """Fixed trade amount (extend here for Martingale etc.)."""
        return TRADE_AMOUNT

    # ─── STATUS ───────────────────────────────────────────────────────────────

    def summary(self) -> str:
        s = self.stats
        return (
            f"Trades={s.total_trades} | "
            f"W={s.wins} L={s.losses} | "
            f"WR={s.win_rate:.1f}% | "
            f"P/L={s.net_profit:+.2f}"
        )
