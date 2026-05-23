import asyncio
from datetime import datetime
from typing import List, Optional, Dict
from loguru import logger
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.broker.angel_one import angel_client
from app.engine.risk_manager import risk_manager, RiskSignal
from app.models.schemas import Trade, TradeStatus, ScoredStock
from app.database import AsyncSessionLocal
from app.config import settings


class OrderEngine:
    """Manages the full trade lifecycle: entry, monitoring, exit."""

    def __init__(self):
        self._running = False
        self._monitor_task: Optional[asyncio.Task] = None
        self._realized_pnl_today = 0.0
        self._today_date = datetime.now().strftime("%Y-%m-%d")

    # ─── Public controls ──────────────────────────────────────────────

    async def start(self):
        if self._running:
            return
        self._running = True
        self._today_date = datetime.now().strftime("%Y-%m-%d")
        self._realized_pnl_today = 0.0
        # Restore any open positions from DB
        await self._restore_open_positions()
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info("Order engine started")

    async def stop(self):
        self._running = False
        if self._monitor_task:
            self._monitor_task.cancel()
        logger.info("Order engine stopped")

    async def square_off_all(self):
        """Force-close all open positions (called at EOD)."""
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Trade).where(Trade.status == TradeStatus.OPEN)
            )
            open_trades = result.scalars().all()

        for trade in open_trades:
            await self._exit_position(trade, TradeStatus.CLOSED_SQUAREOFF)

        logger.info(f"Square-off complete. Closed {len(open_trades)} positions.")

    # ─── Entry ────────────────────────────────────────────────────────

    async def enter_positions(self, candidates: List[Dict]):
        """Buy top candidates up to max_positions limit."""
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Trade).where(Trade.status == TradeStatus.OPEN)
            )
            current_open = len(result.scalars().all())

        slots = settings.max_positions - current_open
        if slots <= 0:
            logger.info("Max positions reached, skipping entry.")
            return

        capital_per_position = settings.trading_capital * settings.position_size_pct

        for candidate in candidates[:slots]:
            symbol = candidate["symbol"]
            token = candidate["token"]
            score = candidate["score"]

            # Get live price
            loop = asyncio.get_event_loop()
            ltp = await loop.run_in_executor(
                None, angel_client.get_ltp, "NSE", symbol, token
            )

            if not ltp or ltp <= 0:
                logger.warning(f"Skipping {symbol}: could not get LTP")
                continue

            quantity = risk_manager.calculate_position_size(ltp, capital_per_position)
            if quantity <= 0:
                logger.warning(f"Skipping {symbol}: insufficient capital for price {ltp}")
                continue

            # Place buy order
            order_id = await loop.run_in_executor(
                None,
                angel_client.place_order,
                symbol, token, "BUY", quantity
            )

            if not order_id:
                logger.error(f"Order placement failed for {symbol}")
                continue

            # Refresh LTP after order (might have slipped slightly)
            entry_price = await loop.run_in_executor(
                None, angel_client.get_ltp, "NSE", symbol, token
            ) or ltp

            async with AsyncSessionLocal() as db:
                pos = risk_manager.add_position(0, symbol, entry_price, quantity)
                trade = Trade(
                    symbol=symbol,
                    token=token,
                    entry_price=entry_price,
                    quantity=quantity,
                    stop_loss=pos.initial_sl,
                    target=pos.target,
                    current_sl=pos.current_sl,
                    highest_price=pos.highest_price,
                    status=TradeStatus.OPEN,
                    entry_order_id=order_id,
                    score=score,
                )
                db.add(trade)
                await db.commit()
                await db.refresh(trade)

            # Update risk manager with actual DB id
            risk_manager.remove_position(0)
            risk_manager.add_position(trade.id, symbol, entry_price, quantity)

            logger.info(
                f"Entered {symbol}: qty={quantity} price={entry_price} "
                f"SL={pos.initial_sl} target={pos.target} order={order_id}"
            )

    # ─── Monitor loop ─────────────────────────────────────────────────

    async def _monitor_loop(self):
        """Poll LTPs every 5 seconds and check risk signals."""
        while self._running:
            try:
                await self._check_positions()
            except Exception as e:
                logger.error(f"Monitor loop error: {e}")
            await asyncio.sleep(5)

    async def _check_positions(self):
        positions = risk_manager.all_positions()
        if not positions:
            return

        loop = asyncio.get_event_loop()

        for pos in positions:
            ltp = await loop.run_in_executor(
                None, angel_client.get_ltp, "NSE", pos.symbol, self._get_token(pos.symbol)
            )

            if ltp is None:
                continue

            signal = risk_manager.check_position(pos.trade_id, ltp)

            if signal == RiskSignal.STOP_LOSS:
                await self._exit_by_trade_id(pos.trade_id, TradeStatus.CLOSED_STOPLOSS)
            elif signal == RiskSignal.TARGET:
                await self._exit_by_trade_id(pos.trade_id, TradeStatus.CLOSED_TARGET)
            elif signal in (RiskSignal.TRAILING_STOP,):
                await self._exit_by_trade_id(pos.trade_id, TradeStatus.CLOSED_TRAILING)
            else:
                # Update DB with latest trailing SL
                await self._update_sl_in_db(pos.trade_id, pos.current_sl, pos.highest_price)

    async def _exit_by_trade_id(self, trade_id: int, status: TradeStatus):
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Trade).where(Trade.id == trade_id))
            trade = result.scalar_one_or_none()
            if trade:
                await self._exit_position(trade, status, db=db)

    async def _exit_position(
        self,
        trade: Trade,
        status: TradeStatus,
        db: Optional[AsyncSession] = None
    ):
        loop = asyncio.get_event_loop()
        exit_price = await loop.run_in_executor(
            None, angel_client.get_ltp, "NSE", trade.symbol, trade.token
        ) or trade.entry_price

        order_id = await loop.run_in_executor(
            None,
            angel_client.place_order,
            trade.symbol, trade.token, "SELL", trade.quantity
        )

        pnl = round((exit_price - trade.entry_price) * trade.quantity, 2)
        self._realized_pnl_today += pnl

        risk_manager.remove_position(trade.id)

        close_fn = db if db else AsyncSessionLocal()
        if not db:
            ctx = AsyncSessionLocal()
            async with ctx as session:
                await session.execute(
                    update(Trade)
                    .where(Trade.id == trade.id)
                    .values(
                        exit_price=exit_price,
                        pnl=pnl,
                        status=status,
                        exit_order_id=order_id,
                        closed_at=datetime.now(),
                        current_sl=trade.current_sl,
                    )
                )
                await session.commit()
        else:
            await db.execute(
                update(Trade)
                .where(Trade.id == trade.id)
                .values(
                    exit_price=exit_price,
                    pnl=pnl,
                    status=status,
                    exit_order_id=order_id,
                    closed_at=datetime.now(),
                )
            )
            await db.commit()

        logger.info(
            f"Closed {trade.symbol}: exit={exit_price} pnl={pnl:+.2f} status={status.value}"
        )

    async def _update_sl_in_db(self, trade_id: int, current_sl: float, highest_price: float):
        async with AsyncSessionLocal() as db:
            await db.execute(
                update(Trade)
                .where(Trade.id == trade_id)
                .values(current_sl=current_sl, highest_price=highest_price)
            )
            await db.commit()

    async def _restore_open_positions(self):
        """On restart, re-add open trades to risk manager."""
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Trade).where(Trade.status == TradeStatus.OPEN)
            )
            trades = result.scalars().all()

        for trade in trades:
            pos = risk_manager.add_position(
                trade.id, trade.symbol, trade.entry_price, trade.quantity
            )
            # Restore current trailing SL state
            pos.current_sl = trade.current_sl
            pos.highest_price = trade.highest_price
            logger.info(f"Restored position: {trade.symbol} id={trade.id}")

    def _get_token(self, symbol: str) -> str:
        """Look up Angel One token for a symbol."""
        from app.data.fetcher import NIFTY200_WATCHLIST
        for s in NIFTY200_WATCHLIST:
            if s["symbol"] == symbol:
                return s["token"]
        return ""

    @property
    def realized_pnl_today(self) -> float:
        return self._realized_pnl_today

    @property
    def is_running(self) -> bool:
        return self._running


order_engine = OrderEngine()
