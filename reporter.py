"""
reporter.py — Trade result logging and session report generation
Cross-platform: Windows & macOS
"""

from __future__ import annotations

import csv
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from config import LOG_DIR

log = logging.getLogger(__name__)

# CSV file for this session (created on first write)
_csv_path: Optional[Path] = None


def _get_csv_path() -> Path:
    global _csv_path
    if _csv_path is None:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        _csv_path = LOG_DIR / f"trades_{ts}.csv"
    return _csv_path


def log_scan_cycle(
    all_signals: Dict[str, Optional[str]],
    lock_states: Dict[str, Optional[str]],
) -> None:
    """
    Log a brief summary of a scan cycle.
    all_signals : pair → "BUY" | "SELL" | None  (1M signals)
    lock_states : pair → "BUY" | "SELL" | None  (2M locks)
    """
    active_locks   = {p: v for p, v in lock_states.items() if v}
    active_signals = {p: v for p, v in all_signals.items() if v}

    log.info(
        f"🔍 Scan | 2M locks: {len(active_locks)} | "
        f"1M signals: {len(active_signals)}"
    )
    for pair, sig in active_signals.items():
        log.info(f"   ↳ {pair}: {sig}")


def log_trade_result(
    pair:      str,
    direction: str,
    lock_2m:   str,
    amount:    float,
    expiry:    int,
    rsi_2m:    float,
    rsi_1m:    float,
    k_2m:      float,
    d_2m:      float,
    k_1m:      float,
    d_1m:      float,
    result:    str,    # "win" | "lose" | "pending"
    profit:    float,
    balance:   float,
) -> None:
    """
    Append a trade record to the session CSV and log to console.
    """
    csv_path = _get_csv_path()
    write_header = not csv_path.exists()

    row = {
        "time":      datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "pair":      pair,
        "direction": direction,
        "lock_2m":   lock_2m,
        "amount":    f"{amount:.2f}",
        "expiry_s":  expiry,
        "rsi_2m":    f"{rsi_2m:.2f}",
        "rsi_1m":    f"{rsi_1m:.2f}",
        "k_2m":      f"{k_2m:.2f}",
        "d_2m":      f"{d_2m:.2f}",
        "k_1m":      f"{k_1m:.2f}",
        "d_1m":      f"{d_1m:.2f}",
        "result":    result,
        "profit":    f"{profit:+.2f}",
        "balance":   f"{balance:.2f}",
    }

    try:
        with open(csv_path, "a", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(row.keys()))
            if write_header:
                writer.writeheader()
            writer.writerow(row)
    except OSError as exc:
        log.warning(f"Could not write trade CSV: {exc}")

    icon = "🟢" if result == "win" else ("🔴" if result == "lose" else "⏳")
    log.info(
        f"{icon} {pair} {direction} | {result.upper()} | "
        f"profit={profit:+.2f} | balance={balance:.2f}"
    )


def generate_session_report(
    stats: Any,   # SessionStats from risk_manager
    session_start: datetime,
) -> None:
    """Print a formatted end-of-session summary."""
    duration = datetime.now() - session_start
    hours, rem = divmod(int(duration.total_seconds()), 3600)
    mins, secs  = divmod(rem, 60)

    lines = [
        "",
        "═" * 55,
        "  📊  SESSION REPORT",
        "═" * 55,
        f"  Duration    : {hours:02d}h {mins:02d}m {secs:02d}s",
        f"  Total Trades: {stats.total_trades}",
        f"  Wins        : {stats.wins}",
        f"  Losses      : {stats.losses}",
        f"  Win Rate    : {stats.win_rate:.1f}%",
        f"  Net P/L     : {stats.net_profit:+.2f}",
        "═" * 55,
        "",
    ]
    report = "\n".join(lines)
    log.info(report)

    # Also save to file
    try:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = LOG_DIR / f"report_{ts}.txt"
        report_path.write_text(report, encoding="utf-8")
        log.info(f"📄 Report saved → {report_path}")
    except OSError as exc:
        log.warning(f"Could not save report: {exc}")
