# CTTH — Centre Technique du Textile et de l'Habillement
## AI Watch Agent Platform

**Intelligent Trade Monitoring for Morocco's Textile Sector**

---

## Project Overview

CTTH AI Watch Agent is a comprehensive full-stack web application designed for monitoring and analyzing international trade data in Morocco's textile industry. The platform provides real-time market intelligence, automated news aggregation, and AI-powered report generation.

### Core Features

- **Trade Data Analytics**: Real-time import/export data from Eurostat and UN Comtrade
- **Automated News Aggregation**: AI-powered web search using OpenAI and Google Gemini
- **AI Report Generation**: Intelligent report creation with PDF export
- **User Authentication**: JWT-based auth with role-based access control
- **Responsive Dashboard**: Modern Next.js frontend with real-time data visualization

---

## Tech Stack

### Backend
- **Framework**: FastAPI (Python 3.14)
- **Database**: MongoDB Atlas (Motor async + PyMongo sync)
- **Auth**: JWT (python-jose + bcrypt)
- **APIs**: Eurostat, UN Comtrade, Federal Register, OTEXA, OpenAI, Google Gemini
- **Port**: `5000`

### Frontend
- **Framework**: Next.js 14.2 (React 18, App Router)
- **Styling**: Tailwind CSS 3.4
- **State**: Zustand
- **Charts**: Recharts 2.13
- **HTTP**: Axios
- **Icons**: Lucide React
- **Port**: `4000`

---

## Project Structure

```
CTTH/
├── backend/                    # FastAPI application
│   ├── app/
│   │   ├── agents/            # Data collection agents
│   │   │   ├── base_agent.py      # Base agent (PyMongo)
│   │   │   ├── comtrade_agent.py  # UN Comtrade (HS 50-63)
│   │   │   ├── eurostat_agent.py  # Eurostat ext_lt_maineu
│   │   │   ├── federal_register_agent.py
│   │   │   ├── general_watcher.py # OpenAI + Gemini search
│   │   │   ├── otexa_agent.py     # OTEXA trade.gov
│   │   │   └── constants.py
│   │   ├── api/               # API routes
│   │   │   ├── auth.py            # Register / Login / Me
│   │   │   ├── dashboard.py       # KPIs, trends, partners
│   │   │   ├── trade.py           # Trade data + aggregation
│   │   │   ├── news.py            # News articles + refresh
│   │   │   ├── reports.py         # Report CRUD + generation
│   │   │   ├── settings_routes.py # Data sources + API keys
│   │   │   ├── health.py          # Health check
│   │   │   └── deps.py            # Auth dependency
│   │   ├── models/            # MongoDB collection constants
│   │   ├── schemas/           # Pydantic schemas
│   │   ├── services/          # Business logic
│   │   │   ├── trade_service.py   # MongoDB aggregation queries
│   │   │   ├── news_service.py    # Text search with $regex
│   │   │   └── report_service.py  # GPT-4 report generation
│   │   ├── templates/         # Jinja2 HTML templates
│   │   ├── tasks/             # Background task stubs
│   │   ├── config.py          # Pydantic Settings
│   │   ├── database.py        # Motor + PyMongo connections
│   │   └── main.py            # FastAPI app entry point
│   ├── venv/                  # Python virtual environment
│   └── requirements.txt       # Python dependencies
│
├── frontend/                   # Next.js application
│   ├── src/
│   │   ├── app/               # App Router pages
│   │   │   ├── page.tsx           # Dashboard (/)
│   │   │   ├── login/page.tsx     # Login
│   │   │   ├── trade/page.tsx     # Trade analytics
│   │   │   ├── news/page.tsx      # News feed
│   │   │   ├── reports/page.tsx   # Reports
│   │   │   └── settings/page.tsx  # Settings
│   │   ├── components/        # Reusable UI components
│   │   ├── lib/               # API client, store, utils
│   │   └── types/             # TypeScript definitions
│   ├── package.json
│   └── next.config.js
│
├── scripts/                    # Utility scripts
│   ├── seed_data.py           # Create admin user + data sources
│   └── manual_fetch.py        # Trigger agents manually
├── .env                       # Environment variables
└── README.md
```

---

## Getting Started

### Prerequisites
- Python 3.11+ (tested with 3.14)
- Node.js 18+
- MongoDB Atlas account (free tier works)
- API keys: OpenAI, Google Gemini, UN Comtrade (optional)

### 1. Clone & Environment

```bash
git clone <repo-url>
cd CTTH
```

Create a `.env` file at the project root with your credentials:
```env
MONGODB_URL=mongodb+srv://<user>:<password>@<cluster>.mongodb.net/<db>?retryWrites=true&w=majority
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=1440

OPENAI_API_KEY=sk-...
GEMINI_API_KEY=AI...
COMTRADE_PRIMARY_KEY=...
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Seed the Database

```bash
# From the backend/ directory (with venv activated)
python ../scripts/seed_data.py
```

This creates:
- Admin user: `admin@ctth.ma` / `admin123`
- Data source status entries for all 5 agents

### 4. Start the Backend

```bash
# From the backend/ directory
uvicorn app.main:app --port 5000 --host 0.0.0.0
```

Verify: open http://localhost:5000/api/health — should return `{"status":"healthy","db":"ok"}`

### 5. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev -- --port 4000
```

### 6. Open the App

Open **http://localhost:4000** in your browser.

Login credentials:
- **Email**: `admin@ctth.ma`
- **Password**: `admin123`

