"""
config.py — Pocket Option Wilder Bot
Cross-platform: Windows & macOS
"""

from pathlib import Path

# ─── SESSION ──────────────────────────────────────────────────────────────────
SSID     = '42["auth",{"session":"2jgq2o7ql6f941redfdii6tqne","isDemo":1,"uid":100817301,"platform":2,"isFastHistory":true,"isOptimized":true}]'
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
RSI_BUY_MIN_2M  = 40.0
RSI_SELL_MAX_2M = 60.0
RSI_BUY_MIN_1M  = 40.0
RSI_SELL_MIN_1M = 60.0

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
SCAN_INTERVAL_SEC = 10

# ─── LOGGING / PATHS ──────────────────────────────────────────────────────────
BASE_DIR  = Path(__file__).parent
LOG_DIR   = BASE_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)