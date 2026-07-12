# Architecture

Project tree and component notes for reference.

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

Notes:
- Backend: FastAPI app with modular services and pydantic models. Data fetching uses yfinance/akshare; consider adding retry/caching.
- Frontend: Vue 3 + Vite; charts built with ECharts. Keep components small and stateless where possible.
- Deployment: deploy-local.ps1 for Windows developers; adapt setup-server.sh for Linux servers.
