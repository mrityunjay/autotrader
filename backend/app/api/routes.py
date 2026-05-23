import json
import asyncio
from datetime import datetime, date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy import select, desc, and_
from loguru import logger

from app.database import get_db, AsyncSessionLocal
from app.models.schemas import (
    Trade, TradeStatus, ScoredStock, DailyPnL,
    TradeResponse, ScoredStockResponse, DailyPnLResponse,
    PortfolioStatus, SettingsUpdate,
)
from app.engine.order_engine import order_engine
from app.engine.risk_manager import risk_manager
from app.engine.scheduler import trading_scheduler
from app.broker.angel_one import angel_client
from app.config import settings
from app.data.fetcher import NIFTY200_WATCHLIST


router = APIRouter()

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket):
        self.active.remove(ws)

    async def broadcast(self, data: dict):
        msg = json.dumps(data)
        dead = []
        for ws in self.active:
            try:
                await ws.send_text(msg)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.active.remove(ws)


ws_manager = ConnectionManager()


# ─── Portfolio / Status ───────────────────────────────────────────────

@router.get("/status", response_model=PortfolioStatus)
async def get_status():
    positions = risk_manager.all_positions()
    deployed = sum(p.entry_price * p.quantity for p in positions)

    # Get unrealized PnL
    price_map = {}
    loop = asyncio.get_event_loop()
    for pos in positions:
        token = next((s["token"] for s in NIFTY200_WATCHLIST if s["symbol"] == pos.symbol), None)
        if token:
            ltp = await loop.run_in_executor(None, angel_client.get_ltp, "NSE", pos.symbol, token)
            if ltp:
                price_map[pos.symbol] = ltp

    unrealized_pnl = risk_manager.total_unrealized_pnl(price_map)

    return PortfolioStatus(
        total_capital=settings.trading_capital,
        deployed_capital=deployed,
        available_capital=settings.trading_capital - deployed,
        open_positions=len(positions),
        realized_pnl_today=order_engine.realized_pnl_today,
        unrealized_pnl=unrealized_pnl,
        total_pnl_today=order_engine.realized_pnl_today + unrealized_pnl,
        is_market_open=_is_market_hours(),
        engine_running=order_engine.is_running,
    )


# ─── Positions ────────────────────────────────────────────────────────

@router.get("/positions", response_model=List[TradeResponse])
async def get_open_positions(db=Depends(get_db)):
    result = await db.execute(
        select(Trade)
        .where(Trade.status == TradeStatus.OPEN)
        .order_by(desc(Trade.created_at))
    )
    return result.scalars().all()


@router.get("/positions/{trade_id}", response_model=TradeResponse)
async def get_position(trade_id: int, db=Depends(get_db)):
    result = await db.execute(select(Trade).where(Trade.id == trade_id))
    trade = result.scalar_one_or_none()
    if not trade:
        raise HTTPException(404, "Trade not found")
    return trade


@router.delete("/positions/{trade_id}")
async def manual_close_position(trade_id: int, db=Depends(get_db)):
    result = await db.execute(select(Trade).where(Trade.id == trade_id))
    trade = result.scalar_one_or_none()
    if not trade:
        raise HTTPException(404, "Trade not found")
    if trade.status != TradeStatus.OPEN:
        raise HTTPException(400, "Trade is not open")

    from app.engine.order_engine import order_engine as oe
    await oe._exit_position(trade, TradeStatus.CLOSED_MANUAL, db=db)
    return {"message": f"Position {trade.symbol} closed manually"}


# ─── Trade History ────────────────────────────────────────────────────

@router.get("/trades", response_model=List[TradeResponse])
async def get_trade_history(
    limit: int = 50,
    status: Optional[TradeStatus] = None,
    db=Depends(get_db)
):
    query = select(Trade).order_by(desc(Trade.created_at)).limit(limit)
    if status:
        query = query.where(Trade.status == status)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/trades/today", response_model=List[TradeResponse])
async def get_todays_trades(db=Depends(get_db)):
    today = datetime.now().strftime("%Y-%m-%d")
    result = await db.execute(
        select(Trade)
        .where(Trade.created_at >= today)
        .order_by(desc(Trade.created_at))
    )
    return result.scalars().all()


