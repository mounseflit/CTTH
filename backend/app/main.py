import logging

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, dashboard, health, market_research, news, reports, scheduler_routes, settings_routes, trade
from app.database import close_connections, create_indexes

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Creating MongoDB indexes …")
    await create_indexes()

    # Initialize and start scheduler
    from app.scheduler.core import init_scheduler, start_scheduler
    init_scheduler()
    start_scheduler()

    yield

    # Shutdown
    from app.scheduler.core import stop_scheduler
    stop_scheduler()

    logger.info("Closing MongoDB connections …")
    await close_connections()


app = FastAPI(
    title="CTTH AI Watch Agent",
    description="Plateforme de veille intelligente pour le secteur textile marocain",
    version="0.1.0",
    lifespan=lifespan,
    redirect_slashes=False,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4000",
        "http://127.0.0.1:4000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["Authentification"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Tableau de bord"])
app.include_router(trade.router, prefix="/api/trade", tags=["Donnees commerciales"])
app.include_router(news.router, prefix="/api/news", tags=["Actualites"])
app.include_router(reports.router, prefix="/api/reports", tags=["Rapports"])
app.include_router(
    settings_routes.router, prefix="/api/settings", tags=["Parametres"]
)
app.include_router(
    market_research.router, prefix="/api/market-research", tags=["Etude de marche"]
)
app.include_router(health.router, prefix="/api/health", tags=["Sante"])
app.include_router(
    scheduler_routes.router, prefix="/api/scheduler", tags=["Planificateur"]
)


@app.get("/")
async def root():
    return {
        "name": "CTTH AI Watch Agent",
        "version": "0.1.0",
        "status": "running",
    }
