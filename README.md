# AutoTrader — NSE Intraday Trading System

Automated intraday trading system for NSE via Angel One SmartAPI.

## Features
- **AI stock scorer**: Ranks Nifty 200 stocks daily using RSI, MACD, volume surge, price momentum, moving averages
- **Auto entry**: Buys top-scoring stocks at market open (9:20 AM IST)
- **Risk management**:
  - 2% hard stop loss from entry
  - 4.5% profit target
  - **Trailing stop loss**: SL moves up as price rises, locks at entry once profitable
- **Auto square-off**: Closes all positions at 3:10 PM IST
- **Live dashboard**: Real-time P&L, position tracker, trade log, daily performance chart

---

## Setup

### 1. Angel One SmartAPI credentials

1. Open Angel One account → [Smart API](https://smartapi.angelbroking.com/)
2. Create an app → get your **API Key**
3. Note your **Client ID** (your Angel One login ID) and **Password**
4. Enable TOTP in Angel One app → get your **TOTP Secret** (shown when setting up 2FA)

### 2. Configure environment

```bash
cd backend
cp .env.example .env
# Edit .env with your credentials
```

Key settings in `.env`:
```
ANGEL_API_KEY=your_api_key
ANGEL_CLIENT_ID=your_client_id
ANGEL_PASSWORD=your_password
ANGEL_TOTP_SECRET=your_totp_secret_base32

TRADING_CAPITAL=50000       # INR you want to allocate
MAX_POSITIONS=5             # Max concurrent trades
STOP_LOSS_PCT=0.02          # 2%
TARGET_PCT=0.045            # 4.5%
TRAILING_SL_PCT=0.02        # 2% trailing
```

### 3. Run locally (development)

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
# Open http://localhost:5173
```

### 4. Run with Docker

```bash
cp backend/.env.example backend/.env
# Edit backend/.env with credentials
docker-compose up --build
# Dashboard: http://localhost:5173
# API:       http://localhost:8000/docs
```

---

## How it works

### Daily flow
| Time (IST) | Action |
|---|---|
| 9:05 AM | Score all 50 watchlist stocks (technical indicators) |
| 9:20 AM | Engine starts, buys top 5 scoring candidates |
| 9:20 AM → 3:10 PM | Monitor every 5 sec — exit on SL / target / trailing SL |
| 3:10 PM | Square off any remaining positions |
| 3:35 PM | Engine stops |

### Trailing stop loss
```
Entry:    ₹100    → SL = ₹98    (2% below entry)
Price hits ₹103   → SL moves to ₹100.94 (2% below ₹103), never below entry
Price hits ₹105   → SL moves to ₹102.90
Price drops to ₹102.90 → EXIT (trailing SL triggered, profit locked)
Price hits ₹104.5 (target) → EXIT (profit target hit)
```

### Stock scoring (0-100)
| Factor | Max points | Signal |
|---|---|---|
| RSI (45-60 zone) | 20 | Bullish momentum, not overbought |
| MACD histogram | 25 | Bullish crossover / acceleration |
| Volume ratio | 20 | Unusual volume = institutional interest |
| Price momentum | 20 | 1D and 5D positive momentum |
| MA trend (price > MA20 > MA50) | 15 | Strong uptrend |

---

## API Endpoints

| Endpoint | Description |
|---|---|
| `GET /api/status` | Portfolio summary, P&L, engine status |
| `GET /api/positions` | Open positions |
| `DELETE /api/positions/{id}` | Manually close a position |
| `GET /api/trades` | Full trade history |
| `GET /api/scores/today` | Today's stock scores |
| `POST /api/scores/refresh` | Trigger re-scoring manually |
| `POST /api/engine/start` | Start trading engine |
| `POST /api/engine/stop` | Stop engine |
| `POST /api/engine/squareoff` | Force close all positions |
| `GET /api/settings` | Current settings |
| `PATCH /api/settings` | Update trading parameters live |
| `WS /api/ws` | Live position/P&L feed (WebSocket) |

Full Swagger docs: `http://localhost:8000/docs`

---

## Adding US market (Phase 2)

When you open an IBKR account:
1. Install `ib_insync` → `pip install ib_insync`
2. Add `backend/app/broker/ibkr.py` (same interface as `angel_one.py`)
3. Add US watchlist to `data/fetcher.py`
4. The scheduler, order engine, and risk manager work unchanged

---

## Disclaimer

This software is for educational purposes. Trading involves significant financial risk.
Always test with small capital first. Past performance of any strategy does not guarantee future results.
