"""Stock data fetching service using yfinance.

Uses yf.download() as primary method (more reliable than Ticker.history),
with Ticker.info as supplement for real-time quote fields.
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

logger = logging.getLogger(__name__)

JP_STOCK_NAMES = {
    "7203.T": "トヨタ自動車",
    "6758.T": "ソニーグループ",
    "9984.T": "ソフトバンクグループ",
    "6861.T": "キーエンス",
    "7974.T": "任天堂",
    "8306.T": "三菱UFJ FG",
    "9433.T": "KDDI",
    "6501.T": "日立製作所",
    "4063.T": "信越化学工業",
    "6902.T": "デンソー",
}

US_STOCK_NAMES = {
    "AAPL": "Apple",
    "GOOGL": "Alphabet",
    "MSFT": "Microsoft",
    "AMZN": "Amazon",
    "NVDA": "NVIDIA",
    "TSLA": "Tesla",
    "META": "Meta",
    "JPM": "JPMorgan",
    "V": "Visa",
    "WMT": "Walmart",
}


def _detect_market(symbol: str) -> Market:
    return Market.JP if symbol.endswith(".T") else Market.US


def _get_currency(market: Market) -> str:
    return "JPY" if market == Market.JP else "USD"


def _get_name(symbol: str) -> str:
    return JP_STOCK_NAMES.get(symbol) or US_STOCK_NAMES.get(symbol) or symbol


def _download(symbol: str, period: str = "5d") -> pd.DataFrame:
    """Use yf.download() which is more reliable than Ticker.history()."""
    try:
        df = yf.download(symbol, period=period, progress=False, auto_adjust=True)
        if df is not None and not df.empty:
            # yf.download for single ticker may have multi-level columns
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            return df
    except Exception as e:
        logger.error(f"yf.download failed for {symbol}: {e}")
    return pd.DataFrame()


def fetch_quote(symbol: str) -> StockQuote | None:
    """Fetch real-time quote for a single symbol."""
    try:
        # Use download for price data (most reliable)
        df = _download(symbol, period="5d")
        if df.empty or len(df) < 1:
            logger.error(f"No data returned for {symbol}")
            return None

        last = df.iloc[-1]
        prev = df.iloc[-2] if len(df) >= 2 else df.iloc[-1]

        current_price = float(last["Close"])
        previous_close = float(prev["Close"])

        market = _detect_market(symbol)
        change = current_price - previous_close
        change_pct = (change / previous_close * 100) if previous_close else 0

        # Try to get name from Ticker.info, but don't fail if it errors
        name = _get_name(symbol)
        try:
            ticker = yf.Ticker(symbol)
            fast_info = getattr(ticker, "fast_info", None)
            if fast_info and hasattr(fast_info, "short_name"):
                name = fast_info.short_name or name
            elif hasattr(ticker, "info"):
                info = ticker.info
                if info:
                    name = info.get("shortName") or info.get("longName") or name
        except Exception:
            pass  # Use fallback name

        if market == Market.JP:
            name = JP_STOCK_NAMES.get(symbol, name)

        return StockQuote(
            symbol=symbol,
            name=name,
            market=market,
            currency=_get_currency(market),
            current_price=round(current_price, 2),
            previous_close=round(previous_close, 2),
            open_price=round(float(last["Open"]), 2),
            day_high=round(float(last["High"]), 2),
            day_low=round(float(last["Low"]), 2),
            volume=int(last["Volume"]),
            change=round(change, 4),
            change_percent=round(change_pct, 2),
            timestamp=datetime.now(timezone.utc),
        )
    except Exception as e:
        logger.error(f"Error fetching quote for {symbol}: {e}")
        return None


def fetch_quotes(symbols: list[str]) -> list[StockQuote]:
    """Fetch quotes for multiple symbols."""
    quotes = []
    for symbol in symbols:
        quote = fetch_quote(symbol)
        if quote:
            quotes.append(quote)
    return quotes


def fetch_history(
    symbol: str, period: str = "6mo", interval: str = "1d"
) -> list[HistoricalBar]:
    """Fetch historical OHLCV data."""
    try:
        df = yf.download(
            symbol, period=period, interval=interval,
            progress=False, auto_adjust=True,
        )
        if df is None or df.empty:
            return []
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
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
    except Exception as e:
        logger.error(f"Error fetching history for {symbol}: {e}")
        return []


def fetch_history_df(symbol: str, period: str = "6mo") -> pd.DataFrame:
    """Fetch historical data as a pandas DataFrame for analysis."""
    try:
        df = yf.download(symbol, period=period, progress=False, auto_adjust=True)
        if df is not None and not df.empty:
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            return df
    except Exception as e:
        logger.error(f"Error fetching history df for {symbol}: {e}")
    return pd.DataFrame()
