"""交易策略引擎

基于市场状况和技术分析，为每支股票生成可操作的交易策略。
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
    """为指定股票生成多种交易策略"""

    def generate_strategies(self, symbol: str) -> list[TradingStrategy]:
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
        self, symbol: str, df: pd.DataFrame, ind: TechnicalIndicators,
        price: float, atr: float,
    ) -> TradingStrategy | None:
        actions = []

        if ind.sma_5 and ind.sma_20 and ind.sma_60:
            if ind.sma_5 > ind.sma_20 > ind.sma_60:
                actions.append(
                    StrategyAction(
                        action="BUY",
                        reason="均线多头排列（SMA5 > SMA20 > SMA60），回踩20日均线可考虑入场做多。",
                        entry_price=round(ind.sma_20, 2),
                        stop_loss=round(ind.sma_60, 2),
                        take_profit=round(price + 3 * atr, 2),
                        position_size_pct=15.0,
                    )
                )
                actions.append(
                    StrategyAction(
                        action="HOLD",
                        reason="已持仓者可将止损上移至20日均线，随价格上涨逐步提高止损位。",
                    )
                )
            elif ind.sma_5 < ind.sma_20 < ind.sma_60:
                actions.append(
                    StrategyAction(
                        action="SELL",
                        reason="均线空头排列（SMA5 < SMA20 < SMA60），建议清仓多单或考虑做空。",
                        stop_loss=round(ind.sma_20, 2),
                        take_profit=round(price - 3 * atr, 2),
                        position_size_pct=10.0,
                    )
                )
            else:
                actions.append(
                    StrategyAction(
                        action="WATCH",
                        reason="均线未形成明确排列，建议等待趋势确认后再入场。",
                    )
                )
        elif ind.sma_5 and ind.sma_20:
            if ind.sma_5 > ind.sma_20:
                actions.append(
                    StrategyAction(
                        action="BUY",
                        reason="短期均线上穿中期均线，出现早期看涨信号。",
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
                        reason="短期均线下穿中期均线，出现早期看跌信号。",
                        stop_loss=round(price + 2 * atr, 2),
                        position_size_pct=10.0,
                    )
                )

        return TradingStrategy(
            symbol=symbol,
            strategy_type=StrategyType.TREND_FOLLOWING,
            name="趋势跟踪策略",
            description="基于均线排列判断趋势方向，在趋势回调时顺势入场，止损设置在关键均线位置。",
            actions=actions,
            risk_level="MEDIUM",
            timeframe="MEDIUM",
            generated_at=datetime.now(timezone.utc),
        )

    def _mean_reversion(
        self, symbol: str, df: pd.DataFrame, ind: TechnicalIndicators,
        price: float, atr: float,
    ) -> TradingStrategy | None:
        actions = []

        if ind.bollinger_lower and ind.bollinger_upper and ind.bollinger_middle:
            bb_range = ind.bollinger_upper - ind.bollinger_lower
            if bb_range > 0:
                position = (price - ind.bollinger_lower) / bb_range

                if position < 0.2:
                    actions.append(
                        StrategyAction(
                            action="BUY",
                            reason=f"股价接近布林带下轨（{ind.bollinger_lower:.2f}），"
                            f"预期向中轨（{ind.bollinger_middle:.2f}）回归。",
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
                            reason=f"股价接近布林带上轨（{ind.bollinger_upper:.2f}），"
                            f"预期向中轨（{ind.bollinger_middle:.2f}）回落。",
                            stop_loss=round(ind.bollinger_upper + atr, 2),
                            take_profit=round(ind.bollinger_middle, 2),
                            position_size_pct=10.0,
                        )
                    )
                else:
                    actions.append(
                        StrategyAction(
                            action="WATCH",
                            reason="股价处于布林带中间区域，等待触及上下轨时再操作。",
                        )
                    )

        if ind.rsi_14 is not None:
            if ind.rsi_14 < 30:
                actions.append(
                    StrategyAction(
                        action="BUY",
                        reason=f"RSI 为 {ind.rsi_14:.1f}（超卖），历史上该水平容易出现反弹。",
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
                        reason=f"RSI 为 {ind.rsi_14:.1f}（超买），建议获利了结或考虑做空。",
                        stop_loss=round(price + 2 * atr, 2),
                        take_profit=round(price - 2 * atr, 2),
                        position_size_pct=8.0,
                    )
                )

        return TradingStrategy(
            symbol=symbol,
            strategy_type=StrategyType.MEAN_REVERSION,
            name="均值回归策略",
            description="利用布林带和RSI识别超买超卖极端状态，在偏离均值时逆向操作，预期价格回归中枢。",
            actions=actions,
            risk_level="MEDIUM",
            timeframe="SHORT",
            generated_at=datetime.now(timezone.utc),
        )

    def _momentum(
        self, symbol: str, df: pd.DataFrame, ind: TechnicalIndicators,
        price: float, atr: float,
    ) -> TradingStrategy | None:
        actions = []

        if ind.macd is not None and ind.macd_signal is not None:
            if ind.macd > ind.macd_signal and ind.macd_histogram and ind.macd_histogram > 0:
                if ind.rsi_14 and 40 < ind.rsi_14 < 70:
                    actions.append(
                        StrategyAction(
                            action="BUY",
                            reason=(
                                f"MACD 金叉且柱状图持续放大，"
                                f"RSI 为 {ind.rsi_14:.1f}，动能确认且未超买。"
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
                            reason="MACD 看涨但 RSI 未确认，等待指标共振后再入场。",
                        )
                    )
            elif ind.macd < ind.macd_signal and ind.macd_histogram and ind.macd_histogram < 0:
                actions.append(
                    StrategyAction(
                        action="SELL",
                        reason="MACD 死叉且柱状图为负，下行动能增强。",
                        stop_loss=round(price + 2 * atr, 2),
                        position_size_pct=10.0,
                    )
                )

        if len(df) >= 10:
            roc_10 = (price - float(df["Close"].iloc[-10])) / float(df["Close"].iloc[-10]) * 100
            if roc_10 > 8:
                actions.append(
                    StrategyAction(
                        action="BUY",
                        reason=f"10日涨幅达 +{roc_10:.1f}%，上涨动能强劲，可跟随趋势并设紧密止损。",
                        stop_loss=round(price - 1.5 * atr, 2),
                        take_profit=round(price + 2 * atr, 2),
                        position_size_pct=8.0,
                    )
                )
            elif roc_10 < -8:
                actions.append(
                    StrategyAction(
                        action="SELL",
                        reason=f"10日跌幅达 {roc_10:.1f}%，下跌动能较强，切勿盲目抄底。",
                        stop_loss=round(price + 1.5 * atr, 2),
                        position_size_pct=8.0,
                    )
                )

        return TradingStrategy(
            symbol=symbol,
            strategy_type=StrategyType.MOMENTUM,
            name="动量策略",
            description="追踪强势方向性行情，利用MACD交叉和变化率确认动能方向，在多指标共振时入场。",
            actions=actions,
            risk_level="HIGH",
            timeframe="SHORT",
            generated_at=datetime.now(timezone.utc),
        )

    def _breakout(
        self, symbol: str, df: pd.DataFrame, ind: TechnicalIndicators,
        price: float, atr: float,
    ) -> TradingStrategy | None:
        actions = []

        if len(df) >= 20:
            high_20 = float(df["High"].iloc[-20:].max())
            low_20 = float(df["Low"].iloc[-20:].min())
            range_20 = high_20 - low_20

            if price > high_20 * 0.98:
                actions.append(
                    StrategyAction(
                        action="BUY",
                        reason=f"股价逼近20日高点（{high_20:.2f}），突破后可能引发向上加速行情。",
                        entry_price=round(high_20 * 1.005, 2),
                        stop_loss=round(high_20 - atr, 2),
                        take_profit=round(high_20 + range_20 * 0.5, 2),
                        position_size_pct=10.0,
                    )
                )

            if price < low_20 * 1.02:
                actions.append(
                    StrategyAction(
                        action="SELL",
                        reason=f"股价逼近20日低点（{low_20:.2f}），跌破后可能引发进一步下跌。",
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
                            f"股价处于整理区间。"
                            f"上方阻力位 {high_20:.2f}（距 {dist_to_high_pct:.1f}%），"
                            f"下方支撑位 {low_20:.2f}（距 {dist_to_low_pct:.1f}%）。"
                            f"建议在关键位置设置提醒。"
                        ),
                    )
                )

        return TradingStrategy(
            symbol=symbol,
            strategy_type=StrategyType.BREAKOUT,
            name="突破策略",
            description="监控股价是否突破关键支撑/阻力位，在确认突破后入场，止损设在突破位下方。",
            actions=actions,
            risk_level="HIGH",
            timeframe="SHORT",
            generated_at=datetime.now(timezone.utc),
        )

    def _swing_trade(
        self, symbol: str, df: pd.DataFrame, ind: TechnicalIndicators,
        price: float, atr: float,
    ) -> TradingStrategy | None:
        actions = []

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
                    reason=f"波段做多：{buy_signals}/4 个指标看涨，"
                    f"建议持有5-15个交易日，目标收益2-3倍ATR。",
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
                    reason=f"波段做空：{sell_signals}/4 个指标看跌，"
                    f"建议清仓多单，可考虑做空持有5-15个交易日。",
                    stop_loss=round(price + 2 * atr, 2),
                    take_profit=round(price - 3 * atr, 2),
                    position_size_pct=10.0,
                )
            )
        else:
            actions.append(
                StrategyAction(
                    action="HOLD",
                    reason=f"信号混合（看多：{buy_signals}，看空：{sell_signals}），"
                    f"等待3个以上指标同向确认后再操作。",
                )
            )

        actions.append(
            StrategyAction(
                action="HOLD",
                reason=(
                    f"风控提示：使用ATR止损（每股 {atr:.2f}），"
                    f"单笔波段交易不超过总仓位的2%。"
                ),
            )
        )

        return TradingStrategy(
            symbol=symbol,
            strategy_type=StrategyType.SWING_TRADE,
            name="波段交易策略",
            description="多指标综合评分的中线持仓策略，需3个以上指标共振方可入场，持仓5-15个交易日，采用ATR风控管理。",
            actions=actions,
            risk_level="MEDIUM",
            timeframe="MEDIUM",
            generated_at=datetime.now(timezone.utc),
        )


strategy_engine = StrategyEngine()
