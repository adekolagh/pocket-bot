"""
api_client.py — Pocket Option async API wrapper
Fixed connection (no balance verification loop).
Fetches 2M and 1M candles only.
Cross-platform: Windows & macOS
"""

from __future__ import annotations

import asyncio
import logging
from typing import Optional, List, Dict, Any

from config import (
    SSID, IS_DEMO,
    CANDLE_COUNT,
    TF_2M, TF_1M,
)

log = logging.getLogger(__name__)


class PocketOptionClient:
    """
    Thin async wrapper around pocketoptionapi_async.
    Handles connection, candle fetching and trade placement.
    """

    def __init__(self) -> None:
        self.client:    Any           = None
        self.connected: bool          = False
        self._balance:  Optional[float] = None

    # ─── CONNECTION ───────────────────────────────────────────────────────────

    async def connect(self) -> bool:
        """
        Connect to Pocket Option.
        Trusts connect() — no balance-verification loop.
        Candle fetches confirm session health.
        """
        try:
            from pocketoptionapi_async import AsyncPocketOptionClient  # type: ignore

            self.client = AsyncPocketOptionClient(SSID, IS_DEMO)
            await self.client.connect()
            self.connected = True
            log.info("✅ Connected (async library)")
            await asyncio.sleep(3)
            log.info("✅ Session ready")
            return True

        except ImportError:
            log.error(
                "❌ pocketoptionapi_async not installed.  "
                "Run: pip install pocketoptionapi-async"
            )
            return False
        except Exception as exc:
            log.error(f"❌ Connection failed: {exc}")
            self.connected = False
            return False

    async def disconnect(self) -> None:
        """Gracefully disconnect."""
        if self.client:
            try:
                await self.client.disconnect()
            except Exception:
                pass
        self.connected = False
        log.info("🔌 Disconnected")

    # ─── BALANCE ──────────────────────────────────────────────────────────────

    async def get_balance(self) -> float:
        """
        Attempt to fetch balance.
        Returns cached / 0.0 on failure — does NOT crash the bot.
        Balance display is cosmetic; trading logic does not depend on it.
        """
        if not self.connected or self.client is None:
            return self._balance or 0.0
        try:
            raw = await self.client.get_balance()
            if isinstance(raw, dict):
                val = float(raw.get("balance", raw.get("amount", 0)))
            else:
                val = float(raw)
            self._balance = val
            return val
        except Exception as exc:
            log.debug(f"Balance fetch skipped: {exc}")
            return self._balance or 0.0

    # ─── CANDLES ──────────────────────────────────────────────────────────────

    async def get_candles_2m(self, pair: str) -> List[Dict]:
        """Fetch 2-minute candles."""
        return await self._fetch_candles(pair, TF_2M)

    async def get_candles_1m(self, pair: str) -> List[Dict]:
        """Fetch 1-minute candles."""
        return await self._fetch_candles(pair, TF_1M)

    async def get_all_timeframes(
        self, pair: str
    ) -> Dict[str, List[Dict]]:
        """
        Fetch both timeframes concurrently.
        Returns {"2M": [...], "1M": [...]}.
        """
        results = await asyncio.gather(
            self.get_candles_2m(pair),
            self.get_candles_1m(pair),
            return_exceptions=True,
        )
        candles_2m = results[0] if not isinstance(results[0], Exception) else []
        candles_1m = results[1] if not isinstance(results[1], Exception) else []
        return {"2M": candles_2m, "1M": candles_1m}

    async def _fetch_candles(self, pair: str, tf_sec: int) -> List[Dict]:
        """
        Internal: fetch candles for a pair/timeframe.
        Returns list of OHLCV dicts or empty list on error.
        """
        if not self.connected or self.client is None:
            return []
        try:
            raw = await self.client.get_candles(
                pair, tf_sec, CANDLE_COUNT
            )
            if not raw:
                return []
            # Normalize to list of dicts
            normalized = []
            for c in raw:
                if isinstance(c, dict):
                    normalized.append(c)
                elif hasattr(c, "__iter__"):
                    c = list(c)
                    normalized.append({
                        "time":  c[0],
                        "open":  float(c[1]),
                        "high":  float(c[2]),
                        "low":   float(c[3]),
                        "close": float(c[4]),
                    })
            return normalized
        except Exception as exc:
            log.debug(f"Candle fetch {pair}/{tf_sec}s failed: {exc}")
            return []

    # ─── TRADING ──────────────────────────────────────────────────────────────

    async def place_trade(
        self,
        pair:      str,
        direction: str,   # "BUY" or "SELL"
        amount:    float,
        expiry:    int,   # seconds
    ) -> Optional[str]:
        """
        Place a binary options trade.
        Returns trade_id string or None on failure.
        direction: "BUY" → "call", "SELL" → "put"
        """
        if not self.connected or self.client is None:
            log.error("❌ Cannot place trade — not connected")
            return None

        action = "call" if direction == "BUY" else "put"
        try:
            result = await self.client.buy(
                amount, pair, action, expiry
            )
            if result:
                trade_id = str(result) if not isinstance(result, dict) \
                    else str(result.get("id", result))
                log.info(
                    f"📤 Trade placed | {pair} {direction} "
                    f"${amount:.2f} {expiry}s → id={trade_id}"
                )
                return trade_id
            return None
        except Exception as exc:
            log.error(f"❌ Trade failed {pair} {direction}: {exc}")
            return None

    async def check_trade_result(
        self, trade_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Poll for trade outcome.
        Returns dict with keys: result ("win"/"lose"), profit, balance
        or None if not yet resolved.
        """
        if not self.connected or self.client is None:
            return None
        try:
            raw = await self.client.check_win(trade_id)
            if raw is None:
                return None
            if isinstance(raw, dict):
                return {
                    "result":  raw.get("result",  "unknown"),
                    "profit":  float(raw.get("profit", 0)),
                    "balance": float(raw.get("balance", 0)),
                }
            # Some library versions return a float (profit)
            profit = float(raw)
            return {
                "result":  "win" if profit > 0 else "lose",
                "profit":  profit,
                "balance": await self.get_balance(),
            }
        except Exception as exc:
            log.debug(f"Result check {trade_id}: {exc}")
            return None
