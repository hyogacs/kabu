"""Trading strategy engine.

Generates actionable trading strategies based on market conditions
and technical analysis for each stock.
"""

import logging
from datetime import datetime, timezone

import pandas as pd

from app.models.stock import (
    Signal,
    StrategyAction,
    StrategyType,
    TechnicalIndicators,
    TradingStrategy,
)
from app.services.stock_data import fetch_history_df
from app.services.technical_analysis import calculate_indicators

logger = logging.getLogger(__name__)


class StrategyEngine:
    """Generates multiple trading strategies for a given stock."""

    def generate_strategies(self, symbol: str) -> list[TradingStrategy]:
        """Generate all applicable strategies for a symbol."""
        df = fetch_history_df(symbol, period="6mo")
        if df.empty or len(df) < 30:
            return []

        indicators = calculate_indicators(df)
        current_price = float(df["Close"].iloc[-1])
        atr = indicators.atr_14 or (current_price * 0.02)

        strategies = []

        trend_strategy = self._trend_following(symbol, df, indicators, current_price, atr)
        if trend_strategy:
            strategies.append(trend_strategy)

        mr_strategy = self._mean_reversion(symbol, df, indicators, current_price, atr)
        if mr_strategy:
            strategies.append(mr_strategy)

        mom_strategy = self._momentum(symbol, df, indicators, current_price, atr)
        if mom_strategy:
            strategies.append(mom_strategy)

        bo_strategy = self._breakout(symbol, df, indicators, current_price, atr)
        if bo_strategy:
            strategies.append(bo_strategy)

        swing_strategy = self._swing_trade(symbol, df, indicators, current_price, atr)
        if swing_strategy:
            strategies.append(swing_strategy)

        return strategies

    def _trend_following(
        self,
        symbol: str,
        df: pd.DataFrame,
        ind: TechnicalIndicators,
        price: float,
        atr: float,
    ) -> TradingStrategy | None:
        """Trend following: ride the prevailing trend with MA crossovers."""
        actions = []

        if ind.sma_5 and ind.sma_20 and ind.sma_60:
            if ind.sma_5 > ind.sma_20 > ind.sma_60:
                # Strong uptrend
                actions.append(
                    StrategyAction(
                        action="BUY",
                        reason="All MAs aligned bullish (SMA5 > SMA20 > SMA60). Enter long on pullback to SMA20.",
                        entry_price=round(ind.sma_20, 2),
                        stop_loss=round(ind.sma_60, 2),
                        take_profit=round(price + 3 * atr, 2),
                        position_size_pct=15.0,
                    )
                )
                actions.append(
                    StrategyAction(
                        action="HOLD",
                        reason="If already long, trail stop to SMA20. Move stop-loss up as price advances.",
                    )
                )
            elif ind.sma_5 < ind.sma_20 < ind.sma_60:
                # Strong downtrend
                actions.append(
                    StrategyAction(
                        action="SELL",
                        reason="All MAs aligned bearish (SMA5 < SMA20 < SMA60). Exit longs, consider short.",
                        stop_loss=round(ind.sma_20, 2),
                        take_profit=round(price - 3 * atr, 2),
                        position_size_pct=10.0,
                    )
                )
            else:
                actions.append(
                    StrategyAction(
                        action="WATCH",
                        reason="MAs are not aligned. Wait for clear trend confirmation before entering.",
                    )
                )
        elif ind.sma_5 and ind.sma_20:
            if ind.sma_5 > ind.sma_20:
                actions.append(
                    StrategyAction(
                        action="BUY",
                        reason="Short-term MA crossed above medium-term MA. Early bullish signal.",
                        entry_price=round(price, 2),
                        stop_loss=round(price - 2 * atr, 2),
                        take_profit=round(price + 3 * atr, 2),
                        position_size_pct=10.0,
                    )
                )
            else:
                actions.append(
                    StrategyAction(
                        action="SELL",
                        reason="Short-term MA crossed below medium-term MA. Early bearish signal.",
                        stop_loss=round(price + 2 * atr, 2),
                        position_size_pct=10.0,
                    )
                )

        return TradingStrategy(
            symbol=symbol,
            strategy_type=StrategyType.TREND_FOLLOWING,
            name="Trend Following Strategy",
            description=(
                "Follows the prevailing trend using moving average alignment. "
                "Enters on pullbacks in the direction of the trend, with stops "
                "placed at key MA levels."
            ),
            actions=actions,
            risk_level="MEDIUM",
            timeframe="MEDIUM",
            generated_at=datetime.now(timezone.utc),
        )

    def _mean_reversion(
        self,
        symbol: str,
        df: pd.DataFrame,
        ind: TechnicalIndicators,
        price: float,
        atr: float,
    ) -> TradingStrategy | None:
        """Mean reversion: trade bounces off Bollinger Bands."""
        actions = []

        if ind.bollinger_lower and ind.bollinger_upper and ind.bollinger_middle:
            bb_range = ind.bollinger_upper - ind.bollinger_lower
            if bb_range > 0:
                position = (price - ind.bollinger_lower) / bb_range

                if position < 0.2:
                    actions.append(
                        StrategyAction(
                            action="BUY",
                            reason=f"Price near lower Bollinger Band ({ind.bollinger_lower:.2f}). "
                            f"Expect mean reversion to middle band ({ind.bollinger_middle:.2f}).",
                            entry_price=round(ind.bollinger_lower, 2),
                            stop_loss=round(ind.bollinger_lower - atr, 2),
                            take_profit=round(ind.bollinger_middle, 2),
                            position_size_pct=10.0,
                        )
                    )
                elif position > 0.8:
                    actions.append(
                        StrategyAction(
                            action="SELL",
                            reason=f"Price near upper Bollinger Band ({ind.bollinger_upper:.2f}). "
                            f"Expect mean reversion to middle band ({ind.bollinger_middle:.2f}).",
                            stop_loss=round(ind.bollinger_upper + atr, 2),
                            take_profit=round(ind.bollinger_middle, 2),
                            position_size_pct=10.0,
                        )
                    )
                else:
                    actions.append(
                        StrategyAction(
                            action="WATCH",
                            reason="Price within normal Bollinger Band range. Wait for extremes.",
                        )
                    )

        if ind.rsi_14 is not None:
            if ind.rsi_14 < 30:
                actions.append(
                    StrategyAction(
                        action="BUY",
                        reason=f"RSI at {ind.rsi_14:.1f} (oversold). Historical tendency to bounce from this level.",
                        entry_price=round(price, 2),
                        stop_loss=round(price - 2 * atr, 2),
                        take_profit=round(price + 2 * atr, 2),
                        position_size_pct=8.0,
                    )
                )
            elif ind.rsi_14 > 70:
                actions.append(
                    StrategyAction(
                        action="SELL",
                        reason=f"RSI at {ind.rsi_14:.1f} (overbought). Consider taking profits or shorting.",
                        stop_loss=round(price + 2 * atr, 2),
                        take_profit=round(price - 2 * atr, 2),
                        position_size_pct=8.0,
                    )
                )

        return TradingStrategy(
            symbol=symbol,
            strategy_type=StrategyType.MEAN_REVERSION,
            name="Mean Reversion Strategy",
            description=(
                "Trades against extremes using Bollinger Bands and RSI. "
                "Buys oversold conditions and sells overbought conditions, "
                "expecting price to revert to the mean."
            ),
            actions=actions,
            risk_level="MEDIUM",
            timeframe="SHORT",
            generated_at=datetime.now(timezone.utc),
        )

    def _momentum(
        self,
        symbol: str,
        df: pd.DataFrame,
        ind: TechnicalIndicators,
        price: float,
        atr: float,
    ) -> TradingStrategy | None:
        """Momentum: follow strong directional moves with MACD and RSI."""
        actions = []

        if ind.macd is not None and ind.macd_signal is not None:
            if ind.macd > ind.macd_signal and ind.macd_histogram and ind.macd_histogram > 0:
                if ind.rsi_14 and 40 < ind.rsi_14 < 70:
                    actions.append(
                        StrategyAction(
                            action="BUY",
                            reason=(
                                f"MACD bullish with increasing histogram. "
                                f"RSI at {ind.rsi_14:.1f} confirms momentum without being overbought."
                            ),
                            entry_price=round(price, 2),
                            stop_loss=round(price - 2 * atr, 2),
                            take_profit=round(price + 4 * atr, 2),
                            position_size_pct=12.0,
                        )
                    )
                else:
                    actions.append(
                        StrategyAction(
                            action="WATCH",
                            reason="MACD bullish but RSI not confirming. Wait for alignment.",
                        )
                    )
            elif ind.macd < ind.macd_signal and ind.macd_histogram and ind.macd_histogram < 0:
                actions.append(
                    StrategyAction(
                        action="SELL",
                        reason="MACD bearish crossover with negative histogram. Momentum shifting downward.",
                        stop_loss=round(price + 2 * atr, 2),
                        position_size_pct=10.0,
                    )
                )

        # Check price rate of change
        if len(df) >= 10:
            roc_10 = (price - float(df["Close"].iloc[-10])) / float(df["Close"].iloc[-10]) * 100
            if roc_10 > 8:
                actions.append(
                    StrategyAction(
                        action="BUY",
                        reason=f"Strong upward momentum: +{roc_10:.1f}% in 10 days. Trail stop tightly.",
                        stop_loss=round(price - 1.5 * atr, 2),
                        take_profit=round(price + 2 * atr, 2),
                        position_size_pct=8.0,
                    )
                )
            elif roc_10 < -8:
                actions.append(
                    StrategyAction(
                        action="SELL",
                        reason=f"Strong downward momentum: {roc_10:.1f}% in 10 days. Avoid catching falling knife.",
                        stop_loss=round(price + 1.5 * atr, 2),
                        position_size_pct=8.0,
                    )
                )

        return TradingStrategy(
            symbol=symbol,
            strategy_type=StrategyType.MOMENTUM,
            name="Momentum Strategy",
            description=(
                "Follows strong directional moves using MACD crossovers "
                "and rate of change. Enters when momentum is confirmed "
                "by multiple indicators."
            ),
            actions=actions,
            risk_level="HIGH",
            timeframe="SHORT",
            generated_at=datetime.now(timezone.utc),
        )

    def _breakout(
        self,
        symbol: str,
        df: pd.DataFrame,
        ind: TechnicalIndicators,
        price: float,
        atr: float,
    ) -> TradingStrategy | None:
        """Breakout: trade price breaking key support/resistance levels."""
        actions = []

        if len(df) >= 20:
            high_20 = float(df["High"].iloc[-20:].max())
            low_20 = float(df["Low"].iloc[-20:].min())
            range_20 = high_20 - low_20

            # Near resistance breakout
            if price > high_20 * 0.98:
                actions.append(
                    StrategyAction(
                        action="BUY",
                        reason=f"Price approaching 20-day high ({high_20:.2f}). "
                        f"Break above could trigger breakout rally.",
                        entry_price=round(high_20 * 1.005, 2),
                        stop_loss=round(high_20 - atr, 2),
                        take_profit=round(high_20 + range_20 * 0.5, 2),
                        position_size_pct=10.0,
                    )
                )

            # Near support breakdown
            if price < low_20 * 1.02:
                actions.append(
                    StrategyAction(
                        action="SELL",
                        reason=f"Price approaching 20-day low ({low_20:.2f}). "
                        f"Break below could trigger further selling.",
                        stop_loss=round(low_20 + atr, 2),
                        take_profit=round(low_20 - range_20 * 0.5, 2),
                        position_size_pct=10.0,
                    )
                )

            if not actions:
                dist_to_high_pct = (high_20 - price) / price * 100
                dist_to_low_pct = (price - low_20) / price * 100
                actions.append(
                    StrategyAction(
                        action="WATCH",
                        reason=(
                            f"Price in consolidation range. "
                            f"Resistance at {high_20:.2f} ({dist_to_high_pct:.1f}% away), "
                            f"Support at {low_20:.2f} ({dist_to_low_pct:.1f}% away). "
                            f"Set alerts at these levels."
                        ),
                    )
                )

        return TradingStrategy(
            symbol=symbol,
            strategy_type=StrategyType.BREAKOUT,
            name="Breakout Strategy",
            description=(
                "Watches for price breaking through key support/resistance levels. "
                "Enters on confirmed breakouts with volume, with stops placed "
                "just below the breakout level."
            ),
            actions=actions,
            risk_level="HIGH",
            timeframe="SHORT",
            generated_at=datetime.now(timezone.utc),
        )

    def _swing_trade(
        self,
        symbol: str,
        df: pd.DataFrame,
        ind: TechnicalIndicators,
        price: float,
        atr: float,
    ) -> TradingStrategy | None:
        """Swing trade: multi-day holds using combined signals."""
        actions = []

        # Composite scoring for swing entry
        buy_signals = 0
        sell_signals = 0

        if ind.rsi_14:
            if ind.rsi_14 < 40:
                buy_signals += 1
            elif ind.rsi_14 > 60:
                sell_signals += 1

        if ind.macd_histogram:
            if ind.macd_histogram > 0:
                buy_signals += 1
            else:
                sell_signals += 1

        if ind.sma_5 and ind.sma_20:
            if ind.sma_5 > ind.sma_20:
                buy_signals += 1
            else:
                sell_signals += 1

        if ind.stoch_k and ind.stoch_d:
            if ind.stoch_k < 30:
                buy_signals += 1
            elif ind.stoch_k > 70:
                sell_signals += 1

        if buy_signals >= 3:
            actions.append(
                StrategyAction(
                    action="BUY",
                    reason=f"Swing buy: {buy_signals}/4 indicators bullish. "
                    f"Hold for 5-15 trading days targeting 2-3x ATR profit.",
                    entry_price=round(price, 2),
                    stop_loss=round(price - 2 * atr, 2),
                    take_profit=round(price + 3 * atr, 2),
                    position_size_pct=12.0,
                )
            )
        elif sell_signals >= 3:
            actions.append(
                StrategyAction(
                    action="SELL",
                    reason=f"Swing sell: {sell_signals}/4 indicators bearish. "
                    f"Exit longs, consider short for 5-15 days.",
                    stop_loss=round(price + 2 * atr, 2),
                    take_profit=round(price - 3 * atr, 2),
                    position_size_pct=10.0,
                )
            )
        else:
            actions.append(
                StrategyAction(
                    action="HOLD",
                    reason=f"Mixed signals (Buy: {buy_signals}, Sell: {sell_signals}). "
                    f"Wait for clearer setup with 3+ aligned indicators.",
                )
            )

        # Position management
        actions.append(
            StrategyAction(
                action="HOLD",
                reason=(
                    f"Risk management: Use ATR-based stops ({atr:.2f} per share). "
                    f"Never risk more than 2% of portfolio on a single swing trade."
                ),
            )
        )

        return TradingStrategy(
            symbol=symbol,
            strategy_type=StrategyType.SWING_TRADE,
            name="Swing Trading Strategy",
            description=(
                "Multi-day position strategy using composite indicator scoring. "
                "Requires 3+ indicators to align before entry. Holds for 5-15 "
                "trading days with ATR-based risk management."
            ),
            actions=actions,
            risk_level="MEDIUM",
            timeframe="MEDIUM",
            generated_at=datetime.now(timezone.utc),
        )


# Singleton
strategy_engine = StrategyEngine()
