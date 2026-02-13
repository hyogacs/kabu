"""Application configuration."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Kabu - Stock Monitor"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    # Stock data refresh interval (seconds)
    REFRESH_INTERVAL: int = 30

    # Default watchlist
    DEFAULT_US_STOCKS: list[str] = [
        "AAPL", "GOOGL", "MSFT", "AMZN", "NVDA",
        "TSLA", "META", "JPM", "V", "WMT",
    ]
    DEFAULT_JP_STOCKS: list[str] = [
        "7203.T", "6758.T", "9984.T", "6861.T", "7974.T",
        "8306.T", "9433.T", "6501.T", "4063.T", "6902.T",
    ]

    # AI Analysis
    AI_LOOKBACK_DAYS: int = 120
    SHORT_MA_PERIOD: int = 5
    MEDIUM_MA_PERIOD: int = 20
    LONG_MA_PERIOD: int = 60

    class Config:
        env_file = ".env"


settings = Settings()
