"""Stock data fetching service.

Directly calls Yahoo Finance chart API via httpx — no yfinance dependency.
Uses a persistent HTTP client with cached cookies for performance.
"""

import logging
from datetime import datetime, timezone

import httpx
import pandas as pd

from app.core.config import settings
from app.models.stock import (
    HistoricalBar,
    Market,
    StockQuote,
)

logger = logging.getLogger(__name__)

# ── Name mappings ────────────────────────────────────────────────
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

# ── Yahoo Finance direct API client ─────────────────────────────

YAHOO_CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json,text/html,application/xhtml+xml",
    "Accept-Language": "en-US,en;q=0.9",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
}

# Module-level persistent client (reuses TCP connections + cookies)
_client: httpx.Client | None = None
_crumb: str | None = None  # None = not tried yet, "" = tried and failed/not needed
_session_ready = False


def _get_client() -> httpx.Client:
    """Get or create the persistent HTTP client."""
    global _client
    if _client is None:
        _client = httpx.Client(
            headers=HEADERS,
            follow_redirects=True,
            timeout=15.0,
        )
    return _client


def _ensure_session() -> None:
    """Initialize session cookies + crumb once on first use."""
    global _crumb, _session_ready

    if _session_ready:
        return

    client = _get_client()

    # Step 1: Get cookies from Yahoo Finance
    try:
        client.get("https://finance.yahoo.com/quote/AAPL/")
        logger.info("Yahoo Finance session cookies obtained")
    except Exception as e:
        logger.warning(f"Failed to get Yahoo cookies (non-fatal): {e}")

    # Step 2: Try to get crumb (optional — chart API works without it)
    try:
        resp = client.get("https://query2.finance.yahoo.com/v1/test/getcrumb")
        if resp.status_code == 200 and resp.text.strip():
            _crumb = resp.text.strip()
            logger.info(f"Yahoo crumb obtained: {_crumb[:8]}...")
        else:
            _crumb = ""  # Not available, that's fine
            logger.info("Yahoo crumb not available (chart API works without it)")
    except Exception:
        _crumb = ""

    _session_ready = True


def _fetch_chart(
    symbol: str,
    range_: str = "5d",
    interval: str = "1d",
) -> dict | None:
    """Fetch chart data from Yahoo Finance v8 chart API."""
    _ensure_session()
    client = _get_client()

    params: dict = {
        "range": range_,
        "interval": interval,
        "includePrePost": "false",
        "events": "",
    }
    if _crumb:
        params["crumb"] = _crumb

    url = YAHOO_CHART_URL.format(symbol=symbol)

    try:
        resp = client.get(url, params=params)
        if resp.status_code == 200:
            data = resp.json()
            result = data.get("chart", {}).get("result")
            if result and len(result) > 0:
                return result[0]
            error = data.get("chart", {}).get("error")
            logger.error(f"Yahoo chart error for {symbol}: {error}")
            return None

        # 401 = crumb expired → refresh session once and retry
        if resp.status_code == 401:
            global _session_ready
            _session_ready = False
            _ensure_session()
            if _crumb:
                params["crumb"] = _crumb
            resp = client.get(url, params=params)
            if resp.status_code == 200:
                data = resp.json()
                result = data.get("chart", {}).get("result")
                if result and len(result) > 0:
                    return result[0]

        logger.error(f"Yahoo chart HTTP {resp.status_code} for {symbol}")
        return None
    except Exception as e:
        logger.error(f"Yahoo chart request failed for {symbol}: {e}")
        return None


def _parse_chart_to_df(chart: dict) -> pd.DataFrame:
    """Parse Yahoo chart API response into a DataFrame."""
    timestamps = chart.get("timestamp", [])
    quotes = chart.get("indicators", {}).get("quote", [{}])[0]

    if not timestamps or not quotes:
        return pd.DataFrame()

    df = pd.DataFrame({
        "Date": pd.to_datetime(timestamps, unit="s", utc=True),
        "Open": quotes.get("open", []),
        "High": quotes.get("high", []),
        "Low": quotes.get("low", []),
        "Close": quotes.get("close", []),
        "Volume": quotes.get("volume", []),
    })

    df.dropna(subset=["Close"], inplace=True)
    df.set_index("Date", inplace=True)
    df["Volume"] = df["Volume"].fillna(0).astype(int)

    return df


# ── Helpers ──────────────────────────────────────────────────────

def _detect_market(symbol: str) -> Market:
    return Market.JP if symbol.endswith(".T") else Market.US


def _get_currency(market: Market) -> str:
    return "JPY" if market == Market.JP else "USD"


def _get_name(symbol: str, chart_meta: dict | None = None) -> str:
    if symbol in JP_STOCK_NAMES:
        return JP_STOCK_NAMES[symbol]
    if symbol in US_STOCK_NAMES:
        return US_STOCK_NAMES[symbol]
    if chart_meta:
        return (
            chart_meta.get("shortName")
            or chart_meta.get("longName")
            or chart_meta.get("symbol", symbol)
        )
    return symbol


# ── Public API ───────────────────────────────────────────────────

def fetch_quote(symbol: str) -> StockQuote | None:
    """Fetch real-time quote for a single symbol."""
    chart = _fetch_chart(symbol, range_="5d", interval="1d")
    if not chart:
        return None

    df = _parse_chart_to_df(chart)
    if df.empty:
        return None

    meta = chart.get("meta", {})

    last = df.iloc[-1]
    prev = df.iloc[-2] if len(df) >= 2 else df.iloc[-1]

    current_price = float(last["Close"])
    previous_close = meta.get("chartPreviousClose") or float(prev["Close"])

    market = _detect_market(symbol)
    change = current_price - previous_close
    change_pct = (change / previous_close * 100) if previous_close else 0

    return StockQuote(
        symbol=symbol,
        name=_get_name(symbol, meta),
        market=market,
        currency=meta.get("currency", _get_currency(market)),
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
    chart = _fetch_chart(symbol, range_=period, interval=interval)
    if not chart:
        return []

    df = _parse_chart_to_df(chart)
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


def fetch_history_df(symbol: str, period: str = "6mo") -> pd.DataFrame:
    """Fetch historical data as a pandas DataFrame for analysis."""
    chart = _fetch_chart(symbol, range_=period, interval="1d")
    if not chart:
        return pd.DataFrame()
    return _parse_chart_to_df(chart)
