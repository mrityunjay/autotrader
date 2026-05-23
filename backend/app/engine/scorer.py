import asyncio
from datetime import datetime
from typing import List, Dict, Optional
from loguru import logger

from app.data.fetcher import NIFTY200_WATCHLIST, fetch_daily_candles, add_indicators
from app.config import settings


def _score_stock(df) -> Dict:
    """
    Score a stock 0-100 using technical indicators.
    Higher = stronger buy signal for intraday momentum.
    """
    if df is None or len(df) < 30:
        return {"score": 0, "rsi": None, "macd_hist": None,
                "volume_ratio": None, "momentum_1d": None,
                "momentum_5d": None, "ma_trend": None}

    row = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else row
    score = 0.0
    details = {}

    # ── RSI scoring (0-20 pts) ──────────────────────────────────────
    rsi = row.get("rsi")
    details["rsi"] = round(float(rsi), 2) if rsi else None
    if rsi:
        if 45 <= rsi <= 60:          # sweet spot: bullish but not overbought
            score += 20
        elif 40 <= rsi < 45 or 60 < rsi <= 65:
            score += 12
        elif 35 <= rsi < 40:
            score += 5
        # RSI > 70 or < 30 = no points (overbought / oversold risk)

    # ── MACD scoring (0-25 pts) ─────────────────────────────────────
    macd_hist = row.get("macd_hist")
    prev_hist = prev.get("macd_hist")
    details["macd_hist"] = round(float(macd_hist), 4) if macd_hist else None
    if macd_hist is not None and prev_hist is not None:
        if macd_hist > 0 and macd_hist > prev_hist:    # bullish + accelerating
            score += 25
        elif macd_hist > 0:                             # bullish but slowing
            score += 15
        elif macd_hist < 0 and macd_hist > prev_hist:  # negative but recovering
            score += 8

    # ── Volume scoring (0-20 pts) ───────────────────────────────────
    vol_ratio = row.get("volume_ratio")
    details["volume_ratio"] = round(float(vol_ratio), 2) if vol_ratio else None
    if vol_ratio:
        if vol_ratio >= 2.5:
            score += 20
        elif vol_ratio >= 2.0:
            score += 15
        elif vol_ratio >= 1.5:
            score += 10
        elif vol_ratio >= 1.2:
            score += 5

    # ── Price momentum (0-20 pts) ───────────────────────────────────
    close = row["close"]
    prev_close = df.iloc[-2]["close"] if len(df) >= 2 else close
    prev5_close = df.iloc[-6]["close"] if len(df) >= 6 else close

    mom_1d = (close - prev_close) / prev_close * 100
    mom_5d = (close - prev5_close) / prev5_close * 100
    details["momentum_1d"] = round(mom_1d, 2)
    details["momentum_5d"] = round(mom_5d, 2)

    if mom_1d > 0 and mom_5d > 0:
        score += 20
    elif mom_1d > 0:
        score += 10
    elif mom_5d > 0:
        score += 5

    # ── Moving average trend (0-15 pts) ─────────────────────────────
    ma20 = row.get("ma20")
    ma50 = row.get("ma50")
    ma_trend = None
    if ma20 and ma50:
        ma_trend = round((ma20 - ma50) / ma50 * 100, 2)
        details["ma_trend"] = ma_trend
        if close > ma20 > ma50:           # strong uptrend
            score += 15
        elif close > ma20:
            score += 8
        elif close > ma50:
            score += 4

    return {
        "score": round(score, 2),
        "rsi": details.get("rsi"),
        "macd_hist": details.get("macd_hist"),
        "volume_ratio": details.get("volume_ratio"),
        "momentum_1d": details.get("momentum_1d"),
        "momentum_5d": details.get("momentum_5d"),
        "ma_trend": ma_trend,
        "last_price": round(float(row["close"]), 2),
    }


async def score_all_stocks() -> List[Dict]:
    """
    Fetch data and score all watchlist stocks.
    Returns sorted list (highest score first).
    """
    results = []
    today = datetime.now().strftime("%Y-%m-%d")

    logger.info(f"Scoring {len(NIFTY200_WATCHLIST)} stocks for {today}...")

    # Run in thread pool since Angel One SDK is synchronous
    loop = asyncio.get_event_loop()

    for stock in NIFTY200_WATCHLIST:
        try:
            df = await loop.run_in_executor(None, fetch_daily_candles, stock["token"])
            if df is not None:
                df = add_indicators(df)
                result = _score_stock(df)
                result.update({
                    "symbol": stock["symbol"],
                    "token": stock["token"],
                    "name": stock["name"],
                    "date": today,
                })
                results.append(result)
        except Exception as e:
            logger.warning(f"Scoring failed for {stock['symbol']}: {e}")

    results.sort(key=lambda x: x["score"], reverse=True)

    # Mark top N as selected
    top_n = min(settings.top_stocks_to_score, len(results))
    for i, r in enumerate(results):
        r["selected"] = 1 if i < top_n else 0

    logger.info(
        f"Scoring complete. Top 5: {[r['symbol'] + '(' + str(r['score']) + ')' for r in results[:5]]}"
    )
    return results


def get_top_buy_candidates(scored: List[Dict], n: int = 5) -> List[Dict]:
    """Filter scored stocks to the top buy candidates."""
    selected = [s for s in scored if s["selected"] == 1]
    # Further filter: RSI not overbought, positive momentum
    candidates = [
        s for s in selected
        if (s["rsi"] is None or s["rsi"] < 68)
        and (s["momentum_1d"] is None or s["momentum_1d"] > -1)
        and s["score"] >= 40
    ]
    return candidates[:n]
