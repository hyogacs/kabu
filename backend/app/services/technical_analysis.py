"""Technical analysis calculations."""

import numpy as np
import pandas as pd
import ta

from app.models.stock import TechnicalIndicators


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
    rsi_indicator = ta.momentum.RSIIndicator(close=close, window=14)
    rsi_14 = rsi_indicator.rsi().iloc[-1]

    # MACD
    macd_indicator = ta.trend.MACD(close=close)
    macd_val = macd_indicator.macd().iloc[-1]
    macd_signal = macd_indicator.macd_signal().iloc[-1]
    macd_hist = macd_indicator.macd_diff().iloc[-1]

    # Bollinger Bands
    bb = ta.volatility.BollingerBands(close=close, window=20, window_dev=2)
    bb_upper = bb.bollinger_hband().iloc[-1]
    bb_middle = bb.bollinger_mavg().iloc[-1]
    bb_lower = bb.bollinger_lband().iloc[-1]

    # ATR
    atr_indicator = ta.volatility.AverageTrueRange(
        high=high, low=low, close=close, window=14
    )
    atr_14 = atr_indicator.average_true_range().iloc[-1]

    # OBV
    obv_indicator = ta.volume.OnBalanceVolumeIndicator(close=close, volume=volume)
    obv = obv_indicator.on_balance_volume().iloc[-1]

    # Stochastic Oscillator
    stoch = ta.momentum.StochasticOscillator(
        high=high, low=low, close=close, window=14, smooth_window=3
    )
    stoch_k = stoch.stoch().iloc[-1]
    stoch_d = stoch.stoch_signal().iloc[-1]

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
        macd_signal=_safe(macd_signal),
        macd_histogram=_safe(macd_hist),
        bollinger_upper=_safe(bb_upper),
        bollinger_middle=_safe(bb_middle),
        bollinger_lower=_safe(bb_lower),
        atr_14=_safe(atr_14),
        obv=_safe(obv),
        stoch_k=_safe(stoch_k),
        stoch_d=_safe(stoch_d),
    )
