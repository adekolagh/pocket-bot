"""
logger.py — Logging setup
Cross-platform: Windows & macOS  (uses colorama for Windows terminal colours)
"""

import logging
import sys
from datetime import datetime
from pathlib import Path

from config import LOG_DIR


def setup_logging(level: int = logging.INFO) -> None:
    """
    Configure root logger:
      • Console  → coloured (via colorama on Windows, ANSI on macOS)
      • File     → logs/session_YYYYMMDD_HHMMSS.log (plain text)
    """
    # Initialise colorama (no-op on macOS/Linux, required on Windows)
    try:
        import colorama  # type: ignore
        colorama.init(autoreset=True)
    except ImportError:
        pass

    root = logging.getLogger()
    root.setLevel(level)
    root.handlers.clear()

    # ── Console handler ────────────────────────────────────────────────────
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(level)
    console.setFormatter(_ColourFormatter())
    root.addHandler(console)

    # ── File handler ───────────────────────────────────────────────────────
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path  = LOG_DIR / f"session_{timestamp}.log"
    file_hdlr = logging.FileHandler(log_path, encoding="utf-8")
    file_hdlr.setLevel(logging.DEBUG)
    file_hdlr.setFormatter(
        logging.Formatter(
            "%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
            datefmt="%H:%M:%S",
        )
    )
    root.addHandler(file_hdlr)

    logging.getLogger("websockets").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)


# ─── Coloured formatter ────────────────────────────────────────────────────────

_LEVEL_COLOURS = {
    "DEBUG":    "\033[90m",    # dark grey
    "INFO":     "\033[97m",    # bright white
    "WARNING":  "\033[93m",    # yellow
    "ERROR":    "\033[91m",    # red
    "CRITICAL": "\033[95m",    # magenta
}
_RESET = "\033[0m"


class _ColourFormatter(logging.Formatter):
    _FMT = "%(asctime)s  %(levelname)-8s  %(message)s"

    def format(self, record: logging.LogRecord) -> str:
        colour = _LEVEL_COLOURS.get(record.levelname, "")
        formatter = logging.Formatter(
            f"{colour}{self._FMT}{_RESET}",
            datefmt="%H:%M:%S",
        )
        return formatter.format(record)