---

## Ports Summary

| Service   | Port   | URL                           |
|-----------|--------|-------------------------------|
| Backend   | `5000` | http://localhost:5000          |
| Frontend  | `4000` | http://localhost:4000          |
| API Docs  | `5000` | http://localhost:5000/docs     |
| Health    | `5000` | http://localhost:5000/api/health |

---

## API Endpoints

```
Auth:
  POST   /api/auth/register             Register new user
  POST   /api/auth/login                Login (returns JWT)
  GET    /api/auth/me                   Current user info

Dashboard:
  GET    /api/dashboard                 KPIs, trends, partners, news

Trade:
  GET    /api/trade/data                Paginated trade data
  GET    /api/trade/aggregated          Grouped aggregations
  GET    /api/trade/top-partners        Top trading partners
  GET    /api/trade/hs-breakdown        HS chapter breakdown

News:
  GET    /api/news                      Paginated news articles
  GET    /api/news/{id}                 Single article
  POST   /api/news/refresh              Trigger agent fetch

Reports:
  GET    /api/reports                   List user reports
  POST   /api/reports                   Create new report
  GET    /api/reports/{id}              Get report details
  GET    /api/reports/{id}/status       Check generation status

Settings:
  GET    /api/settings/data-sources     Data source status
  POST   /api/settings/data-sources/{name}/refresh   Trigger agent
  GET    /api/settings/api-keys         API key status (masked)

Health:
  GET    /api/health                    DB connectivity check
```

---

## Data Sources & Agents

| Agent               | Source              | Data                        |
|---------------------|---------------------|-----------------------------|
| `EurostatAgent`     | Eurostat API        | EU-Morocco trade (SITC, EUR)|
| `ComtradeAgent`     | UN Comtrade API     | World trade (HS 50-63, USD) |
| `FederalRegisterAgent` | Federal Register | US textile regulations      |
| `GeneralWatcher`    | OpenAI + Gemini     | AI web search news          |
| `OtexaAgent`        | OTEXA (trade.gov)   | US textile import data      |

### Manual Data Fetch

```bash
# From the backend/ directory (with venv activated)
python ../scripts/manual_fetch.py --agent eurostat
python ../scripts/manual_fetch.py --agent comtrade
python ../scripts/manual_fetch.py --agent federal_register
python ../scripts/manual_fetch.py --agent general_watcher
python ../scripts/manual_fetch.py --agent otexa
python ../scripts/manual_fetch.py --agent all
```

---

## Key Features

### 1. Dashboard (`/`)
- 4 KPI cards (exports, imports, balance, news count)
- Export/Import trend chart (annual)
- Top 5 trading partners bar chart
- HS chapter breakdown
- Recent news feed

### 2. Trade Analytics (`/trade`)
- Flow filter (imports/exports/all)
- HS chapter multi-select dropdown (chapters 50-63)
- Paginated data table with 454+ records
- Top partners and HS breakdown charts

### 3. News & Intelligence (`/news`)
- Multi-source aggregation (5 agents)
- Category filtering and text search
- 108+ articles from regulatory, market, and industry sources

### 4. Report Generation (`/reports`)
- AI-generated trade reports (GPT-4)
- Report types: weekly summary, market analysis, regulatory alerts
- All statistics from database queries (LLM never generates numbers)

### 5. Settings (`/settings`)
- Data source health monitoring
- Manual agent refresh triggers
- API key status display

---

## Design System

### CTTH Color Palette
- **Primary**: Tropical Teal (`#58B9AF`)
- **Surface**: Gunmetal (`#353A3A`)
- **Accent**: Frozen Water (`#C1DEDB`)
- **Background**: White (`#FFFFFF`)

### UI Patterns
- Glass morphism cards with subtle borders
- Smooth gradient backgrounds
- Responsive layouts (mobile to desktop)
- Animated transitions and loading states

---

## Environment Variables Reference

| Variable               | Required | Description                         |
|------------------------|----------|-------------------------------------|
| `MONGODB_URL`          | Yes      | MongoDB Atlas connection string     |
| `JWT_SECRET_KEY`       | Yes      | Secret for JWT token signing        |
| `JWT_ALGORITHM`        | No       | Default: `HS256`                    |
| `JWT_EXPIRATION_MINUTES` | No     | Default: `1440` (24 hours)          |
| `OPENAI_API_KEY`       | No       | For AI search + report generation   |
| `GEMINI_API_KEY`       | No       | For Google Gemini web search        |
| `COMTRADE_PRIMARY_KEY` | No       | For UN Comtrade API access          |

---

## Troubleshooting

### Backend won't start
- Check that `.env` exists with a valid `MONGODB_URL`
- Ensure the virtual environment is activated
- Run `pip install -r requirements.txt` again

### Frontend shows loading spinner forever
- Verify the backend is running on port `5000`
- Check `frontend/src/lib/api.ts` has `baseURL` set to `http://localhost:5000`
- Open browser DevTools Network tab to check for CORS or 401 errors
- Clear `localStorage` in browser console: `localStorage.clear()`

### Login fails
- Run `python ../scripts/seed_data.py` to create the admin user
- Check backend logs for error messages

### CORS errors
- Ensure `backend/app/main.py` has `http://localhost:4000` in `allow_origins`
- Restart the backend after any changes to `main.py`

---

## License

Internal project for CTTH (Centre Technique du Textile et de l'Habillement).

Built by **Mounsef Litniti** — GenAI Consultant at AI Crafters.
