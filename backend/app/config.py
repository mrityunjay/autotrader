from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    # Angel One credentials
    angel_api_key: str = Field(default="PLACEHOLDER", alias="ANGEL_API_KEY")
    angel_client_id: str = Field(default="PLACEHOLDER", alias="ANGEL_CLIENT_ID")
    angel_password: str = Field(default="PLACEHOLDER", alias="ANGEL_PASSWORD")
    angel_totp_secret: str = Field(default="PLACEHOLDER", alias="ANGEL_TOTP_SECRET")

    # Trading config
    trading_capital: float = Field(default=50000.0)
    max_positions: int = Field(default=5)
    position_size_pct: float = Field(default=0.20)
    stop_loss_pct: float = Field(default=0.02)
    target_pct: float = Field(default=0.045)
    trailing_sl_pct: float = Field(default=0.02)
    top_stocks_to_score: int = Field(default=50)

    # Market hours
    market_open: str = Field(default="09:15")
    market_close: str = Field(default="15:30")
    square_off_time: str = Field(default="15:10")
    scoring_time: str = Field(default="09:05")

    # App
    database_url: str = Field(default="sqlite+aiosqlite:///./trading.db")
    log_level: str = Field(default="INFO")
    environment: str = Field(default="development")


settings = Settings()
