from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from loguru import logger

from app.config import settings


class RiskSignal(str, Enum):
    HOLD = "HOLD"
    STOP_LOSS = "STOP_LOSS"
    TARGET = "TARGET"
    TRAILING_STOP = "TRAILING_STOP"
    SQUARE_OFF = "SQUARE_OFF"


@dataclass
class PositionRisk:
    """Tracks risk state for a single open position."""

    trade_id: int
    symbol: str
    entry_price: float
    quantity: int
    stop_loss_pct: float = field(default_factory=lambda: settings.stop_loss_pct)
    target_pct: float = field(default_factory=lambda: settings.target_pct)
    trailing_sl_pct: float = field(default_factory=lambda: settings.trailing_sl_pct)

    # Computed at init
    initial_sl: float = field(init=False)
    target: float = field(init=False)
    highest_price: float = field(init=False)
    current_sl: float = field(init=False)
    in_profit_zone: bool = field(init=False, default=False)

    def __post_init__(self):
        self.initial_sl = round(self.entry_price * (1 - self.stop_loss_pct), 2)
        self.target = round(self.entry_price * (1 + self.target_pct), 2)
        self.highest_price = self.entry_price
        self.current_sl = self.initial_sl

    def update(self, current_price: float) -> RiskSignal:
        """
        Call on every price tick. Updates trailing SL and returns action signal.

        Trailing SL logic:
          - Price rises → SL moves up proportionally (never goes below entry)
          - Once in profit zone (price > entry), SL locks at entry minimum
          - If price falls to SL → exit
          - If price hits target → exit
        """
        current_price = round(current_price, 2)

        # Update highest watermark
        if current_price > self.highest_price:
            self.highest_price = current_price

            # Recalculate trailing SL
            new_sl = round(current_price * (1 - self.trailing_sl_pct), 2)

            # Never let SL go below entry once we're profitable
            if current_price > self.entry_price:
                new_sl = max(new_sl, self.entry_price)
                self.in_profit_zone = True

            if new_sl > self.current_sl:
                old_sl = self.current_sl
                self.current_sl = new_sl
                logger.debug(
                    f"{self.symbol}: Trailing SL moved {old_sl} → {self.current_sl} "
                    f"(price={current_price}, high={self.highest_price})"
                )

        # --- Signal evaluation ---

        # Stop loss hit
        if current_price <= self.current_sl:
            if self.current_sl > self.initial_sl:
                logger.info(f"{self.symbol}: Trailing SL triggered at {current_price} (SL={self.current_sl})")
                return RiskSignal.TRAILING_STOP
            logger.info(f"{self.symbol}: Stop loss triggered at {current_price} (SL={self.current_sl})")
            return RiskSignal.STOP_LOSS

        # Target hit
        if current_price >= self.target:
            logger.info(f"{self.symbol}: Target hit at {current_price} (target={self.target})")
            return RiskSignal.TARGET

        return RiskSignal.HOLD

    def unrealized_pnl(self, current_price: float) -> float:
        return round((current_price - self.entry_price) * self.quantity, 2)

    def unrealized_pnl_pct(self, current_price: float) -> float:
        return round((current_price - self.entry_price) / self.entry_price * 100, 2)

    def to_dict(self) -> dict:
        return {
            "trade_id": self.trade_id,
            "symbol": self.symbol,
            "entry_price": self.entry_price,
            "quantity": self.quantity,
            "initial_sl": self.initial_sl,
            "current_sl": self.current_sl,
            "target": self.target,
            "highest_price": self.highest_price,
            "in_profit_zone": self.in_profit_zone,
        }


class RiskManager:
    """Manages risk across all open positions."""

    def __init__(self):
        self._positions: dict[int, PositionRisk] = {}  # trade_id → PositionRisk

    def add_position(
        self,
        trade_id: int,
        symbol: str,
        entry_price: float,
        quantity: int,
    ) -> PositionRisk:
        pos = PositionRisk(
            trade_id=trade_id,
            symbol=symbol,
            entry_price=entry_price,
            quantity=quantity,
        )
        self._positions[trade_id] = pos
        logger.info(
            f"Risk tracking started: {symbol} entry={entry_price} "
            f"SL={pos.initial_sl} target={pos.target}"
        )
        return pos

    def remove_position(self, trade_id: int):
        self._positions.pop(trade_id, None)

    def check_position(self, trade_id: int, current_price: float) -> Optional[RiskSignal]:
        pos = self._positions.get(trade_id)
        if not pos:
            return None
        return pos.update(current_price)

    def get_position(self, trade_id: int) -> Optional[PositionRisk]:
        return self._positions.get(trade_id)

    def all_positions(self) -> list:
        return list(self._positions.values())

    def total_unrealized_pnl(self, price_map: dict) -> float:
        """price_map: {symbol: current_price}"""
        total = 0.0
        for pos in self._positions.values():
            price = price_map.get(pos.symbol)
            if price:
                total += pos.unrealized_pnl(price)
        return round(total, 2)

    def calculate_position_size(self, price: float, capital: float) -> int:
        """
        Returns quantity to buy given price and allocated capital.
        Ensures at least 1 share.
        """
        if price <= 0:
            return 0
        qty = int(capital // price)
        return max(qty, 1)


risk_manager = RiskManager()
