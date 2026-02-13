"""Stock data fetching service.

Directly calls Yahoo Finance chart API via httpx — no yfinance dependency.
This bypasses yfinance's fragile cookie/crumb handling that causes
JSONDecodeError on many corporate networks.
"""

import logging
import time
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
    "Accept-Encoding": "gzip, deflate, br",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
}

# Crumb cache
_crumb: str | None = None
_cookies: httpx.Cookies | None = None


def _get_http_client() -> httpx.Client:
    """Create httpx client with proper settings."""
    return httpx.Client(
        headers=HEADERS,
        follow_redirects=True,
        timeout=15.0,
    )


def _init_cookies_and_crumb(client: httpx.Client) -> tuple[httpx.Cookies, str]:
    """Get Yahoo Finance consent cookies and crumb token."""
    global _crumb, _cookies
    if _crumb and _cookies:
        return _cookies, _crumb

    # Step 1: Visit Yahoo Finance to get cookies (consent, etc.)
    try:
        resp = client.get("https://finance.yahoo.com/quote/AAPL/")
        cookies = resp.cookies
    except Exception:
        cookies = httpx.Cookies()

    # Step 2: Get crumb
    try:
        resp = client.get(
            "https://query2.finance.yahoo.com/v1/test/getcrumb",
            cookies=cookies,
        )
        if resp.status_code == 200 and resp.text.strip():
            _crumb = resp.text.strip()
            _cookies = cookies
            logger.info(f"Yahoo Finance crumb obtained: {_crumb[:8]}...")
            return _cookies, _crumb
    except Exception as e:
        logger.warning(f"Failed to get crumb: {e}")

    # Return empty if crumb fails — chart API may still work without it
    _cookies = cookies
    _crumb = ""
    return _cookies, _crumb


def _fetch_chart(
    symbol: str,
    range_: str = "5d",
    interval: str = "1d",
) -> dict | None:
    """Fetch chart data from Yahoo Finance v8 chart API."""
    with _get_http_client() as client:
        cookies, crumb = _init_cookies_and_crumb(client)

        params: dict = {
            "range": range_,
            "interval": interval,
            "includePrePost": "false",
            "events": "",
        }
        if crumb:
            params["crumb"] = crumb

        url = YAHOO_CHART_URL.format(symbol=symbol)

        # Try up to 2 times (with and without crumb)
        for attempt in range(2):
            try:
                resp = client.get(url, params=params, cookies=cookies)
                if resp.status_code == 200:
                    data = resp.json()
                    result = data.get("chart", {}).get("result")
                    if result and len(result) > 0:
                        return result[0]
                    else:
                        error = data.get("chart", {}).get("error")
                        logger.error(f"Yahoo chart error for {symbol}: {error}")
                        return None
                elif resp.status_code == 401 and attempt == 0:
                    # Crumb expired, refresh
                    logger.info("Crumb expired, refreshing...")
                    global _crumb, _cookies
                    _crumb = None
                    _cookies = None
                    cookies, crumb = _init_cookies_and_crumb(client)
                    if crumb:
                        params["crumb"] = crumb
                    continue
                else:
                    logger.error(
                        f"Yahoo chart HTTP {resp.status_code} for {symbol}: "
                        f"{resp.text[:200]}"
                    )
                    return None
            except Exception as e:
                logger.error(f"Yahoo chart request failed for {symbol}: {e}")
                return None

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

    # Drop rows with None values (holidays, etc.)
    df.dropna(subset=["Close"], inplace=True)
    df.set_index("Date", inplace=True)

    # Replace any remaining None/NaN in volume
    df["Volume"] = df["Volume"].fillna(0).astype(int)

    return df


# ── Helper ───────────────────────────────────────────────────────

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

    name = _get_name(symbol, meta)

    return StockQuote(
        symbol=symbol,
        name=name,
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
