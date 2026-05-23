from sqlalchemy import Column, String, Float, Integer, DateTime, Enum as SAEnum, Text
from sqlalchemy.sql import func
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum

from app.database import Base


class TradeStatus(str, Enum):
    OPEN = "OPEN"
    CLOSED_TARGET = "CLOSED_TARGET"
    CLOSED_STOPLOSS = "CLOSED_STOPLOSS"
    CLOSED_TRAILING = "CLOSED_TRAILING"
    CLOSED_SQUAREOFF = "CLOSED_SQUAREOFF"
    CLOSED_MANUAL = "CLOSED_MANUAL"


class OrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


# SQLAlchemy ORM models
class Trade(Base):
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False)
    token = Column(String(20), nullable=False)
    entry_price = Column(Float, nullable=False)
    exit_price = Column(Float, nullable=True)
    quantity = Column(Integer, nullable=False)
    stop_loss = Column(Float, nullable=False)
    target = Column(Float, nullable=False)
    current_sl = Column(Float, nullable=False)     # trailing SL tracks here
    highest_price = Column(Float, nullable=False)   # for trailing SL
    pnl = Column(Float, nullable=True)
    status = Column(SAEnum(TradeStatus), default=TradeStatus.OPEN)
    entry_order_id = Column(String(50), nullable=True)
    exit_order_id = Column(String(50), nullable=True)
    score = Column(Float, nullable=True)            # AI score at entry
    created_at = Column(DateTime, server_default=func.now())
    closed_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)


class ScoredStock(Base):
    __tablename__ = "scored_stocks"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(String(10), nullable=False)       # YYYY-MM-DD
    symbol = Column(String(20), nullable=False)
    token = Column(String(20), nullable=False)
    score = Column(Float, nullable=False)
    rsi = Column(Float, nullable=True)
    macd_hist = Column(Float, nullable=True)
    volume_ratio = Column(Float, nullable=True)
    momentum_1d = Column(Float, nullable=True)
    momentum_5d = Column(Float, nullable=True)
    ma_trend = Column(Float, nullable=True)
    last_price = Column(Float, nullable=True)
    selected = Column(Integer, default=0)           # 1 if picked for trading
    created_at = Column(DateTime, server_default=func.now())


class DailyPnL(Base):
    __tablename__ = "daily_pnl"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(String(10), unique=True, nullable=False)
    realized_pnl = Column(Float, default=0.0)
    unrealized_pnl = Column(Float, default=0.0)
    trades_count = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    capital_deployed = Column(Float, default=0.0)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())


# Pydantic response models
class TradeResponse(BaseModel):
    id: int
    symbol: str
    entry_price: float
    exit_price: Optional[float]
    quantity: int
    stop_loss: float
    target: float
    current_sl: float
    highest_price: float
    pnl: Optional[float]
    status: TradeStatus
    score: Optional[float]
    created_at: datetime
    closed_at: Optional[datetime]

    class Config:
        from_attributes = True


class ScoredStockResponse(BaseModel):
    symbol: str
    token: str
    score: float
    rsi: Optional[float]
    macd_hist: Optional[float]
    volume_ratio: Optional[float]
    momentum_1d: Optional[float]
    momentum_5d: Optional[float]
    last_price: Optional[float]
    selected: int

    class Config:
        from_attributes = True


class DailyPnLResponse(BaseModel):
    date: str
    realized_pnl: float
    unrealized_pnl: float
    trades_count: int
    winning_trades: int
    losing_trades: int
    capital_deployed: float

    class Config:
        from_attributes = True


class PortfolioStatus(BaseModel):
    total_capital: float
    deployed_capital: float
    available_capital: float
    open_positions: int
    realized_pnl_today: float
    unrealized_pnl: float
    total_pnl_today: float
    is_market_open: bool
    engine_running: bool


class SettingsUpdate(BaseModel):
    trading_capital: Optional[float] = None
    max_positions: Optional[int] = None
    stop_loss_pct: Optional[float] = None
    target_pct: Optional[float] = None
    trailing_sl_pct: Optional[float] = None
    position_size_pct: Optional[float] = None
