# CTTH — Centre Technique du Textile et de l'Habillement
## AI Watch Agent Platform

**Intelligent Trade Monitoring for Morocco's Textile Sector**

---

## Project Overview

CTTH AI Watch Agent is a comprehensive full-stack web application designed for monitoring and analyzing international trade data in Morocco's textile industry. The platform automatically aggregates global trade data, sector news and market research — then generates analytical reports in French using AI (GPT-4 / Gemini).

### Core Features

- **Trade Data Analytics**: Real-time import/export data from Eurostat and UN Comtrade, with compound MongoDB indexes for fast aggregation
- **Automated News Aggregation**: AI-powered web search using OpenAI GPT-4o and Google Gemini; articles deduplicated by `source_url`
- **AI Report Generation**: Intelligent report creation with PDF export and email delivery (primary + fallback mail APIs)
- **Market Research**: 5-tab market analysis — overview, segmentation, companies, Porter/PESTEL/TAM frameworks, competitive events
- **Daily Pipeline Scheduler**: APScheduler runs agents in parallel phases every night at 02:00 UTC
- **User Authentication**: JWT-based auth with role-based access control
- **Responsive Dashboard**: Modern Next.js 14 frontend with lazy-loaded Recharts visualizations and client-side TTL caching

---

## Tech Stack

### Backend
- **Framework**: FastAPI 0.115+ (Python 3.12)
- **Database**: MongoDB Atlas (Motor 3.6+ async for routes · PyMongo 4.9+ sync for agents)
- **Auth**: JWT — python-jose + bcrypt
- **AI**: OpenAI 1.51+ (GPT-4o · gpt-4o-search-preview) · google-generativeai 0.8+ (Gemini)
- **Scheduler**: APScheduler 3.10+ (AsyncIOScheduler)
- **HTTP Client**: httpx 0.27+ (async) for agents
- **Templating**: Jinja2 3.1+ for report HTML
- **Port**: `5000` (dev) / `8000` (Docker)

### Frontend
- **Framework**: Next.js 14.2 (React 18, App Router)
- **Language**: TypeScript 5.6
- **Styling**: Tailwind CSS 3.4
- **State**: Zustand 5.0
- **Charts**: Recharts 2.13 (lazy-loaded with `next/dynamic`)
- **HTTP**: Axios 1.7 with in-memory TTL cache
- **Icons**: Lucide React 0.453 (tree-shaken)
- **Port**: `4000`

---

## Project Structure

```
CTTH/
├── backend/                     # FastAPI application
│   ├── app/
│   │   ├── main.py              # FastAPI entry point + lifespan (indexes, scheduler)
│   │   ├── config.py            # Pydantic Settings — reads from .env
│   │   ├── database.py          # Motor (async) + PyMongo (sync) clients + indexes
│   │   ├── agents/              # Data collection agents
│   │   │   ├── base_agent.py        # Abstract base (safe_request, retry, status)
│   │   │   ├── eurostat_agent.py    # Eurostat ext_lt_maineu (EU-Morocco)
│   │   │   ├── comtrade_agent.py    # UN Comtrade HS 50-63
│   │   │   ├── federal_register_agent.py  # US textile regulations
│   │   │   ├── otexa_agent.py       # OTEXA trade.gov data
│   │   │   ├── general_watcher.py   # GPT-4o + Gemini web search
│   │   │   └── constants.py
│   │   ├── api/                 # FastAPI routers
│   │   │   ├── auth.py              # Register / Login / Me
│   │   │   ├── dashboard.py         # KPIs, trends, partners (5-min cache)
│   │   │   ├── trade.py             # Paginated trade data + aggregations
│   │   │   ├── news.py              # News articles + refresh
│   │   │   ├── reports.py           # Report CRUD + PDF generation + email
│   │   │   ├── market_research.py   # Market analysis + frameworks
│   │   │   ├── settings_routes.py   # Data sources + API keys
│   │   │   ├── scheduler_routes.py  # Scheduler status + run history
│   │   │   ├── health.py            # Health check
│   │   │   └── deps.py              # Auth dependency injection
│   │   ├── scheduler/           # APScheduler pipeline
│   │   │   ├── core.py              # AsyncIOScheduler setup
│   │   │   ├── pipeline.py          # Daily orchestrator (parallel phases)
│   │   │   └── jobs.py              # Individual job functions
│   │   ├── services/            # Business logic
│   │   │   ├── trade_service.py
│   │   │   ├── news_service.py
│   │   │   ├── report_service.py
│   │   │   ├── market_research_service.py  # asyncio.gather + TTL cache
│   │   │   └── pdf_service.py
│   │   ├── schemas/             # Pydantic schemas (request / response)
│   │   └── templates/           # Jinja2 HTML templates for reports
│   ├── requirements.txt
│   └── Dockerfile               # python:3.12-slim
│
├── frontend/                    # Next.js 14 App Router
│   ├── src/
│   │   ├── app/                 # Pages
│   │   │   ├── page.tsx             # Dashboard (/)
│   │   │   ├── trade/page.tsx       # Trade analytics
│   │   │   ├── news/page.tsx        # News feed
│   │   │   ├── reports/page.tsx     # Reports (polling + memory-leak-safe)
│   │   │   ├── market-research/page.tsx  # Market research (5 tabs)
│   │   │   ├── settings/page.tsx    # Settings
│   │   │   └── login/page.tsx       # Authentication
│   │   ├── components/
│   │   │   ├── charts/              # AreaTrendChart, BarChartWidget, PieChartWidget
│   │   │   ├── layout/              # Sidebar, navigation
│   │   │   └── ui/                  # Card, Badge, LoadingSpinner, Pagination
│   │   ├── lib/
│   │   │   ├── api.ts               # Axios client + in-memory TTL cache
│   │   │   └── store.ts             # Zustand auth store
│   │   └── types/                   # TypeScript interfaces
│   ├── next.config.js           # compress, splitChunks, cache headers
│   └── Dockerfile
│
├── scripts/
│   ├── seed_data.py             # Create admin user + data source entries
│   └── manual_fetch.py          # Trigger any agent manually
├── docker-compose.yml
├── .env                         # Environment variables (create this)
└── README.md
```

