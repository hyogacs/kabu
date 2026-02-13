"""Mock stock data generator for environments where Yahoo Finance is unavailable.

Generates realistic-looking stock data with random walks based on
actual recent price ranges for US and JP stocks.
"""

import random
import math
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd

from app.models.stock import HistoricalBar, Market, StockQuote

# Seed data: (symbol, name, market, currency, base_price, volatility)
STOCK_SEEDS = {
    # US Stocks
    "AAPL": ("Apple Inc.", Market.US, "USD", 232.0, 0.018),
    "GOOGL": ("Alphabet Inc.", Market.US, "USD", 182.0, 0.020),
    "MSFT": ("Microsoft Corp.", Market.US, "USD", 420.0, 0.017),
    "AMZN": ("Amazon.com Inc.", Market.US, "USD", 218.0, 0.022),
    "NVDA": ("NVIDIA Corp.", Market.US, "USD", 135.0, 0.030),
    "TSLA": ("Tesla Inc.", Market.US, "USD", 355.0, 0.035),
    "META": ("Meta Platforms Inc.", Market.US, "USD", 680.0, 0.023),
    "JPM": ("JPMorgan Chase & Co.", Market.US, "USD", 265.0, 0.015),
    "V": ("Visa Inc.", Market.US, "USD", 325.0, 0.014),
    "WMT": ("Walmart Inc.", Market.US, "USD", 98.0, 0.012),
    # JP Stocks
    "7203.T": ("Toyota Motor", Market.JP, "JPY", 2680.0, 0.016),
    "6758.T": ("Sony Group", Market.JP, "JPY", 3200.0, 0.020),
    "9984.T": ("SoftBank Group", Market.JP, "JPY", 9200.0, 0.025),
    "6861.T": ("Keyence", Market.JP, "JPY", 62000.0, 0.018),
    "7974.T": ("Nintendo", Market.JP, "JPY", 9900.0, 0.019),
    "8306.T": ("Mitsubishi UFJ Financial", Market.JP, "JPY", 1850.0, 0.017),
    "9433.T": ("KDDI", Market.JP, "JPY", 4900.0, 0.012),
    "6501.T": ("Hitachi", Market.JP, "JPY", 3600.0, 0.020),
    "4063.T": ("Shin-Etsu Chemical", Market.JP, "JPY", 5200.0, 0.016),
    "6902.T": ("Denso", Market.JP, "JPY", 2100.0, 0.018),
}

# Cache generated histories so they stay consistent within a session
_history_cache: dict[str, pd.DataFrame] = {}


def _generate_ohlcv_series(
    base_price: float, volatility: float, days: int = 180
) -> pd.DataFrame:
    """Generate realistic OHLCV data using geometric Brownian motion."""
    dates = pd.bdate_range(end=datetime.now(), periods=days)
    prices = [base_price * random.uniform(0.85, 0.95)]  # Start lower

    # Random walk with drift
    drift = random.uniform(-0.0002, 0.0005)
    for i in range(1, days):
        shock = random.gauss(drift, volatility)
        prices.append(prices[-1] * math.exp(shock))

    data = []
    for i, date in enumerate(dates):
        close = prices[i]
        daily_vol = abs(random.gauss(0, volatility))
        high = close * (1 + daily_vol * random.uniform(0.3, 1.2))
        low = close * (1 - daily_vol * random.uniform(0.3, 1.2))
        open_ = low + (high - low) * random.uniform(0.2, 0.8)
        # Volume: base volume with some randomness
        avg_volume = int(base_price * 50000 / max(base_price, 1))
        vol = int(avg_volume * random.uniform(0.5, 2.5))
        data.append(
            {
                "Date": date,
                "Open": round(open_, 2),
                "High": round(high, 2),
                "Low": round(low, 2),
                "Close": round(close, 2),
                "Volume": vol,
            }
        )

    df = pd.DataFrame(data)
    df.set_index("Date", inplace=True)
    return df


def get_mock_history_df(symbol: str, period: str = "6mo") -> pd.DataFrame:
    """Get mock historical DataFrame for a symbol."""
    if symbol not in STOCK_SEEDS:
        return pd.DataFrame()

    if symbol not in _history_cache:
        _, _, _, base_price, volatility = STOCK_SEEDS[symbol]
        _history_cache[symbol] = _generate_ohlcv_series(base_price, volatility, 180)

    df = _history_cache[symbol].copy()

    # Trim by period
    period_days = {"1mo": 22, "3mo": 66, "6mo": 132, "1y": 252, "2y": 504}
    days = period_days.get(period, 132)
    if len(df) > days:
        df = df.iloc[-days:]

    return df


def get_mock_history(
    symbol: str, period: str = "6mo", interval: str = "1d"
) -> list[HistoricalBar]:
    """Get mock historical bars."""
    df = get_mock_history_df(symbol, period)
    if df.empty:
        return []

    bars = []
    for date, row in df.iterrows():
        bars.append(
            HistoricalBar(
                date=date.strftime("%Y-%m-%d"),
                open=round(float(row["Open"]), 2),
                high=round(float(row["High"]), 2),
                low=round(float(row["Low"]), 2),
                close=round(float(row["Close"]), 2),
                volume=int(row["Volume"]),
            )
        )
    return bars


def get_mock_quote(symbol: str) -> StockQuote | None:
    """Generate a mock real-time quote."""
    if symbol not in STOCK_SEEDS:
        return None

    name, market, currency, base_price, volatility = STOCK_SEEDS[symbol]

    # Use cached history for consistency
    df = get_mock_history_df(symbol)
    if df.empty:
        return None

    current_price = float(df["Close"].iloc[-1])
    previous_close = float(df["Close"].iloc[-2]) if len(df) > 1 else current_price

    # Add small real-time jitter
    jitter = random.gauss(0, volatility * 0.1)
    current_price = round(current_price * (1 + jitter), 2)

    change = round(current_price - previous_close, 4)
    change_pct = round(change / previous_close * 100, 2) if previous_close else 0

    last_row = df.iloc[-1]

    return StockQuote(
        symbol=symbol,
        name=name,
        market=market,
        currency=currency,
        current_price=current_price,
        previous_close=previous_close,
        open_price=round(float(last_row["Open"]), 2),
        day_high=round(max(float(last_row["High"]), current_price), 2),
        day_low=round(min(float(last_row["Low"]), current_price), 2),
        volume=int(last_row["Volume"]),
        change=change,
        change_percent=change_pct,
        timestamp=datetime.now(timezone.utc),
    )


def get_mock_quotes(symbols: list[str]) -> list[StockQuote]:
    """Get mock quotes for multiple symbols."""
    quotes = []
    for symbol in symbols:
        q = get_mock_quote(symbol)
        if q:
            quotes.append(q)
    return quotes
