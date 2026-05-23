import pandas as pd
import ta
from datetime import datetime, timedelta
from typing import Optional
from loguru import logger

from app.broker.angel_one import angel_client


# Nifty 200 symbol → token mapping (top 50 liquid stocks for scoring)
# Token IDs from Angel One instrument list
NIFTY200_WATCHLIST = [
    {"symbol": "RELIANCE-EQ",  "token": "2885",  "name": "Reliance Industries"},
    {"symbol": "TCS-EQ",       "token": "11536", "name": "TCS"},
    {"symbol": "HDFCBANK-EQ",  "token": "1333",  "name": "HDFC Bank"},
    {"symbol": "INFY-EQ",      "token": "1594",  "name": "Infosys"},
    {"symbol": "ICICIBANK-EQ", "token": "4963",  "name": "ICICI Bank"},
    {"symbol": "HINDUNILVR-EQ","token": "1394",  "name": "HUL"},
    {"symbol": "ITC-EQ",       "token": "1660",  "name": "ITC"},
    {"symbol": "SBIN-EQ",      "token": "3045",  "name": "SBI"},
    {"symbol": "BAJFINANCE-EQ","token": "317",   "name": "Bajaj Finance"},
    {"symbol": "KOTAKBANK-EQ", "token": "1922",  "name": "Kotak Mahindra"},
    {"symbol": "LT-EQ",        "token": "11483", "name": "L&T"},
    {"symbol": "AXISBANK-EQ",  "token": "5900",  "name": "Axis Bank"},
    {"symbol": "ASIANPAINT-EQ","token": "236",   "name": "Asian Paints"},
    {"symbol": "HCLTECH-EQ",   "token": "7229",  "name": "HCL Tech"},
    {"symbol": "MARUTI-EQ",    "token": "10999", "name": "Maruti"},
    {"symbol": "TITAN-EQ",     "token": "3506",  "name": "Titan"},
    {"symbol": "WIPRO-EQ",     "token": "3787",  "name": "Wipro"},
    {"symbol": "SUNPHARMA-EQ", "token": "3351",  "name": "Sun Pharma"},
    {"symbol": "ULTRACEMCO-EQ","token": "11532", "name": "UltraTech Cement"},
    {"symbol": "NESTLEIND-EQ", "token": "17963", "name": "Nestle"},
    {"symbol": "POWERGRID-EQ", "token": "14977", "name": "Power Grid"},
    {"symbol": "NTPC-EQ",      "token": "11630", "name": "NTPC"},
    {"symbol": "TECHM-EQ",     "token": "13538", "name": "Tech Mahindra"},
    {"symbol": "ONGC-EQ",      "token": "2475",  "name": "ONGC"},
    {"symbol": "DMART-EQ",      "token": "19913", "name": "D-Mart (Avenue Supermarts)"},
    {"symbol": "TATASTEEL-EQ", "token": "3499",  "name": "Tata Steel"},
    {"symbol": "BAJAJFINSV-EQ","token": "16675", "name": "Bajaj Finserv"},
    {"symbol": "ADANIENT-EQ",  "token": "25",    "name": "Adani Enterprises"},
    {"symbol": "ADANIPORTS-EQ","token": "15083", "name": "Adani Ports"},
    {"symbol": "GRASIM-EQ",    "token": "1232",  "name": "Grasim"},
    {"symbol": "JSWSTEEL-EQ",  "token": "11723", "name": "JSW Steel"},
    {"symbol": "HINDALCO-EQ",  "token": "1363",  "name": "Hindalco"},
    {"symbol": "CIPLA-EQ",     "token": "694",   "name": "Cipla"},
    {"symbol": "DRREDDY-EQ",   "token": "881",   "name": "Dr Reddy's"},
    {"symbol": "EICHERMOT-EQ", "token": "910",   "name": "Eicher Motors"},
    {"symbol": "BPCL-EQ",      "token": "526",   "name": "BPCL"},
    {"symbol": "HEROMOTOCO-EQ","token": "1348",  "name": "Hero MotoCorp"},
    {"symbol": "DIVISLAB-EQ",  "token": "10940", "name": "Divi's Labs"},
    {"symbol": "BHARTIARTL-EQ","token": "10604", "name": "Bharti Airtel"},
    {"symbol": "COALINDIA-EQ", "token": "20374", "name": "Coal India"},
    {"symbol": "BRITANNIA-EQ", "token": "547",   "name": "Britannia"},
    {"symbol": "INDUSINDBK-EQ","token": "5258",  "name": "IndusInd Bank"},
    {"symbol": "APOLLOHOSP-EQ","token": "157",   "name": "Apollo Hospitals"},
    {"symbol": "BAJAJ-AUTO-EQ","token": "16669", "name": "Bajaj Auto"},
    {"symbol": "TATACONSUM-EQ","token": "3432",  "name": "Tata Consumer"},
    {"symbol": "SBILIFE-EQ",   "token": "21808", "name": "SBI Life"},
    {"symbol": "HDFCLIFE-EQ",  "token": "467",   "name": "HDFC Life"},
    {"symbol": "UPL-EQ",       "token": "11287", "name": "UPL"},
    {"symbol": "M&M-EQ",       "token": "2031",  "name": "Mahindra"},
    {"symbol": "SHREECEM-EQ",  "token": "3103",  "name": "Shree Cement"},
]