---

## Getting Started

### Prerequisites

| Tool | Version |
|------|---------|
| Docker + Docker Compose | 24+ |
| **— or manually —** | |
| Python | 3.12+ |
| Node.js | 20+ |
| npm | 10+ |
| MongoDB | Atlas (free tier) or 6.0+ local |

---

### Quick Start (Docker)

```bash
# 1. Clone
git clone <repo-url>
cd CTTH

# 2. Create .env (see Environment Variables section below)

# 3. Start
docker-compose up --build

# Backend  → http://localhost:8000
# Frontend → http://localhost:3000
# Swagger  → http://localhost:8000/docs
```

---

### Manual Setup

#### 1. Environment File

Create `.env` at the project root (see full reference in [Environment Variables](#environment-variables)):

```env
MONGODB_URL=mongodb+srv://<user>:<pass>@cluster.mongodb.net/?retryWrites=true
JWT_SECRET_KEY=your-very-long-random-secret
OPENAI_API_KEY=sk-...
```

#### 2. Backend

```bash
cd backend

# Create and activate virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Seed database (creates admin user + data source entries)
python ../scripts/seed_data.py

# Start dev server
uvicorn app.main:app --port 5000 --host 0.0.0.0 --reload
```

Verify: `GET http://localhost:5000/api/health` → `{"status":"healthy","db":"ok"}`

#### 3. Frontend

```bash
cd frontend

npm install

# Development
npm run dev -- --port 4000

# Production build
npm run build && npm start
```

#### 4. Open the App

Navigate to **http://localhost:4000**

Default credentials (created by `seed_data.py`):
- **Email**: `admin@ctth.ma`
- **Password**: `admin123`

---

## Ports Summary

| Service | Port (dev) | Port (Docker) | URL |
|---------|-----------|--------------|-----|
| Backend | `5000` | `8000` | http://localhost:5000 |
| Frontend | `4000` | `3000` | http://localhost:4000 |
| API Docs | `5000` | `8000` | http://localhost:5000/docs |
| Health | `5000` | `8000` | http://localhost:5000/api/health |

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `MONGODB_URL` | ✅ | — | MongoDB connection string |
| `JWT_SECRET_KEY` | ✅ | — | Secret for JWT signing |
| `JWT_ALGORITHM` | | `HS256` | JWT algorithm |
| `JWT_EXPIRATION_MINUTES` | | `1440` | Token TTL (24 hours) |
| `OPENAI_API_KEY` | Recommended | `""` | GPT-4 for reports & web search |
| `GEMINI_API_KEY` | Recommended | `""` | Google Gemini web search |
| `COMTRADE_PRIMARY_KEY` | | `""` | UN Comtrade API (~500 req/day) |
| `COMTRADE_SECONDARY_KEY` | | `""` | Fallback Comtrade key |
| `APP_LANGUAGE` | | `fr` | Response language for AI |
| `LOG_LEVEL` | | `INFO` | DEBUG / INFO / WARNING / ERROR |
| `SCHEDULER_ENABLED` | | `true` | Enable daily pipeline |
| `SCHEDULER_DAILY_HOUR` | | `2` | Daily run hour (UTC) |
| `SCHEDULER_DAILY_MINUTE` | | `0` | Daily run minute |
| `MAIL_API_URL` | | `https://aic-mail-server.vercel.app/api/send-email` | Primary email API |
| `MAIL_API_FALLBACK_URL` | | `https://mail-api-mounsef.vercel.app/api/send-email` | Fallback email API |
| `EUROSTAT_COMEXT_BASE_URL` | | `https://ec.europa.eu/eurostat/api/comext/dissemination` | Eurostat API base |
| `COMTRADE_BASE_URL` | | `https://comtradeapi.un.org/data/v1/get` | UN Comtrade API base |
| `FEDERAL_REGISTER_BASE_URL` | | `https://www.federalregister.gov/api/v1` | Federal Register base |

---

## API Endpoints

> Full interactive documentation: **`http://localhost:5000/docs`** (Swagger UI)

### Authentication — `/api/auth`
```
POST  /api/auth/register          Create account
POST  /api/auth/login             Login → returns JWT
GET   /api/auth/me                Current user info
```

### Dashboard — `/api/dashboard`
```
GET   /api/dashboard              KPIs, trend chart, top partners, recent news
                                  (5-minute in-memory cache)
```

### Trade Data — `/api/trade`
```
GET   /api/trade/data             Paginated rows (filters: flow, hs_code, partner, year)
GET   /api/trade/aggregated       Grouped aggregations by period + HS chapter
GET   /api/trade/top-partners     Top trading partners by total value
GET   /api/trade/hs-breakdown     Value breakdown by HS chapter
```

### News — `/api/news`
```
GET   /api/news                   Paginated articles (filters: category, search, source)
GET   /api/news/{id}              Single article detail
POST  /api/news/refresh           Trigger GeneralWatcher agent
```

### Reports — `/api/reports`
```
GET   /api/reports                List current user's reports
POST  /api/reports                Create + generate a report (async background task)
GET   /api/reports/{id}           Report detail + full content
GET   /api/reports/{id}/status    Generation status (pending/generating/completed/failed)
GET   /api/reports/{id}/download  Download PDF
POST  /api/reports/{id}/send-email  Send report by email
                                    Body: {"extra_emails": ["user@example.com"]}
```

### Market Research — `/api/market-research`
```
GET   /api/market-research/overview          Market summary (5-min cache)
GET   /api/market-research/market-size-series  Market size time series
GET   /api/market-research/market-share      Company market shares
GET   /api/market-research/segments          Market segments by axis
GET   /api/market-research/companies         Company list + financials
GET   /api/market-research/insights          AI-generated insights
GET   /api/market-research/competitive-events  M&A, partnerships, expansions
POST  /api/market-research/framework         Generate AI framework
                                              Body: {"framework_type": "porter"|"pestel"|"tam_sam_som"}
```

### Scheduler — `/api/scheduler`
```
GET   /api/scheduler/status       Active jobs and next run times
GET   /api/scheduler/runs         Pipeline execution history (paginated)
GET   /api/scheduler/runs/{id}    Single run detail with per-phase stats
```

### Settings — `/api/settings`
```
GET   /api/settings/data-sources            Agent health + last fetch info
POST  /api/settings/data-sources/{name}/refresh  Trigger agent manually
GET   /api/settings/api-keys                API key configuration status
```

### Health
```
GET   /api/health                 MongoDB ping → {"status":"healthy","db":"ok"}
```

---

## Data Sources & Agents

| Agent | Source | Data | Auth |
|-------|--------|------|------|
| `EurostatAgent` | `ec.europa.eu/eurostat` | EU-Morocco bilateral trade, annual series (SITC) | None (public) |
| `ComtradeAgent` | `comtradeapi.un.org` | World textile trade HS 50-63 by partner + HS code | API key (~500 req/day) |
| `FederalRegisterAgent` | `federalregister.gov` | US textile regulations, tariff notices | None (public API) |
| `OtexaAgent` | `trade.gov/otexa` | US textile import data, quotas | None (public) |
| `GeneralWatcher` | GPT-4o-search-preview + Gemini | Latest news, trends, regulatory changes | OpenAI + Gemini keys |

All agents inherit from `BaseAgent` which provides:
- `safe_request()` — HTTP with exponential retry (3 attempts)
- `update_status()` — writes to `data_source_status` collection
- `increment_api_calls()` — daily call counter (prevents quota overrun)

### Manual Agent Trigger

```bash
# From backend/ with venv activated:
python ../scripts/manual_fetch.py --agent eurostat
python ../scripts/manual_fetch.py --agent comtrade
python ../scripts/manual_fetch.py --agent federal_register
python ../scripts/manual_fetch.py --agent general_watcher
python ../scripts/manual_fetch.py --agent otexa
python ../scripts/manual_fetch.py --agent all
```

Or via API: `POST /api/settings/data-sources/{agent_name}/refresh`

---

## Daily Pipeline Scheduler

APScheduler runs inside the FastAPI process (AsyncIOScheduler). Default: **02:00 UTC daily**.

```
Phase 1 — Trade data  (parallel, ThreadPoolExecutor ×4)
  ├── job_fetch_eurostat()
  ├── job_fetch_comtrade()
  ├── job_fetch_federal_register()
  └── job_fetch_otexa()

Phase 2 — News
  └── job_fetch_news()            ← GeneralWatcher (GPT-4o + Gemini)

Phase 3 — Market research
  ├── job_fetch_market_research()
  └── job_generate_frameworks()   ← Porter, PESTEL, TAM·SAM·SOM

Phase 4 — Maintenance
  └── job_reset_daily_counters()
```

Each pipeline run is saved in `scheduler_runs` with status, timestamps, and per-phase counters.

---

## Frontend Pages

| Page | Route | Description |
|------|-------|-------------|
| Dashboard | `/` | 4 KPI cards, export/import trend chart, top-5 partners, HS breakdown, recent news |
| Trade Analytics | `/trade` | Paginated table + bar chart; filters: flow, HS chapter (50-63), partner, year |
| News & Intelligence | `/news` | Categorized articles, text search, source filter, relevance scores |
| Reports | `/reports` | Create AI reports (GPT-4), track status, download PDF, send by email |
| Market Research | `/market-research` | 5 tabs: Overview · Segmentation · Companies · Frameworks · Events |
| Settings | `/settings` | Agent health monitoring, manual refresh triggers, API key status |
| Login | `/login` | JWT authentication form |

---

## MongoDB Collections

Database name: **`ctth`**

| Collection | Description | Key Indexes |
|-----------|-------------|-------------|
| `users` | User accounts | `email` (unique) |
| `trade_data` | Import/export records | Composite unique `(source, reporter_code, partner_code, hs_code, flow, period_date, frequency)` · `(flow, period_date)` · `partner_code` |
| `news_articles` | News from all agents | `source_url` (unique) · `category` · `published_at` · `created_at` |
| `reports` | Generated reports | `generated_by` · `status` |
| `market_segments` | Market segments | `(axis, code)` (unique) |
| `market_size_series` | Market size time series | `(segment_code, geography_code, year, flow)` (unique) |
| `companies` | Sector companies | `name` (unique) |
| `market_share_series` | Company market shares | `(company_name, segment_code, year)` (unique) |
| `competitive_events` | M&A, partnerships, etc. | `event_date` · `company_name` |
| `insights` | AI-generated insights | `category` · `created_at` |
| `framework_results` | Porter/PESTEL/TAM results | `(framework_type, created_at)` |
| `data_source_status` | Agent health tracking | `source_name` (unique) |
| `scheduler_runs` | Pipeline execution history | `started_at` |
| `email_recipients` | Email notification list | `(user_id, email)` (unique) |

---

## Performance Optimisations

### Backend

| Optimisation | Before | After |
|-------------|--------|-------|
| Dashboard: 4 sequential `_sum_trade_value()` calls → 1 combined pipeline + `asyncio.gather` | ~4–5 s | ~0.5 s |
| Market research overview: 7 sequential DB round-trips → 1 pipeline + 3 parallel counts | ~3 s | ~0.4 s |
| Segments N+1: one `find_one()` per segment → 1 batch aggregation | O(N) queries | 2 queries |
| In-memory TTL cache (5 min) on dashboard + market-research overview | — | Instant on cache hit |
| Compound index `(flow, period_date)` + `partner_code` index | Full collection scan | Index scan |

### Frontend

| Optimisation | Impact |
|-------------|--------|
| Client-side TTL cache in `api.ts` (dashboard=2 min, market-research=3 min, settings=1–5 min) | Navigation back to cached pages is instant |
| Lazy-load Recharts components via `next/dynamic` (AreaTrendChart, BarChart, PieChart) | Initial bundle −~200 KB |
| Webpack `splitChunks` for `recharts` and `lucide-react` | Separate chunks, loaded only when needed |
| `compress: true` in `next.config.js` (gzip/brotli) | Transfer size −60–70% |
| `Cache-Control: max-age=31536000, immutable` on `/_next/static/` | Static assets cached 1 year in browser |
| Polling interval refs tracked in `useRef` + cleaned up on unmount | No memory leak on page navigation |
| Cache bust (`dashboardApi.invalidate()`) on Actualiser button | Refresh always fetches fresh data |

---

## Design System

### CTTH Color Palette
- **Primary**: Tropical Teal — `#58B9AF`
- **Surface**: Gunmetal — `#353A3A`
- **Accent**: Frozen Water — `#C1DEDB`
- **Background**: White — `#FFFFFF`

### UI Patterns
- Glass morphism cards (`glass-card`) with `backdrop-blur` and subtle borders
- `animate-slide-up` entrance animations with staggered delays
- Gradient icon containers per data type
- Responsive grid layouts (1 → 2 → 4 columns)
- Skeleton/spinner placeholders for lazy-loaded charts

---

## Email Delivery

Reports can be sent via `POST /api/reports/{id}/send-email`. The system tries the primary API first, then automatically falls back to the secondary:

```
Primary:  https://aic-mail-server.vercel.app/api/send-email
Fallback: https://mail-api-mounsef.vercel.app/api/send-email
```

Expected payload format (handled internally):
```json
{
  "to": "recipient@example.com",
  "cc": "",
  "bcc": "",
  "subject": "Rapport — ...",
  "message": "<html>...</html>",
  "isHtml": true,
  "attachments": []
}
```

Response includes `"endpoint"` field indicating which URL was used.

---

## Troubleshooting

### Backend won't start
```bash
# Verify MongoDB connection
python -c "from app.database import get_sync_db; db = get_sync_db(); print(db.list_collection_names())"

# Verify required env vars
python -c "from app.config import settings; print(settings.MONGODB_URL[:30], settings.JWT_SECRET_KEY[:10])"
```
- Ensure `.env` exists with `MONGODB_URL` and `JWT_SECRET_KEY`
- Ensure the virtual environment is activated and dependencies installed

### Frontend shows loading spinner forever
- Verify backend is running: `curl http://localhost:5000/api/health`
- Check `NEXT_PUBLIC_API_URL` in `frontend/.env.local` matches the backend port
- Open DevTools → Network tab for CORS or 401 errors
- Clear local storage: `localStorage.clear()` in browser console

### Login fails
- Run `python ../scripts/seed_data.py` to create the admin user
- Default: `admin@ctth.ma` / `admin123`

### Charts not loading
- Charts are lazy-loaded; a brief spinner on first visit is expected
- Check DevTools Console for JS errors
- Ensure `next/dynamic` is resolving the chart component paths correctly

### Report generation fails
- Ensure `OPENAI_API_KEY` is set in `.env`
- Check status: `GET /api/reports/{id}/status` — the `error` field contains the error message
- Ensure the `reports/` directory exists in the backend container

### Email delivery fails
- Check `MAIL_API_URL` and `MAIL_API_FALLBACK_URL` in `.env`
- The endpoint response includes an `"endpoint"` field showing which URL was used
- Verify email payload does **not** include a `"from"` field (not accepted by the API)

### Agent data not updating
1. Check `GET /api/settings/data-sources` for last fetch timestamp and error message
2. Trigger manually: `POST /api/settings/data-sources/{name}/refresh`
3. Check pipeline history: `GET /api/scheduler/runs`
4. For Comtrade: verify `COMTRADE_PRIMARY_KEY` is valid and quota not exceeded (~500/day)

---

## License

Internal project for CTTH (Centre Technique du Textile et de l'Habillement).

Built by **Mounsef Litniti** — GenAI Consultant at AI Crafters.
