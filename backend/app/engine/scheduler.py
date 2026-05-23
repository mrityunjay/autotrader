import asyncio
from datetime import datetime
from typing import Optional
import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from loguru import logger

from app.config import settings
from app.engine.scorer import score_all_stocks, get_top_buy_candidates
from app.engine.order_engine import order_engine
from app.database import AsyncSessionLocal
from app.models.schemas import ScoredStock


IST = pytz.timezone("Asia/Kolkata")


def _is_weekday() -> bool:
    return datetime.now(IST).weekday() < 5  # Mon-Fri


class TradingScheduler:
    def __init__(self):
        self._scheduler = AsyncIOScheduler(timezone=IST)
        self._scored_today: list = []

    def start(self):
        # Morning: score stocks (e.g. 09:05)
        score_h, score_m = map(int, settings.scoring_time.split(":"))
        self._scheduler.add_job(
            self._morning_scoring,
            CronTrigger(hour=score_h, minute=score_m, timezone=IST),
            id="morning_scoring",
        )

        # Market open: start engine and enter positions (09:20 — 5 min after open)
        open_h, open_m = map(int, settings.market_open.split(":"))
        self._scheduler.add_job(
            self._market_open,
            CronTrigger(hour=open_h, minute=open_m + 5, timezone=IST),
            id="market_open",
        )

        # EOD square-off
        sq_h, sq_m = map(int, settings.square_off_time.split(":"))
        self._scheduler.add_job(
            self._square_off,
            CronTrigger(hour=sq_h, minute=sq_m, timezone=IST),
            id="square_off",
        )

        # Market close: stop engine
        close_h, close_m = map(int, settings.market_close.split(":"))
        self._scheduler.add_job(
            self._market_close,
            CronTrigger(hour=close_h, minute=close_m + 5, timezone=IST),
            id="market_close",
        )

        self._scheduler.start()
        logger.info(
            f"Scheduler started. Scoring={settings.scoring_time} "
            f"Open={settings.market_open} SquareOff={settings.square_off_time}"
        )

    def stop(self):
        self._scheduler.shutdown(wait=False)

    async def _morning_scoring(self):
        if not _is_weekday():
            return
        logger.info("Running morning stock scoring...")
        try:
            self._scored_today = await score_all_stocks()
            await self._save_scores(self._scored_today)
            logger.info(f"Scored {len(self._scored_today)} stocks")
        except Exception as e:
            logger.error(f"Morning scoring failed: {e}")

    async def _market_open(self):
        if not _is_weekday():
            return
        logger.info("Market open — starting order engine...")
        await order_engine.start()

        if not self._scored_today:
            logger.warning("No scored stocks for today — running emergency scoring")
            self._scored_today = await score_all_stocks()

        candidates = get_top_buy_candidates(self._scored_today, n=settings.max_positions)
        if candidates:
            logger.info(f"Entering {len(candidates)} positions: {[c['symbol'] for c in candidates]}")
            await order_engine.enter_positions(candidates)
        else:
            logger.warning("No buy candidates passed the filter today")

    async def _square_off(self):
        if not _is_weekday():
            return
        logger.info("EOD square-off triggered...")
        await order_engine.square_off_all()

    async def _market_close(self):
        if not _is_weekday():
            return
        logger.info("Market closed — stopping order engine")
        await order_engine.stop()

    async def _save_scores(self, scores: list):
        async with AsyncSessionLocal() as db:
            for s in scores:
                record = ScoredStock(
                    date=s["date"],
                    symbol=s["symbol"],
                    token=s["token"],
                    score=s["score"],
                    rsi=s.get("rsi"),
                    macd_hist=s.get("macd_hist"),
                    volume_ratio=s.get("volume_ratio"),
                    momentum_1d=s.get("momentum_1d"),
                    momentum_5d=s.get("momentum_5d"),
                    ma_trend=s.get("ma_trend"),
                    last_price=s.get("last_price"),
                    selected=s.get("selected", 0),
                )
                db.add(record)
            await db.commit()

    @property
    def scored_today(self) -> list:
        return self._scored_today

    async def run_scoring_now(self) -> list:
        """Manual trigger for scoring (API endpoint use)."""
        self._scored_today = await score_all_stocks()
        await self._save_scores(self._scored_today)
        return self._scored_today


trading_scheduler = TradingScheduler()