def fetch_daily_candles(token: str, days: int = 60) -> Optional[pd.DataFrame]:
    """Fetch daily OHLCV for last N days."""
    to_date = datetime.now()
    from_date = to_date - timedelta(days=days + 10)  # buffer for weekends

    candles = angel_client.get_candles(
        token=token,
        exchange="NSE",
        interval="ONE_DAY",
        from_date=from_date.strftime("%Y-%m-%d 09:15"),
        to_date=to_date.strftime("%Y-%m-%d 15:30"),
    )

    if not candles:
        return None

    df = pd.DataFrame(candles, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp").reset_index(drop=True)
    df[["open", "high", "low", "close", "volume"]] = df[
        ["open", "high", "low", "close", "volume"]
    ].apply(pd.to_numeric)

    return df.tail(days)


def fetch_intraday_candles(token: str, interval: str = "FIVE_MINUTE") -> Optional[pd.DataFrame]:
    """Fetch today's intraday candles."""
    today = datetime.now()
    from_date = today.replace(hour=9, minute=15, second=0)

    candles = angel_client.get_candles(
        token=token,
        exchange="NSE",
        interval=interval,
        from_date=from_date.strftime("%Y-%m-%d %H:%M"),
        to_date=today.strftime("%Y-%m-%d %H:%M"),
    )

    if not candles:
        return None

    df = pd.DataFrame(candles, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp").reset_index(drop=True)
    df[["open", "high", "low", "close", "volume"]] = df[
        ["open", "high", "low", "close", "volume"]
    ].apply(pd.to_numeric)

    return df


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Compute RSI, MACD, Bollinger Bands, moving averages on OHLCV dataframe."""
    if len(df) < 26:
        return df

    # RSI (14)
    df["rsi"] = ta.momentum.RSIIndicator(df["close"], window=14).rsi()

    # MACD (12, 26, 9)
    macd_ind = ta.trend.MACD(df["close"], window_fast=12, window_slow=26, window_sign=9)
    df["macd"] = macd_ind.macd()
    df["macd_signal"] = macd_ind.macd_signal()
    df["macd_hist"] = macd_ind.macd_diff()

    # Moving averages
    df["ma20"] = ta.trend.SMAIndicator(df["close"], window=20).sma_indicator()
    df["ma50"] = ta.trend.SMAIndicator(df["close"], window=50).sma_indicator()

    # Bollinger Bands (20, 2)
    bb = ta.volatility.BollingerBands(df["close"], window=20, window_dev=2)
    df["bb_upper"] = bb.bollinger_hband()
    df["bb_lower"] = bb.bollinger_lband()
    df["bb_mid"] = bb.bollinger_mavg()

    # Average True Range (volatility)
    df["atr"] = ta.volatility.AverageTrueRange(
        df["high"], df["low"], df["close"], window=14
    ).average_true_range()

    # Volume moving average
    df["vol_ma20"] = df["volume"].rolling(20).mean()
    df["volume_ratio"] = df["volume"] / df["vol_ma20"]

    return df
