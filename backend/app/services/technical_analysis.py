"""Technical analysis calculations using pure numpy/pandas (no external TA library)."""

import numpy as np
import pandas as pd

from app.models.stock import TechnicalIndicators


def _rsi(series: pd.Series, window: int = 14) -> pd.Series:
    """Calculate Relative Strength Index."""
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.ewm(com=window - 1, min_periods=window).mean()
    avg_loss = loss.ewm(com=window - 1, min_periods=window).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def _macd(
    series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """Calculate MACD, Signal line, and Histogram."""
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def _bollinger_bands(
    series: pd.Series, window: int = 20, num_std: float = 2.0
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """Calculate Bollinger Bands (upper, middle, lower)."""
    middle = series.rolling(window=window).mean()
    std = series.rolling(window=window).std()
    upper = middle + num_std * std
    lower = middle - num_std * std
    return upper, middle, lower


def _atr(
    high: pd.Series, low: pd.Series, close: pd.Series, window: int = 14
) -> pd.Series:
    """Calculate Average True Range."""
    prev_close = close.shift(1)
    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(window=window).mean()


def _obv(close: pd.Series, volume: pd.Series) -> pd.Series:
    """Calculate On-Balance Volume."""
    direction = np.sign(close.diff())
    direction.iloc[0] = 0
    return (volume * direction).cumsum()


def _stochastic(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    window: int = 14,
    smooth: int = 3,
) -> tuple[pd.Series, pd.Series]:
    """Calculate Stochastic Oscillator (%K, %D)."""
    lowest_low = low.rolling(window=window).min()
    highest_high = high.rolling(window=window).max()
    stoch_k = 100 * (close - lowest_low) / (highest_high - lowest_low)
    stoch_d = stoch_k.rolling(window=smooth).mean()
    return stoch_k, stoch_d


def calculate_indicators(df: pd.DataFrame) -> TechnicalIndicators:
    """Calculate all technical indicators from OHLCV DataFrame."""
    if df.empty or len(df) < 20:
        return TechnicalIndicators()

    close = df["Close"]
    high = df["High"]
    low = df["Low"]
    volume = df["Volume"]

    # Moving Averages
    sma_5 = close.rolling(window=5).mean().iloc[-1]
    sma_20 = close.rolling(window=20).mean().iloc[-1]
    sma_60 = close.rolling(window=60).mean().iloc[-1] if len(df) >= 60 else None
    ema_12 = close.ewm(span=12, adjust=False).mean().iloc[-1]
    ema_26 = close.ewm(span=26, adjust=False).mean().iloc[-1]

    # RSI
    rsi_14 = _rsi(close, 14).iloc[-1]

    # MACD
    macd_line, signal_line, histogram = _macd(close)
    macd_val = macd_line.iloc[-1]
    macd_sig = signal_line.iloc[-1]
    macd_hist = histogram.iloc[-1]

    # Bollinger Bands
    bb_upper, bb_middle, bb_lower = _bollinger_bands(close)

    # ATR
    atr_14 = _atr(high, low, close, 14).iloc[-1]

    # OBV
    obv = _obv(close, volume).iloc[-1]

    # Stochastic Oscillator
    stoch_k, stoch_d = _stochastic(high, low, close)

    def _safe(val: float) -> float | None:
        if val is None or (isinstance(val, float) and np.isnan(val)):
            return None
        return round(float(val), 4)

    return TechnicalIndicators(
        sma_5=_safe(sma_5),
        sma_20=_safe(sma_20),
        sma_60=_safe(sma_60),
        ema_12=_safe(ema_12),
        ema_26=_safe(ema_26),
        rsi_14=_safe(rsi_14),
        macd=_safe(macd_val),
        macd_signal=_safe(macd_sig),
        macd_histogram=_safe(macd_hist),
        bollinger_upper=_safe(bb_upper.iloc[-1]),
        bollinger_middle=_safe(bb_middle.iloc[-1]),
        bollinger_lower=_safe(bb_lower.iloc[-1]),
        atr_14=_safe(atr_14),
        obv=_safe(obv),
        stoch_k=_safe(stoch_k.iloc[-1]),
        stoch_d=_safe(stoch_d.iloc[-1]),
    )
