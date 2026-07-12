# QuantView — Offline Trading Platform

A full-stack offline trading platform with real-time stock data visualization,
technical analysis indicators, and financial metrics — all running locally.

## Architecture

```text
offline-trading-platform/
├── backend/                    # FastAPI Python backend
│   ├── app/
│   │   ├── api/v1/            # REST API endpoints
│   │   │   ├── health.py      # Health check
│   │   │   └── stock.py       # Stock data (search, kline, finance)
│   │   ├── core/
│   │   │   └── config.py      # App settings & environment config
│   │   ├── schemas/           # Pydantic models
│   │   │   ├── common.py      # ApiResponse, ApiError
│   │   │   └── market.py      # KLineBar, FinancialIndicators, etc.
│   │   ├── services/
│   │   │   └── stock_service.py  # Data fetching (yfinance, akshare)
│   │   └── main.py            # FastAPI app factory
│   └── requirements.txt
├── frontend/                   # Vue 3 + TypeScript + Vite
│   ├── src/
│   │   ├── api/               # HTTP client (axios)
│   │   ├── assets/            # Styles (SCSS tokens)
│   │   ├── components/        # Vue components
│   │   ├── composables/       # Technical indicators & formatters
│   │   ├── stores/            # Pinia stores (watchlist, theme, etc.)
│   │   ├── views/             # Dashboard, Settings
│   │   ├── router/            # Vue Router config
│   │   └── main.ts            # App entry
│   ├── index.html
│   ├── vite.config.ts
│   └── package.json
├── deploy-local.ps1            # Windows local deployment script
├── build-frontend.sh           # Frontend build script
├── setup-server.sh             # Server setup script
└── .gitignore
```

## Tech Stack

### Backend

- **FastAPI** — async Python web framework
- **Pydantic** — data validation & settings management
- **yfinance** / **akshare** — stock market data sources
- **backtrader** — backtesting engine
- **pandas** / **numpy** — data processing

### Frontend

- **Vue 3** — Composition API with `<script setup>`
- **TypeScript** — type-safe development
- **Vite** — fast dev server & build tool
- **ECharts** — interactive financial charts (candlestick, line, radar)
- **Element Plus** — UI component library
- **Pinia** — state management
- **SCSS** — design tokens & theming

## Features

- **Stock Search** — search by symbol or company name (US, HK, CN markets)
- **K-Line Charts** — candlestick & line views with multiple timeframes (1m to 10y)
- **Technical Indicators** — MA, EMA, MACD, RSI, KDJ, BOLL
- **Financial Radar** — profitability moat visualization
  (ROE, ROA, gross margin, etc.)
- **Watchlist** — track your favorite stocks
- **Dark Theme** — professional dark UI with customizable color schemes
- **Multi-language** — i18n support (Chinese / English)
- **Offline-first** — all data fetched from public APIs, no cloud dependency

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- npm or pnpm

### Backend Setup

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate    # Windows
# source .venv/bin/activate  # Linux/Mac

pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Open <http://localhost:5173> in your browser.

### Windows One-Click Deploy

```powershell
.\deploy-local.ps1
```

## API Endpoints

<!-- markdownlint-disable MD013 -->

| Method | Path                                                          | Description              |
| ------ | ------------------------------------------------------------- | ------------------------ |
| GET    | `/api/v1/health`                                              | Health check             |
| GET    | `/api/v1/stock/search?keyword={keyword}`                      | Search stock symbols     |
| GET    | `/api/v1/stock/kline?symbol={symbol}&period={period}`         | Get K-line data          |
| GET    | `/api/v1/stock/kline/batch?symbols={s1},{s2}&period={period}` | Batch K-line data        |
| GET    | `/api/v1/stock/finance?symbol={symbol}`                       | Get financial indicators |

Interactive API docs at <http://localhost:8000/docs> (development mode).

<!-- markdownlint-enable MD013 -->

## Environment Variables

### Backend (`backend/.env`)

<!-- markdownlint-disable MD013 -->

| Variable               | Default                        | Description                                          |
| ---------------------- | ------------------------------ | ---------------------------------------------------- |
| `APP_NAME`             | `Offline Trading Platform API` | Application name                                     |
| `APP_ENV`              | `development`                  | Environment (`development`, `staging`, `production`) |
| `APP_VERSION`          | `0.1.0`                        | API version                                          |
| `HOST`                 | `127.0.0.1`                    | Server host                                          |
| `PORT`                 | `8000`                         | Server port                                          |
| `DEBUG`                | `true`                         | Debug mode                                           |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:5173`        | Allowed CORS origins                                 |

### Frontend (`frontend/.env.development`)

<!-- markdownlint-disable MD013 -->

| Variable            | Default                 | Description          |
| ------------------- | ----------------------- | -------------------- |
| `VITE_API_BASE_URL` | `http://127.0.0.1:8000` | Backend API base URL |

<!-- markdownlint-enable MD013 -->

## License

MIT
