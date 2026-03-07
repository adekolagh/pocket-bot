"""
dashboard.py — Live terminal dashboard
Cross-platform: Windows & macOS
Uses only stdlib + colorama (no curses, which is unavailable on Windows).
"""

from __future__ import annotations

import sys
import os
import logging
from datetime import datetime
from typing import Dict, Optional, Any

log = logging.getLogger(__name__)

try:
    import colorama  # type: ignore
    colorama.init(autoreset=True)
    _HAS_COLORAMA = True
except ImportError:
    _HAS_COLORAMA = False

# ANSI helpers (safe on macOS; colorama translates on Windows)
_G   = "\033[92m"   # green
_R   = "\033[91m"   # red
_Y   = "\033[93m"   # yellow
_C   = "\033[96m"   # cyan
_W   = "\033[97m"   # bright white
_DIM = "\033[90m"   # dark grey
_RST = "\033[0m"


def _clr() -> str:
    """Return ANSI clear-screen + move-cursor-to-top string."""
    return "\033[2J\033[H"


class Dashboard:
    """
    Lightweight live dashboard.
    Call .render() on each scan cycle to refresh the terminal.
    """

    def __init__(self) -> None:
        self.session_start   = datetime.now()
        self.balance:  float = 0.0
        self.lock_states:  Dict[str, Optional[str]] = {}
        self.active_trades: Dict[str, Dict[str, Any]] = {}

    def update(
        self,
        balance:      float,
        lock_states:  Dict[str, Optional[str]],
        active_trades: Dict[str, Dict[str, Any]],
    ) -> None:
        self.balance       = balance
        self.lock_states   = lock_states
        self.active_trades = active_trades

    def render(self, stats: Any) -> None:
        """Render dashboard to stdout."""
        now      = datetime.now().strftime("%H:%M:%S")
        elapsed  = datetime.now() - self.session_start
        h, rem   = divmod(int(elapsed.total_seconds()), 3600)
        m, s     = divmod(rem, 60)

        lines: list[str] = []
        lines.append(_clr())
        lines.append(f"{_C}{'═'*60}{_RST}")
        lines.append(f"{_W}  🤖  POCKET OPTION — WILDER BOT  {_DIM}[2M/1M]{_RST}")
        lines.append(f"{_C}{'═'*60}{_RST}")
        lines.append(
            f"  {_DIM}Time{_RST} {now}   "
            f"{_DIM}Up{_RST} {h:02d}h{m:02d}m{s:02d}s   "
            f"{_DIM}Balance{_RST} {_W}${self.balance:.2f}{_RST}"
        )
        lines.append(
            f"  {_DIM}Trades{_RST} {stats.total_trades}  "
            f"{_G}W {stats.wins}{_RST}  "
            f"{_R}L {stats.losses}{_RST}  "
            f"{_Y}WR {stats.win_rate:.1f}%{_RST}  "
            f"P/L {_G if stats.net_profit >= 0 else _R}"
            f"{stats.net_profit:+.2f}{_RST}"
        )
        lines.append(f"{_C}{'─'*60}{_RST}")

        # Active trades
        if self.active_trades:
            lines.append(f"  {_Y}⚡ ACTIVE TRADES{_RST}")
            for pair, td in self.active_trades.items():
                dir_col = _G if td["direction"] == "BUY" else _R
                lines.append(
                    f"    {dir_col}{td['direction']}{_RST} {pair}  "
                    f"${td['amount']:.2f}  exp={td['expiry']}s"
                )
            lines.append(f"{_C}{'─'*60}{_RST}")

        # 2M lock table
        buy_locks  = [p for p, v in self.lock_states.items() if v == "BUY"]
        sell_locks = [p for p, v in self.lock_states.items() if v == "SELL"]

        if buy_locks or sell_locks:
            lines.append(f"  {_DIM}2M LOCKS{_RST}")
            for pair in buy_locks:
                lines.append(f"    {_G}▲ BUY  {pair}{_RST}")
            for pair in sell_locks:
                lines.append(f"    {_R}▼ SELL {pair}{_RST}")
        else:
            lines.append(f"  {_DIM}No 2M locks active{_RST}")

        lines.append(f"{_C}{'═'*60}{_RST}")
        lines.append(f"  {_DIM}Press Ctrl+C to stop{_RST}")

        sys.stdout.write("\n".join(lines) + "\n")
        sys.stdout.flush()
