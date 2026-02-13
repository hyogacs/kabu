"""AI-powered stock analysis engine.

Uses a multi-factor scoring model combining technical indicators,
trend analysis, and pattern recognition to generate buy/sell signals.
"""

import logging
from datetime import datetime, timezone

import numpy as np
import pandas as pd

from app.models.stock import AIAnalysis, Signal, TechnicalIndicators
from app.services.stock_data import fetch_history_df
from app.services.technical_analysis import calculate_indicators

logger = logging.getLogger(__name__)


class AIAnalyzer:
    """Multi-factor AI analysis engine for stock evaluation."""

    # Weights for each scoring component (total = 1.0)
    WEIGHTS = {
        "trend": 0.25,
        "momentum": 0.20,
        "mean_reversion": 0.15,
        "volume": 0.10,
        "volatility": 0.10,
        "pattern": 0.20,
    }

    def analyze(self, symbol: str) -> AIAnalysis | None:
        """Run full AI analysis on a stock symbol."""
        df = fetch_history_df(symbol, period="6mo")
        if df.empty or len(df) < 30:
            logger.warning(f"Insufficient data for {symbol}")
            return None

        indicators = calculate_indicators(df)
        close = df["Close"]
        current_price = float(close.iloc[-1])

        scores = {}
        reasons = []

        # 1. Trend Score
        trend_score, trend_reasons = self._score_trend(indicators, current_price)
        scores["trend"] = trend_score
        reasons.extend(trend_reasons)

        # 2. Momentum Score
        mom_score, mom_reasons = self._score_momentum(indicators)
        scores["momentum"] = mom_score
        reasons.extend(mom_reasons)

        # 3. Mean Reversion Score
        mr_score, mr_reasons = self._score_mean_reversion(indicators, current_price)
        scores["mean_reversion"] = mr_score
        reasons.extend(mr_reasons)

        # 4. Volume Score
        vol_score, vol_reasons = self._score_volume(df)
        scores["volume"] = vol_score
        reasons.extend(vol_reasons)

        # 5. Volatility Score
        vola_score, vola_reasons = self._score_volatility(indicators, current_price)
        scores["volatility"] = vola_score
        reasons.extend(vola_reasons)

        # 6. Pattern Score
        pat_score, pat_reasons = self._score_pattern(df)
        scores["pattern"] = pat_score
        reasons.extend(pat_reasons)

        # Weighted composite score: -1.0 (strong sell) to +1.0 (strong buy)
        composite = sum(
            scores[k] * self.WEIGHTS[k] for k in self.WEIGHTS
        )

        signal = self._score_to_signal(composite)
        confidence = min(abs(composite), 1.0)

        # Calculate support/resistance
        support = self._find_support(df)
        resistance = self._find_resistance(df)
        atr = indicators.atr_14 or (current_price * 0.02)

        stop_loss = round(current_price - 2 * atr, 2)
        target_price = round(current_price + 3 * atr, 2)
        rr = round((target_price - current_price) / (current_price - stop_loss), 2) if current_price > stop_loss else None

        summary = self._generate_summary(symbol, signal, confidence, reasons)

        return AIAnalysis(
            symbol=symbol,
            signal=signal,
            confidence=round(confidence, 2),
            summary=summary,
            reasons=reasons[:6],  # Top 6 reasons
            support_price=support,
            resistance_price=resistance,
            stop_loss=stop_loss,
            target_price=target_price,
            risk_reward_ratio=rr,
            indicators=indicators,
            analyzed_at=datetime.now(timezone.utc),
        )

    def _score_trend(
        self, ind: TechnicalIndicators, price: float
    ) -> tuple[float, list[str]]:
        """Score based on moving average trends."""
        score = 0.0
        reasons = []

        if ind.sma_5 and ind.sma_20:
            if ind.sma_5 > ind.sma_20:
                score += 0.4
                reasons.append("Short-term MA above medium-term MA (bullish crossover)")
            else:
                score -= 0.4
                reasons.append("Short-term MA below medium-term MA (bearish crossover)")

        if ind.sma_20 and ind.sma_60:
            if ind.sma_20 > ind.sma_60:
                score += 0.3
                reasons.append("Medium-term trend is bullish (SMA20 > SMA60)")
            else:
                score -= 0.3
                reasons.append("Medium-term trend is bearish (SMA20 < SMA60)")

        if ind.sma_20:
            if price > ind.sma_20:
                score += 0.3
                reasons.append(f"Price above SMA20 ({ind.sma_20:.2f})")
            else:
                score -= 0.3
                reasons.append(f"Price below SMA20 ({ind.sma_20:.2f})")

        return max(-1, min(1, score)), reasons

    def _score_momentum(
        self, ind: TechnicalIndicators
    ) -> tuple[float, list[str]]:
        """Score based on RSI, MACD, Stochastic."""
        score = 0.0
        reasons = []

        # RSI
        if ind.rsi_14 is not None:
            if ind.rsi_14 < 30:
                score += 0.5
                reasons.append(f"RSI oversold ({ind.rsi_14:.1f}) - potential rebound")
            elif ind.rsi_14 < 40:
                score += 0.2
            elif ind.rsi_14 > 70:
                score -= 0.5
                reasons.append(f"RSI overbought ({ind.rsi_14:.1f}) - potential pullback")
            elif ind.rsi_14 > 60:
                score -= 0.1

        # MACD
        if ind.macd_histogram is not None:
            if ind.macd_histogram > 0:
                score += 0.3
                if ind.macd and ind.macd_signal and ind.macd > ind.macd_signal:
                    reasons.append("MACD bullish crossover")
            else:
                score -= 0.3
                if ind.macd and ind.macd_signal and ind.macd < ind.macd_signal:
                    reasons.append("MACD bearish crossover")

        # Stochastic
        if ind.stoch_k is not None and ind.stoch_d is not None:
            if ind.stoch_k < 20 and ind.stoch_d < 20:
                score += 0.2
                reasons.append("Stochastic in oversold zone")
            elif ind.stoch_k > 80 and ind.stoch_d > 80:
                score -= 0.2
                reasons.append("Stochastic in overbought zone")

        return max(-1, min(1, score)), reasons

    def _score_mean_reversion(
        self, ind: TechnicalIndicators, price: float
    ) -> tuple[float, list[str]]:
        """Score based on Bollinger Bands position."""
        score = 0.0
        reasons = []

        if ind.bollinger_lower and ind.bollinger_upper and ind.bollinger_middle:
            bb_range = ind.bollinger_upper - ind.bollinger_lower
            if bb_range > 0:
                bb_position = (price - ind.bollinger_lower) / bb_range

                if bb_position < 0.1:
                    score += 0.8
                    reasons.append("Price near lower Bollinger Band - potential bounce")
                elif bb_position < 0.3:
                    score += 0.3
                elif bb_position > 0.9:
                    score -= 0.8
                    reasons.append("Price near upper Bollinger Band - potential retreat")
                elif bb_position > 0.7:
                    score -= 0.3

        return max(-1, min(1, score)), reasons

    def _score_volume(self, df: pd.DataFrame) -> tuple[float, list[str]]:
        """Score based on volume analysis."""
        score = 0.0
        reasons = []

        if len(df) < 20:
            return score, reasons

        recent_vol = df["Volume"].iloc[-5:].mean()
        avg_vol = df["Volume"].iloc[-20:].mean()

        if avg_vol > 0:
            vol_ratio = recent_vol / avg_vol
            price_change = (
                float(df["Close"].iloc[-1]) - float(df["Close"].iloc[-5])
            ) / float(df["Close"].iloc[-5])

            if vol_ratio > 1.5 and price_change > 0:
                score += 0.6
                reasons.append(
                    f"Volume surge ({vol_ratio:.1f}x avg) with price increase"
                )
            elif vol_ratio > 1.5 and price_change < 0:
                score -= 0.6
                reasons.append(
                    f"Volume surge ({vol_ratio:.1f}x avg) with price decline"
                )
            elif vol_ratio < 0.5:
                reasons.append("Low volume - reduced conviction in current trend")

        return max(-1, min(1, score)), reasons

    def _score_volatility(
        self, ind: TechnicalIndicators, price: float
    ) -> tuple[float, list[str]]:
        """Score based on ATR and volatility regime."""
        score = 0.0
        reasons = []

        if ind.atr_14 and price > 0:
            atr_pct = ind.atr_14 / price * 100
            if atr_pct > 5:
                score -= 0.3
                reasons.append(f"High volatility (ATR {atr_pct:.1f}% of price)")
            elif atr_pct < 1:
                score += 0.1
                reasons.append("Low volatility - stable price action")

        return max(-1, min(1, score)), reasons

    def _score_pattern(self, df: pd.DataFrame) -> tuple[float, list[str]]:
        """Score based on candlestick and price patterns."""
        score = 0.0
        reasons = []

        if len(df) < 10:
            return score, reasons

        closes = df["Close"].values
        opens = df["Open"].values
        highs = df["High"].values
        lows = df["Low"].values

        # Higher highs and higher lows (uptrend)
        recent_highs = highs[-5:]
        recent_lows = lows[-5:]
        if all(recent_highs[i] >= recent_highs[i - 1] for i in range(1, len(recent_highs))):
            score += 0.4
            reasons.append("Consecutive higher highs detected (uptrend)")
        elif all(recent_highs[i] <= recent_highs[i - 1] for i in range(1, len(recent_highs))):
            score -= 0.4
            reasons.append("Consecutive lower highs detected (downtrend)")

        # Consecutive positive/negative closes
        last_3_changes = [
            closes[-i] - opens[-i] for i in range(1, min(4, len(df)))
        ]
        if all(c > 0 for c in last_3_changes):
            score += 0.3
            reasons.append("3 consecutive bullish candles")
        elif all(c < 0 for c in last_3_changes):
            score -= 0.3
            reasons.append("3 consecutive bearish candles")

        # Hammer/Doji detection on last candle
        body = abs(closes[-1] - opens[-1])
        total_range = highs[-1] - lows[-1]
        if total_range > 0 and body / total_range < 0.1:
            reasons.append("Doji candle detected - potential trend reversal")
            # Doji is neutral, direction depends on context
            if closes[-1] < df["Close"].rolling(20).mean().iloc[-1]:
                score += 0.2  # Bullish in downtrend
            else:
                score -= 0.2  # Bearish in uptrend

        return max(-1, min(1, score)), reasons

    def _score_to_signal(self, score: float) -> Signal:
        if score >= 0.5:
            return Signal.STRONG_BUY
        elif score >= 0.2:
            return Signal.BUY
        elif score <= -0.5:
            return Signal.STRONG_SELL
        elif score <= -0.2:
            return Signal.SELL
        return Signal.HOLD

    def _find_support(self, df: pd.DataFrame) -> float | None:
        if len(df) < 20:
            return None
        recent_lows = df["Low"].iloc[-20:]
        return round(float(recent_lows.min()), 2)

    def _find_resistance(self, df: pd.DataFrame) -> float | None:
        if len(df) < 20:
            return None
        recent_highs = df["High"].iloc[-20:]
        return round(float(recent_highs.max()), 2)

    def _generate_summary(
        self, symbol: str, signal: Signal, confidence: float, reasons: list[str]
    ) -> str:
        signal_text = {
            Signal.STRONG_BUY: "Strong Buy",
            Signal.BUY: "Buy",
            Signal.HOLD: "Hold",
            Signal.SELL: "Sell",
            Signal.STRONG_SELL: "Strong Sell",
        }
        top_reasons = "; ".join(reasons[:3]) if reasons else "Mixed signals"
        return (
            f"[{symbol}] Signal: {signal_text[signal]} "
            f"(Confidence: {confidence:.0%}). "
            f"Key factors: {top_reasons}."
        )


# Singleton
ai_analyzer = AIAnalyzer()
