"""
config.py — Pocket Option Wilder Bot
Cross-platform: Windows & macOS
"""

import os
from pathlib import Path

# ─── SESSION ──────────────────────────────────────────────────────────────────
SSID     = os.getenv("PO_SSID", "YOUR_SSID_HERE")   # set env var or paste here
IS_DEMO  = True                                       # True = demo, False = real

# ─── TIMEFRAMES (seconds) ─────────────────────────────────────────────────────
TF_2M = 120
TF_1M = 60

# ─── CANDLES ──────────────────────────────────────────────────────────────────
CANDLE_COUNT = 60          # candles fetched per request

# ─── TRADE ────────────────────────────────────────────────────────────────────
TRADE_AMOUNT   = 1.0       # USD per trade
EXPIRY_SEC     = 60        # 1-minute expiry (countdown = 1M candle)
MAX_CONCURRENT = 3         # max open trades at once

# ─── INDICATOR SETTINGS ───────────────────────────────────────────────────────
RSI_PERIOD   = 14
STOCH_K      = 5
STOCH_D      = 3
STOCH_SMOOTH = 3            # smoothing on %K before %D

# ─── STRATEGY THRESHOLDS ──────────────────────────────────────────────────────
# 2M  BUY  lock  : RSI > 40,  K crosses D up,   SAR below price
# 2M  SELL lock  : RSI < 60,  K crosses D down, SAR above price
# 1M  BUY  entry : RSI > 40,  K crosses D up,   SAR below  (MUST)
# 1M  SELL entry : RSI > 60,  K crosses D down, SAR above  (MUST)
RSI_BUY_MIN_2M  = 40.0
RSI_SELL_MAX_2M = 60.0
RSI_BUY_MIN_1M  = 40.0
RSI_SELL_MIN_1M = 60.0      # sell on 1M needs RSI *above* 60

# ─── PAIRS ────────────────────────────────────────────────────────────────────
PAIRS = [
    "EURUSD_otc", "GBPUSD_otc", "USDJPY_otc",
    "AUDUSD_otc", "USDCAD_otc", "USDCHF_otc",
    "EURGBP_otc", "EURJPY_otc", "GBPJPY_otc",
    "NZDUSD_otc", "EURNZD_otc", "EURCAD_otc",
    "EURAUD_otc", "GBPAUD_otc", "GBPCAD_otc",
    "AUDCAD_otc", "AUDCHF_otc", "AUDNZD_otc",
    "CADJPY_otc", "CHFJPY_otc", "NZDCAD_otc",
    "NZDCHF_otc", "NZDJPY_otc", "GBPCHF_otc",
    "GBPNZD_otc", "EURUSD",     "GBPUSD",
]

# ─── SCAN INTERVAL ────────────────────────────────────────────────────────────
SCAN_INTERVAL_SEC = 10      # seconds between full pair scans

# ─── LOGGING / PATHS ──────────────────────────────────────────────────────────
BASE_DIR  = Path(__file__).parent
LOG_DIR   = BASE_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
