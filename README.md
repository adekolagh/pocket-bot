# 🤖 Pocket Option — Wilder Bot

**2-Minute / 1-Minute binary options bot for Pocket Option OTC pairs.**

---

## Strategy

| Step | Timeframe | Direction | Rules |
|------|-----------|-----------|-------|
| Lock | 2M | BUY  | RSI > 40 · Stoch K crosses D up · SAR below price |
| Lock | 2M | SELL | RSI < 60 · Stoch K crosses D down · SAR above price |
| Entry | 1M | BUY  | RSI > 40 · K crosses D up · SAR below (**must**) |
| Entry | 1M | SELL | RSI > 60 · K crosses D down · SAR above (**must**) |

- Stochastic settings: **5, 3, 3**
- Expiry: **1 minute**

---

## Quick Start — GitHub Codespaces

### Step 1 — Open in Codespaces
1. Go to your GitHub repo
2. Click green **`<> Code`** button
3. Click **`Codespaces`** tab
4. Click **`Create codespace on main`**
5. Wait ~1 minute — dependencies install automatically

### Step 2 — Set your SSID
In the Codespaces terminal:
```bash
cp .env.example .env
nano .env
```
Replace `paste_your_ssid_here` with your actual SSID from Pocket Option.

**How to get your SSID:**
1. Open PocketOption in your browser
2. Press F12 → Application → Cookies
3. Find the cookie named `ssid` → copy the value

### Step 3 — Run the bot
```bash
bash start.sh
```

---

## How to get your SSID safely

> ⚠️ Never share your SSID. Never commit it to GitHub.
> The `.env` file is in `.gitignore` — it is safe.

---

## Files

| File | Purpose |
|------|---------|
| `main.py` | Bot entry point, main loop |
| `strategy.py` | 2M lock + 1M entry logic |
| `indicators.py` | RSI, Stochastic, Parabolic SAR |
| `api_client.py` | Pocket Option WebSocket connection |
| `config.py` | All settings (pairs, amounts, timeframes) |
| `risk_manager.py` | Trade limits, session stats |
| `dashboard.py` | Live terminal display |
| `reporter.py` | Trade logging to CSV |
| `logger.py` | Logging setup |
| `start.sh` | Single command to run bot |

---

## Config

Open `config.py` to change:

```python
IS_DEMO      = True     # True = demo account, False = real money
TRADE_AMOUNT = 1.0      # USD per trade
MAX_CONCURRENT = 3      # max open trades at once
EXPIRY_SEC   = 60       # 1 minute expiry
```

---

## 10-Day Demo Testing Plan

| Day | Goal |
|-----|------|
| 1–2 | Confirm connection, candles fetching, signals firing |
| 3–5 | Watch 2M locks and 1M entries — are they logical? |
| 6–8 | Track win/loss ratio in the CSV logs |
| 9–10 | Decide if strategy needs tuning before going live |

Run **6 hours per day** — fits within GitHub free tier (60 hrs/month).

---

## Moving to VPS (after testing)

1. SSH into your VPS
2. `git clone` this repo
3. `bash start.sh`
4. Done — bot runs 24/7

---

## Requirements

- Python 3.11+
- `pocketoptionapi-async`
- `numpy`
- `colorama`

Install: `pip install -r requirements.txt`