# ─── Scored Stocks ────────────────────────────────────────────────────

@router.get("/scores/today", response_model=List[ScoredStockResponse])
async def get_todays_scores(db=Depends(get_db)):
    today = datetime.now().strftime("%Y-%m-%d")
    result = await db.execute(
        select(ScoredStock)
        .where(ScoredStock.date == today)
        .order_by(desc(ScoredStock.score))
    )
    return result.scalars().all()


@router.post("/scores/refresh")
async def trigger_scoring():
    """Manually trigger stock scoring."""
    scores = await trading_scheduler.run_scoring_now()
    return {
        "message": f"Scored {len(scores)} stocks",
        "top5": [{"symbol": s["symbol"], "score": s["score"]} for s in scores[:5]]
    }


# ─── PnL ─────────────────────────────────────────────────────────────

@router.get("/pnl/daily", response_model=List[DailyPnLResponse])
async def get_daily_pnl(days: int = 30, db=Depends(get_db)):
    result = await db.execute(
        select(DailyPnL).order_by(desc(DailyPnL.date)).limit(days)
    )
    return result.scalars().all()


# ─── Engine controls ─────────────────────────────────────────────────

@router.post("/engine/start")
async def start_engine():
    await order_engine.start()
    return {"message": "Engine started"}


@router.post("/engine/stop")
async def stop_engine():
    await order_engine.stop()
    return {"message": "Engine stopped"}


@router.post("/engine/squareoff")
async def square_off():
    await order_engine.square_off_all()
    return {"message": "All positions squared off"}


# ─── Settings ─────────────────────────────────────────────────────────

@router.get("/settings")
async def get_settings():
    return {
        "trading_capital": settings.trading_capital,
        "max_positions": settings.max_positions,
        "stop_loss_pct": settings.stop_loss_pct,
        "target_pct": settings.target_pct,
        "trailing_sl_pct": settings.trailing_sl_pct,
        "position_size_pct": settings.position_size_pct,
        "market_open": settings.market_open,
        "market_close": settings.market_close,
        "square_off_time": settings.square_off_time,
    }


@router.patch("/settings")
async def update_settings(body: SettingsUpdate):
    """Hot-update trading parameters (takes effect on next trade)."""
    updated = {}
    for field, value in body.model_dump(exclude_none=True).items():
        if hasattr(settings, field):
            object.__setattr__(settings, field, value)
            updated[field] = value
    return {"updated": updated}


# ─── WebSocket live feed ──────────────────────────────────────────────

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            # Push live status every 3 seconds
            status = await get_status()
            positions = risk_manager.all_positions()

            pos_data = []
            loop = asyncio.get_event_loop()
            for pos in positions:
                token = next(
                    (s["token"] for s in NIFTY200_WATCHLIST if s["symbol"] == pos.symbol), None
                )
                ltp = None
                if token:
                    ltp = await loop.run_in_executor(
                        None, angel_client.get_ltp, "NSE", pos.symbol, token
                    )
                pos_data.append({
                    **pos.to_dict(),
                    "ltp": ltp,
                    "unrealized_pnl": pos.unrealized_pnl(ltp) if ltp else 0,
                    "unrealized_pnl_pct": pos.unrealized_pnl_pct(ltp) if ltp else 0,
                })

            await websocket.send_json({
                "type": "update",
                "status": status.model_dump(),
                "positions": pos_data,
                "timestamp": datetime.now().isoformat(),
            })
            await asyncio.sleep(3)
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)


# ─── Helpers ──────────────────────────────────────────────────────────

def _is_market_hours() -> bool:
    import pytz
    IST = pytz.timezone("Asia/Kolkata")
    now = datetime.now(IST)
    if now.weekday() >= 5:
        return False
    open_h, open_m = map(int, settings.market_open.split(":"))
    close_h, close_m = map(int, settings.market_close.split(":"))
    open_time = now.replace(hour=open_h, minute=open_m, second=0)
    close_time = now.replace(hour=close_h, minute=close_m, second=0)
    return open_time <= now <= close_time
