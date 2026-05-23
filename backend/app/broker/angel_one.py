import pyotp
import asyncio
from datetime import datetime, timedelta
from typing import Optional
from loguru import logger
from SmartApi import SmartConnect

from app.config import settings


class AngelOneClient:
    """Angel One SmartAPI wrapper with auto-reconnect and session management."""

    def __init__(self):
        self._obj: Optional[SmartConnect] = None
        self._auth_token: Optional[str] = None
        self._feed_token: Optional[str] = None
        self._last_login: Optional[datetime] = None

    def _is_session_valid(self) -> bool:
        if not self._auth_token or not self._last_login:
            return False
        # Re-auth every 6 hours to be safe
        return (datetime.now() - self._last_login).total_seconds() < 21600

    def login(self) -> bool:
        try:
            totp = pyotp.TOTP(settings.angel_totp_secret).now()
            obj = SmartConnect(api_key=settings.angel_api_key)
            data = obj.generateSession(
                settings.angel_client_id,
                settings.angel_password,
                totp
            )
            if data["status"]:
                self._obj = obj
                self._auth_token = data["data"]["jwtToken"]
                self._feed_token = obj.getfeedToken()
                self._last_login = datetime.now()
                logger.info("Angel One login successful")
                return True
            else:
                logger.error(f"Angel One login failed: {data['message']}")
                return False
        except Exception as e:
            logger.error(f"Angel One login exception: {e}")
            return False

    def ensure_session(self) -> bool:
        if not self._is_session_valid():
            return self.login()
        return True

    def get_profile(self) -> dict:
        self.ensure_session()
        return self._obj.getProfile(self._auth_token)

    def get_ltp(self, exchange: str, symbol: str, token: str) -> Optional[float]:
        """Get last traded price."""
        self.ensure_session()
        try:
            data = self._obj.ltpData(exchange, symbol, token)
            if data["status"]:
                return float(data["data"]["ltp"])
            return None
        except Exception as e:
            logger.error(f"LTP fetch failed for {symbol}: {e}")
            return None

    def get_candles(
        self,
        token: str,
        exchange: str,
        interval: str,
        from_date: str,
        to_date: str
    ) -> Optional[list]:
        """
        Fetch historical OHLCV candle data.
        interval: ONE_MINUTE, FIVE_MINUTE, TEN_MINUTE, FIFTEEN_MINUTE, THIRTY_MINUTE, ONE_HOUR, ONE_DAY
        from_date/to_date: 'YYYY-MM-DD HH:MM'
        """
        self.ensure_session()
        try:
            params = {
                "exchange": exchange,
                "symboltoken": token,
                "interval": interval,
                "fromdate": from_date,
                "todate": to_date,
            }
            data = self._obj.getCandleData(params)
            if data["status"]:
                return data["data"]  # list of [timestamp, open, high, low, close, volume]
            logger.warning(f"Candle fetch returned no data for token {token}: {data.get('message')}")
            return None
        except Exception as e:
            logger.error(f"Candle fetch failed for token {token}: {e}")
            return None

    def place_order(
        self,
        symbol: str,
        token: str,
        side: str,          # BUY / SELL
        quantity: int,
        order_type: str = "MARKET",
        price: float = 0,
        exchange: str = "NSE",
        product: str = "INTRADAY",
    ) -> Optional[str]:
        """Place order and return order_id."""
        self.ensure_session()
        try:
            params = {
                "variety": "NORMAL",
                "tradingsymbol": symbol,
                "symboltoken": token,
                "transactiontype": side,
                "exchange": exchange,
                "ordertype": order_type,
                "producttype": product,
                "duration": "DAY",
                "price": str(price) if order_type == "LIMIT" else "0",
                "squareoff": "0",
                "stoploss": "0",
                "quantity": str(quantity),
            }
            data = self._obj.placeOrder(params)
            if data["status"]:
                order_id = data["data"]["orderid"]
                logger.info(f"Order placed: {side} {quantity} {symbol} → order_id={order_id}")
                return order_id
            else:
                logger.error(f"Order placement failed: {data['message']}")
                return None
        except Exception as e:
            logger.error(f"Order placement exception for {symbol}: {e}")
            return None

    def cancel_order(self, order_id: str, variety: str = "NORMAL") -> bool:
        self.ensure_session()
        try:
            data = self._obj.cancelOrder(order_id, variety)
            return data.get("status", False)
        except Exception as e:
            logger.error(f"Cancel order failed: {e}")
            return False

    def get_positions(self) -> list:
        self.ensure_session()
        try:
            data = self._obj.position()
            if data["status"]:
                return data["data"] or []
            return []
        except Exception as e:
            logger.error(f"Positions fetch failed: {e}")
            return []

    def get_funds(self) -> Optional[dict]:
        self.ensure_session()
        try:
            data = self._obj.rmsLimit()
            if data["status"]:
                return data["data"]
            return None
        except Exception as e:
            logger.error(f"Funds fetch failed: {e}")
            return None

    @property
    def feed_token(self) -> Optional[str]:
        return self._feed_token

    @property
    def auth_token(self) -> Optional[str]:
        return self._auth_token


# Singleton instance
angel_client = AngelOneClient()
