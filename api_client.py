"""
api_client.py — Pocket Option API wrapper
Uses BinaryOptionsToolsV2
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

    def __init__(self) -> None:
        self.client:    Any             = None
        self.connected: bool            = False
        self._balance:  Optional[float] = None

    # ─── CONNECTION ───────────────────────────────────────────────────────────

    async def connect(self) -> bool:
        try:
            from BinaryOptionsToolsV2.pocketoption import PocketOptionAsync  # type: ignore

            # Increase connection timeout to 60s
            config = {
                "connection_initialization_timeout_secs": 60,
                "timeout_secs": 30,
                "reconnect_time": 5,
            }

            self.client = PocketOptionAsync(ssid=SSID, config=config)

            log.info("⏳ Waiting for session to establish (15s)...")
            await asyncio.sleep(15)

            self.connected = True
            log.info("✅ Connected")
            log.info("✅ Session ready")
            return True

        except ImportError:
            log.error("❌ BinaryOptionsToolsV2 not installed. Run: pip install binaryoptionstoolsv2")
            return False
        except Exception as exc:
            log.error(f"❌ Connection failed: {exc}")
            self.connected = False
            return False

    async def disconnect(self) -> None:
        self.connected = False
        log.info("🔌 Disconnected")

    # ─── BALANCE ──────────────────────────────────────────────────────────────

    async def get_balance(self) -> float:
        if not self.connected or self.client is None:
            return self._balance or 0.0
        try:
            val = await self.client.balance()
            self._balance = float(val)
            return self._balance
        except Exception as exc:
            log.debug(f"Balance fetch skipped: {exc}")
            return self._balance or 0.0

    # ─── CANDLES ──────────────────────────────────────────────────────────────

    async def get_candles_2m(self, pair: str) -> List[Dict]:
        return await self._fetch_candles(pair, TF_2M)

    async def get_candles_1m(self, pair: str) -> List[Dict]:
        return await self._fetch_candles(pair, TF_1M)

    async def get_all_timeframes(self, pair: str) -> Dict[str, List[Dict]]:
        results = await asyncio.gather(
            self.get_candles_2m(pair),
            self.get_candles_1m(pair),
            return_exceptions=True,
        )
        candles_2m = results[0] if not isinstance(results[0], Exception) else []
        candles_1m = results[1] if not isinstance(results[1], Exception) else []
        return {"2M": candles_2m, "1M": candles_1m}

    async def _fetch_candles(self, pair: str, tf_sec: int) -> List[Dict]:
        if not self.connected or self.client is None:
            return []
        try:
            raw = await asyncio.wait_for(
                self.client.get_candles(pair, tf_sec, CANDLE_COUNT),
                timeout=15
            )
            if not raw:
                return []
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
        direction: str,
        amount:    float,
        expiry:    int,
    ) -> Optional[str]:
        if not self.connected or self.client is None:
            log.error("❌ Cannot place trade — not connected")
            return None

        action = "call" if direction == "BUY" else "put"
        try:
            result = await asyncio.wait_for(
                self.client.buy(amount, pair, action, expiry),
                timeout=10
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

    async def check_trade_result(self, trade_id: str) -> Optional[Dict[str, Any]]:
        if not self.connected or self.client is None:
            return None
        try:
            raw = await asyncio.wait_for(
                self.client.check_win(trade_id),
                timeout=10
            )
            if raw is None:
                return None
            if isinstance(raw, dict):
                return {
                    "result":  raw.get("result",  "unknown"),
                    "profit":  float(raw.get("profit", 0)),
                    "balance": float(raw.get("balance", 0)),
                }
            profit = float(raw)
            return {
                "result":  "win" if profit > 0 else "lose",
                "profit":  profit,
                "balance": await self.get_balance(),
            }
        except Exception as exc:
            log.debug(f"Result check {trade_id}: {exc}")
            return None