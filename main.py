"""
main.py — Pocket Option Wilder Bot — Main Entry Point
2M/1M Strategy | Cross-platform: Windows & macOS

Run:
  Windows  →  python main.py
  macOS    →  python3 main.py
"""

from __future__ import annotations

import asyncio
import logging
import sys
import platform
from datetime import datetime
from typing import Dict, Optional, Any

# ── Cross-platform asyncio policy ─────────────────────────────────────────────
if platform.system() == "Windows":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# ── Local imports ─────────────────────────────────────────────────────────────
from logger       import setup_logging
from config       import PAIRS, SCAN_INTERVAL_SEC, TRADE_AMOUNT, EXPIRY_SEC
from api_client   import PocketOptionClient
from strategy     import get_signal, get_lock_status, get_all_locks, clear_lock
from risk_manager import RiskManager
from dashboard    import Dashboard
from reporter     import log_scan_cycle, log_trade_result, generate_session_report

log = logging.getLogger(__name__)


class WilderBot:
    def __init__(self) -> None:
        self.api           = PocketOptionClient()
        self.risk          = RiskManager()
        self.dash          = Dashboard()
        self.session_start = datetime.now()
        # trade_id → {pair, direction, lock_2m, amount, expiry, rsi_2m, rsi_1m, ...}
        self._pending: Dict[str, Dict[str, Any]] = {}

    # ─── MAIN RUN ─────────────────────────────────────────────────────────────

    async def run(self) -> None:
        setup_logging()
        log.info("🚀 Wilder Bot starting…")

        if not await self.api.connect():
            log.error("❌ Could not connect. Exiting.")
            return

        balance = await self.api.get_balance()
        self.risk.stats.start_balance = balance
        log.info(f"💰 Starting balance: ${balance:.2f}")
        log.info(f"📋 Scanning {len(PAIRS)} pairs on 2M + 1M")
        log.info("Bot running — press Ctrl+C to stop\n")

        try:
            await self._main_loop()
        except KeyboardInterrupt:
            log.info("\n⛔ Interrupted by user")
        finally:
            await self._shutdown()

    # ─── MAIN LOOP ────────────────────────────────────────────────────────────

    async def _main_loop(self) -> None:
        while True:
            cycle_start = asyncio.get_event_loop().time()

            # 1. Check pending trade results
            await self._check_results()

            # 2. Scan all pairs
            signals = await self._scan_pairs()

            # 3. Place trades for confirmed signals
            await self._place_trades(signals)

            # 4. Refresh dashboard
            balance = await self.api.get_balance()
            self.dash.update(
                balance       = balance,
                lock_states   = get_all_locks(),
                active_trades = {
                    td["pair"]: td for td in self._pending.values()
                },
            )
            self.dash.render(self.risk.stats)

            # 5. Log scan summary
            log_scan_cycle(signals, get_all_locks())

            # 6. Sleep until next cycle
            elapsed = asyncio.get_event_loop().time() - cycle_start
            sleep   = max(0.5, SCAN_INTERVAL_SEC - elapsed)
            await asyncio.sleep(sleep)

    # ─── SCAN ─────────────────────────────────────────────────────────────────

    async def _scan_pairs(self) -> Dict[str, Optional[str]]:
        """
        Fetch 2M + 1M candles for every pair concurrently,
        run strategy, collect signals.
        """
        tasks = {
            pair: asyncio.create_task(self.api.get_all_timeframes(pair))
            for pair in PAIRS
        }
        signals: Dict[str, Optional[str]] = {}

        for pair, task in tasks.items():
            try:
                tf_data = await task
                c2m = tf_data.get("2M", [])
                c1m = tf_data.get("1M", [])

                if len(c2m) < 30 or len(c1m) < 30:
                    signals[pair] = None
                    continue

                sig = get_signal(pair, c2m, c1m)
                signals[pair] = sig

            except Exception as exc:
                log.debug(f"Scan error {pair}: {exc}")
                signals[pair] = None

        return signals

    # ─── PLACE TRADES ─────────────────────────────────────────────────────────

    async def _place_trades(
        self, signals: Dict[str, Optional[str]]
    ) -> None:
        for pair, sig in signals.items():
            if sig is None:
                continue
            if not self.risk.can_trade(pair):
                continue

            amount = self.risk.trade_amount()
            trade_id = await self.api.place_trade(
                pair, sig, amount, EXPIRY_SEC
            )
            if trade_id:
                lock_2m = get_lock_status(pair) or sig
                self._pending[trade_id] = {
                    "pair":      pair,
                    "direction": sig,
                    "lock_2m":   lock_2m,
                    "amount":    amount,
                    "expiry":    EXPIRY_SEC,
                }
                self.risk.register_trade(pair)
                clear_lock(pair)   # prevent re-entry until 2M re-locks

    # ─── RESULT CHECK ─────────────────────────────────────────────────────────

    async def _check_results(self) -> None:
        resolved = []
        for trade_id, meta in list(self._pending.items()):
            outcome = await self.api.check_trade_result(trade_id)
            if outcome is None:
                continue
            result  = outcome.get("result",  "unknown")
            profit  = outcome.get("profit",  0.0)
            balance = outcome.get("balance", 0.0)

            if result in ("win", "lose"):
                self.risk.close_trade(meta["pair"], profit)
                log_trade_result(
                    pair      = meta["pair"],
                    direction = meta["direction"],
                    lock_2m   = meta["lock_2m"],
                    amount    = meta["amount"],
                    expiry    = meta["expiry"],
                    rsi_2m    = meta.get("rsi_2m", 0.0),
                    rsi_1m    = meta.get("rsi_1m", 0.0),
                    k_2m      = meta.get("k_2m",   0.0),
                    d_2m      = meta.get("d_2m",   0.0),
                    k_1m      = meta.get("k_1m",   0.0),
                    d_1m      = meta.get("d_1m",   0.0),
                    result    = result,
                    profit    = profit,
                    balance   = balance,
                )
                resolved.append(trade_id)

        for tid in resolved:
            del self._pending[tid]

    # ─── SHUTDOWN ─────────────────────────────────────────────────────────────

    async def _shutdown(self) -> None:
        await self.api.disconnect()
        generate_session_report(self.risk.stats, self.session_start)


# ─── ENTRY POINT ──────────────────────────────────────────────────────────────

def main() -> None:
    bot = WilderBot()
    try:
        asyncio.run(bot.run())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
