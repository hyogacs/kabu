"""Stock data fetching service.

Tries yfinance first; falls back to mock data if network is unavailable.
"""

import logging
from datetime import datetime, timezone

import yfinance as yf
import pandas as pd

from app.core.config import settings
from app.models.stock import (
    HistoricalBar,
    Market,
    StockQuote,
)
from app.services.mock_data import (
    get_mock_history,
    get_mock_history_df,
    get_mock_quote,
    get_mock_quotes,
)

logger = logging.getLogger(__name__)

# Track whether yfinance is reachable
_yfinance_available: bool | None = None

JP_STOCK_NAMES = {
    "7203.T": "Toyota Motor",
    "6758.T": "Sony Group",
    "9984.T": "SoftBank Group",
    "6861.T": "Keyence",
    "7974.T": "Nintendo",
    "8306.T": "Mitsubishi UFJ Financial",
    "9433.T": "KDDI",
    "6501.T": "Hitachi",
    "4063.T": "Shin-Etsu Chemical",
    "6902.T": "Denso",
}


def _detect_market(symbol: str) -> Market:
    return Market.JP if symbol.endswith(".T") else Market.US


def _get_currency(market: Market) -> str:
    return "JPY" if market == Market.JP else "USD"


def _check_yfinance() -> bool:
    """Check if yfinance can reach Yahoo Finance."""
    global _yfinance_available
    if _yfinance_available is not None:
        return _yfinance_available
    try:
        t = yf.Ticker("AAPL")
        h = t.history(period="1d")
        _yfinance_available = not h.empty
    except Exception:
        _yfinance_available = False
    if not _yfinance_available:
        logger.warning("Yahoo Finance unavailable - using simulated data")
    return _yfinance_available


def _yf_quote(symbol: str) -> StockQuote | None:
    """Fetch quote from Yahoo Finance."""
    ticker = yf.Ticker(symbol)
    info = ticker.info
    if not info or "regularMarketPrice" not in info:
        hist = ticker.history(period="2d")
        if hist.empty:
            return None
        last = hist.iloc[-1]
        prev = hist.iloc[-2] if len(hist) > 1 else hist.iloc[-1]
        current_price = float(last["Close"])
        previous_close = float(prev["Close"])
        market = _detect_market(symbol)
        return StockQuote(
            symbol=symbol,
            name=JP_STOCK_NAMES.get(symbol, symbol),
            market=market,
            currency=_get_currency(market),
            current_price=current_price,
            previous_close=previous_close,
            open_price=float(last["Open"]),
            day_high=float(last["High"]),
            day_low=float(last["Low"]),
            volume=int(last["Volume"]),
            change=round(current_price - previous_close, 4),
            change_percent=round(
                (current_price - previous_close) / previous_close * 100, 2
            ),
            timestamp=datetime.now(timezone.utc),
        )

    market = _detect_market(symbol)
    current_price = info.get("regularMarketPrice", 0)
    previous_close = info.get("regularMarketPreviousClose", current_price)
    change = current_price - previous_close
    change_pct = (change / previous_close * 100) if previous_close else 0

    name = info.get("shortName") or info.get("longName") or symbol
    if market == Market.JP:
        name = JP_STOCK_NAMES.get(symbol, name)

    return StockQuote(
        symbol=symbol,
        name=name,
        market=market,
        currency=_get_currency(market),
        current_price=current_price,
        previous_close=previous_close,
        open_price=info.get("regularMarketOpen", current_price),
        day_high=info.get("regularMarketDayHigh", current_price),
        day_low=info.get("regularMarketDayLow", current_price),
        volume=info.get("regularMarketVolume", 0),
        change=round(change, 4),
        change_percent=round(change_pct, 2),
        timestamp=datetime.now(timezone.utc),
    )


def fetch_quote(symbol: str) -> StockQuote | None:
    """Fetch real-time quote (auto-fallback to mock data)."""
    if _check_yfinance():
        try:
            return _yf_quote(symbol)
        except Exception as e:
            logger.error(f"yfinance error for {symbol}: {e}")
    return get_mock_quote(symbol)


def fetch_quotes(symbols: list[str]) -> list[StockQuote]:
    """Fetch quotes for multiple symbols."""
    if _check_yfinance():
        quotes = []
        for symbol in symbols:
            try:
                q = _yf_quote(symbol)
                if q:
                    quotes.append(q)
            except Exception as e:
                logger.error(f"yfinance error for {symbol}: {e}")
                q = get_mock_quote(symbol)
                if q:
                    quotes.append(q)
        return quotes
    return get_mock_quotes(symbols)


def fetch_history(
    symbol: str, period: str = "6mo", interval: str = "1d"
) -> list[HistoricalBar]:
    """Fetch historical OHLCV data."""
    if _check_yfinance():
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period, interval=interval)
            if not hist.empty:
                bars = []
                for date, row in hist.iterrows():
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
        except Exception as e:
            logger.error(f"yfinance history error for {symbol}: {e}")
    return get_mock_history(symbol, period, interval)


def fetch_history_df(symbol: str, period: str = "6mo") -> pd.DataFrame:
    """Fetch historical data as a pandas DataFrame for analysis."""
    if _check_yfinance():
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period)
            if not df.empty:
                return df
        except Exception as e:
            logger.error(f"yfinance history_df error for {symbol}: {e}")
    return get_mock_history_df(symbol, period)
