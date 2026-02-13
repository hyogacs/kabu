# Kabu - Stock Monitoring AI App

Real-time stock monitoring application with AI-powered analysis for **US** and **Japanese** markets.

## Features

- **Real-time Monitoring**: WebSocket-based live price streaming for US (NYSE/NASDAQ) and JP (TSE) stocks
- **AI Analysis Engine**: Multi-factor scoring model generating buy/sell/hold signals with confidence levels
- **Technical Indicators**: RSI, MACD, Bollinger Bands, SMA/EMA, Stochastic, ATR, OBV
- **5 Trading Strategies**:
  - **Trend Following** - MA alignment and crossover signals
  - **Mean Reversion** - Bollinger Band / RSI extremes
  - **Momentum** - MACD + rate-of-change based entries
  - **Breakout** - Support/resistance level breaks
  - **Swing Trade** - Multi-indicator composite scoring
- **Interactive Charts**: Candlestick charts with TradingView's lightweight-charts
- **Risk Management**: Stop-loss, take-profit, position sizing recommendations

## Architecture

```
kabu/
├── backend/                    # Python FastAPI server
│   ├── app/
│   │   ├── api/                # REST + WebSocket endpoints
│   │   ├── core/               # Configuration
│   │   ├── models/             # Pydantic data models
│   │   ├── services/           # Stock data + AI analysis
│   │   └── strategies/         # Trading strategy engine
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                   # React + TypeScript + Vite
│   ├── src/
│   │   ├── components/         # UI components
│   │   ├── hooks/              # WebSocket hook
│   │   ├── services/           # API client
│   │   ├── styles/             # CSS
│   │   └── utils/              # Formatters
│   ├── Dockerfile
│   └── package.json
└── docker-compose.yml
```

## Quick Start

### Local Development

**Backend:**

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev
```

### Docker

```bash
docker compose up --build
```

Visit `http://localhost` (frontend) or `http://localhost:8000/docs` (API docs).

## API Endpoints

| Endpoint | Description |
|---|---|
| `GET /api/stocks` | List stocks (filter by market: US/JP) |
| `GET /api/stocks/{symbol}` | Single stock quote |
| `GET /api/stocks/{symbol}/detail` | Full detail with analysis + strategies |
| `GET /api/stocks/{symbol}/history` | Historical OHLCV data |
| `GET /api/analysis/{symbol}` | AI buy/sell analysis |
| `GET /api/strategies/{symbol}` | Trading strategies |
| `WS /ws/stocks` | Real-time quote streaming |

## Default Watchlist

**US Stocks:** AAPL, GOOGL, MSFT, AMZN, NVDA, TSLA, META, JPM, V, WMT

**JP Stocks:** Toyota (7203.T), Sony (6758.T), SoftBank (9984.T), Keyence (6861.T), Nintendo (7974.T), MUFG (8306.T), KDDI (9433.T), Hitachi (6501.T), Shin-Etsu (4063.T), Denso (6902.T)

## AI Signal Levels

| Signal | Score Range | Meaning |
|---|---|---|
| STRONG_BUY | >= 0.50 | Multiple strong bullish factors aligned |
| BUY | >= 0.20 | Bullish bias with moderate conviction |
| HOLD | -0.20 ~ 0.20 | Mixed or neutral signals |
| SELL | <= -0.20 | Bearish bias with moderate conviction |
| STRONG_SELL | <= -0.50 | Multiple strong bearish factors aligned |

## Disclaimer

This application is for educational and informational purposes only. It does not constitute financial advice. Always do your own research before making investment decisions.
