# CTTH — Centre Technique du Textile et de l'Habillement
## AI Watch Agent Platform

**Intelligent Trade Monitoring for Morocco's Textile Sector**

---

## 📋 Project Overview

CTTH AI Watch Agent is a comprehensive full-stack web application designed for monitoring and analyzing international trade data in Morocco's textile industry. The platform provides real-time market intelligence, automated news aggregation, and AI-powered report generation.

### Core Features

- 📊 **Trade Data Analytics**: Real-time import/export data from Eurostat and UN Comtrade
- 📰 **Automated News Aggregation**: AI-powered web search using OpenAI and Gemini
- 📄 **AI Report Generation**: Intelligent report creation with PDF export and email delivery
- 👥 **User Authentication**: JWT-based auth with role-based access control
- 📱 **Responsive Dashboard**: Modern Next.js frontend with real-time data visualization

---

## 🛠️ Tech Stack

### Backend
- **Framework**: FastAPI (Python 3.14)
- **Database**: MongoDB Atlas (Motor async driver)
- **Task Queue**: Celery (Redis)
- **APIs**: Eurostat, UN Comtrade, OpenAI, Gemini
- **Port**: 8000

### Frontend
- **Framework**: Next.js 14.2 (React 18)
- **Styling**: Tailwind CSS 3.4
- **State**: Zustand
- **Charts**: Recharts 2.13
- **Icons**: Lucide React
- **Port**: 3001

---

## 📁 Project Structure

```
CTTH/
├── backend/                    # FastAPI application
│   ├── app/
│   │   ├── agents/            # Data collection agents
│   │   ├── api/               # API routes
│   │   ├── models/            # MongoDB models
│   │   ├── schemas/           # Pydantic schemas
│   │   ├── services/          # Business logic
│   │   ├── tasks/             # Celery tasks
│   │   ├── config.py          # Configuration
│   │   ├── database.py        # MongoDB connection
│   │   └── main.py            # FastAPI app
│   ├── alembic/               # Database migrations
│   ├── requirements.txt       # Python dependencies
│   └── Dockerfile
│
├── frontend/                   # Next.js application
│   ├── src/
│   │   ├── app/               # App router pages
│   │   ├── components/        # React components
│   │   ├── lib/               # Utilities & API client
│   │   └── types/             # TypeScript definitions
│   ├── tailwind.config.ts     # Tailwind configuration
│   ├── tsconfig.json          # TypeScript config
│   ├── package.json           # Node dependencies
│   └── Dockerfile
│
├── scripts/                    # Utility scripts
├── docker-compose.yml         # Container orchestration
└── .gitignore
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.14+
- Node.js 18+
- MongoDB Atlas (or local MongoDB)
- Git

### Backend Setup

```bash
cd backend
pip install -r requirements.txt
export MONGODB_URL="mongodb+srv://..."
export JWT_SECRET_KEY="your-secret-key"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Frontend Setup

```bash
cd frontend
npm install
export NEXT_PUBLIC_API_URL="http://localhost:8000"
npm run dev
```

Access the application at **http://localhost:3001**

---

## 🔑 Key Features

### 1. Trade Analytics (`/trade`)
- Flow-based filtering (Imports/Exports)
- HS chapter classification
- Real-time data with 450+ trade records
- Top partner analysis and breakdowns

### 2. News & Intelligence (`/news`)
- AI-powered web search integration
- Multi-source aggregation (Gemini, OpenAI)
- 75+ news articles with timestamps

### 3. Report Generation (`/reports`)
- Customizable report types (Weekly, Market Analysis, Regulatory Alerts)
- AI-generated content via GPT-4
- PDF export functionality
- Email delivery via CTTH mail API

### 4. Dashboard (`/`)
- Key metrics and KPIs
- Market trends visualization
- Real-time data updates

---

## 🎨 Design System

### CTTH Color Palette
- **Primary**: Tropical Teal (#58B9AF)
- **Surface**: Gunmetal (#353A3A)
- **Accent**: Frozen Water (#C1DEDB)
- **Background**: White (#FFFFFF)

All components follow the CTTH brand guidelines with:
- Glass morphism cards
- Smooth gradients
- Responsive layouts
- Dark mode optimized

---

## 📊 Data Sources

- **Eurostat**: EU trade statistics (`ext_lt_maineu` dataset)
- **UN Comtrade**: International trade data (851 records)
- **OpenAI**: Web search & GPT-4 reports
- **Google Gemini**: Multi-model AI analysis

---

## 🔐 Authentication

- Email/password login
- JWT token-based sessions
- Role-based access (Analyst, Admin)
- Automatic token refresh

---

## 📧 Email Integration

Reports can be sent via the CTTH email API:
```
POST https://mail-api-mounsef.vercel.app/api/send-email
{
  "to": "recipient@example.com",
  "subject": "CTTH Report",
  "message": "HTML content",
  "isHtml": true
}
```

---

## 🐳 Docker Deployment

```bash
docker-compose up --build
```

Services:
- Backend: `http://localhost:8000`
- Frontend: `http://localhost:3001`

---

## 📝 Environment Variables

### Backend (`.env`)
```
MONGODB_URL=mongodb+srv://...
JWT_SECRET_KEY=your-secret-key
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=...
COMTRADE_API_KEY=...
```

### Frontend (`.env.local`)
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 👨‍💻 Development

### Code Structure
- Backend: FastAPI with async/await patterns
- Frontend: Next.js with app router
- Database: MongoDB with type-safe schemas
- API: RESTful design with OpenAPI docs

### API Endpoints
```
POST   /api/auth/register       - User registration
POST   /api/auth/login          - User login
GET    /api/dashboard           - Dashboard metrics
GET    /api/trade/data          - Trade data with pagination
GET    /api/news                - News articles
POST   /api/reports             - Create report
POST   /api/reports/{id}/email  - Send report via email
GET    /api/settings            - User settings
```

---

## 📄 License

© 2026 CTTH — Centre Technique du Textile et de l'Habillement

---

## 📞 Support

For issues or questions, contact the development team.

**Last Updated**: February 17, 2026
