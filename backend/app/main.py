from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import sys

from app.database import init_db
from app.api.routes import router
from app.engine.scheduler import trading_scheduler
from app.broker.angel_one import angel_client
from app.config import settings


# Configure logger
logger.remove()
logger.add(sys.stdout, level=settings.log_level, format="{time:HH:mm:ss} | {level} | {message}")
logger.add("logs/trading.log", rotation="1 day", retention="30 days", level="DEBUG")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Trading System...")
    await init_db()
    logger.info("Database initialized")

    # Login to Angel One
    if angel_client.login():
        logger.info("Broker connection established")
    else:
        logger.warning("Broker login failed — check credentials in .env")

    # Start scheduler (handles market open/close/scoring automatically)
    trading_scheduler.start()
    logger.info("Trading scheduler started")

    yield

    # Shutdown
    logger.info("Shutting down...")
    trading_scheduler.stop()
    pass  # broker session expires naturally


app = FastAPI(
    title="AutoTrader",
    description="Automated intraday trading system — NSE via Angel One SmartAPI",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "broker_connected": angel_client._auth_token is not None,
        "engine_running": False,
    }
