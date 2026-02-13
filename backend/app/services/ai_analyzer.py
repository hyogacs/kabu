"""AI 智能股票分析引擎

使用多因子评分模型，综合技术指标、趋势分析和形态识别，生成买卖信号。
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
    """多因子 AI 分析引擎"""

    WEIGHTS = {
        "trend": 0.25,
        "momentum": 0.20,
        "mean_reversion": 0.15,
        "volume": 0.10,
        "volatility": 0.10,
        "pattern": 0.20,
    }

    def analyze(self, symbol: str) -> AIAnalysis | None:
        df = fetch_history_df(symbol, period="6mo")
        if df.empty or len(df) < 30:
            logger.warning(f"数据不足，无法分析 {symbol}")
            return None

        indicators = calculate_indicators(df)
        close = df["Close"]
        current_price = float(close.iloc[-1])

        scores = {}
        reasons = []

        trend_score, trend_reasons = self._score_trend(indicators, current_price)
        scores["trend"] = trend_score
        reasons.extend(trend_reasons)

        mom_score, mom_reasons = self._score_momentum(indicators)
        scores["momentum"] = mom_score
        reasons.extend(mom_reasons)

        mr_score, mr_reasons = self._score_mean_reversion(indicators, current_price)
        scores["mean_reversion"] = mr_score
        reasons.extend(mr_reasons)

        vol_score, vol_reasons = self._score_volume(df)
        scores["volume"] = vol_score
        reasons.extend(vol_reasons)

        vola_score, vola_reasons = self._score_volatility(indicators, current_price)
        scores["volatility"] = vola_score
        reasons.extend(vola_reasons)

        pat_score, pat_reasons = self._score_pattern(df)
        scores["pattern"] = pat_score
        reasons.extend(pat_reasons)

        composite = sum(scores[k] * self.WEIGHTS[k] for k in self.WEIGHTS)

        signal = self._score_to_signal(composite)
        confidence = min(abs(composite), 1.0)

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
            reasons=reasons[:6],
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
        score = 0.0
        reasons = []

        if ind.sma_5 and ind.sma_20:
            if ind.sma_5 > ind.sma_20:
                score += 0.4
                reasons.append("短期均线上穿中期均线，形成金叉（看涨）")
            else:
                score -= 0.4
                reasons.append("短期均线下穿中期均线，形成死叉（看跌）")

        if ind.sma_20 and ind.sma_60:
            if ind.sma_20 > ind.sma_60:
                score += 0.3
                reasons.append("中期趋势向上（SMA20 > SMA60）")
            else:
                score -= 0.3
                reasons.append("中期趋势向下（SMA20 < SMA60）")

        if ind.sma_20:
            if price > ind.sma_20:
                score += 0.3
                reasons.append(f"股价位于20日均线上方（{ind.sma_20:.2f}），多头排列")
            else:
                score -= 0.3
                reasons.append(f"股价位于20日均线下方（{ind.sma_20:.2f}），空头排列")

        return max(-1, min(1, score)), reasons

    def _score_momentum(
        self, ind: TechnicalIndicators
    ) -> tuple[float, list[str]]:
        score = 0.0
        reasons = []

        if ind.rsi_14 is not None:
            if ind.rsi_14 < 30:
                score += 0.5
                reasons.append(f"RSI 进入超卖区域（{ind.rsi_14:.1f}），存在反弹机会")
            elif ind.rsi_14 < 40:
                score += 0.2
            elif ind.rsi_14 > 70:
                score -= 0.5
                reasons.append(f"RSI 进入超买区域（{ind.rsi_14:.1f}），存在回调风险")
            elif ind.rsi_14 > 60:
                score -= 0.1

        if ind.macd_histogram is not None:
            if ind.macd_histogram > 0:
                score += 0.3
                if ind.macd and ind.macd_signal and ind.macd > ind.macd_signal:
                    reasons.append("MACD 金叉，动能向上增强")
            else:
                score -= 0.3
                if ind.macd and ind.macd_signal and ind.macd < ind.macd_signal:
                    reasons.append("MACD 死叉，动能向下转弱")

        if ind.stoch_k is not None and ind.stoch_d is not None:
            if ind.stoch_k < 20 and ind.stoch_d < 20:
                score += 0.2
                reasons.append("KDJ 指标进入超卖区域，关注反弹信号")
            elif ind.stoch_k > 80 and ind.stoch_d > 80:
                score -= 0.2
                reasons.append("KDJ 指标进入超买区域，注意获利了结")

        return max(-1, min(1, score)), reasons

    def _score_mean_reversion(
        self, ind: TechnicalIndicators, price: float
    ) -> tuple[float, list[str]]:
        score = 0.0
        reasons = []

        if ind.bollinger_lower and ind.bollinger_upper and ind.bollinger_middle:
            bb_range = ind.bollinger_upper - ind.bollinger_lower
            if bb_range > 0:
                bb_position = (price - ind.bollinger_lower) / bb_range

                if bb_position < 0.1:
                    score += 0.8
                    reasons.append("股价触及布林带下轨，存在反弹空间")
                elif bb_position < 0.3:
                    score += 0.3
                elif bb_position > 0.9:
                    score -= 0.8
                    reasons.append("股价触及布林带上轨，存在回落压力")
                elif bb_position > 0.7:
                    score -= 0.3

        return max(-1, min(1, score)), reasons

    def _score_volume(self, df: pd.DataFrame) -> tuple[float, list[str]]:
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
                reasons.append(f"放量上涨（成交量为均量的 {vol_ratio:.1f} 倍），多头动能充沛")
            elif vol_ratio > 1.5 and price_change < 0:
                score -= 0.6
                reasons.append(f"放量下跌（成交量为均量的 {vol_ratio:.1f} 倍），空头压力较大")
            elif vol_ratio < 0.5:
                reasons.append("成交量萎缩，当前趋势缺乏量能支撑")

        return max(-1, min(1, score)), reasons

    def _score_volatility(
        self, ind: TechnicalIndicators, price: float
    ) -> tuple[float, list[str]]:
        score = 0.0
        reasons = []

        if ind.atr_14 and price > 0:
            atr_pct = ind.atr_14 / price * 100
            if atr_pct > 5:
                score -= 0.3
                reasons.append(f"波动率偏高（ATR 占股价 {atr_pct:.1f}%），风险较大")
            elif atr_pct < 1:
                score += 0.1
                reasons.append("波动率较低，价格走势稳定")

        return max(-1, min(1, score)), reasons

    def _score_pattern(self, df: pd.DataFrame) -> tuple[float, list[str]]:
        score = 0.0
        reasons = []

        if len(df) < 10:
            return score, reasons

        closes = df["Close"].values
        opens = df["Open"].values
        highs = df["High"].values
        lows = df["Low"].values

        recent_highs = highs[-5:]
        recent_lows = lows[-5:]
        if all(recent_highs[i] >= recent_highs[i - 1] for i in range(1, len(recent_highs))):
            score += 0.4
            reasons.append("连续创出更高高点，上升趋势明确")
        elif all(recent_highs[i] <= recent_highs[i - 1] for i in range(1, len(recent_highs))):
            score -= 0.4
            reasons.append("连续创出更低高点，下降趋势明确")

        last_3_changes = [
            closes[-i] - opens[-i] for i in range(1, min(4, len(df)))
        ]
        if all(c > 0 for c in last_3_changes):
            score += 0.3
            reasons.append("连续3根阳线，短期做多情绪浓厚")
        elif all(c < 0 for c in last_3_changes):
            score -= 0.3
            reasons.append("连续3根阴线，短期抛压较重")

        body = abs(closes[-1] - opens[-1])
        total_range = highs[-1] - lows[-1]
        if total_range > 0 and body / total_range < 0.1:
            reasons.append("出现十字星形态，可能发生趋势反转")
            if closes[-1] < df["Close"].rolling(20).mean().iloc[-1]:
                score += 0.2
            else:
                score -= 0.2

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
        return round(float(df["Low"].iloc[-20:].min()), 2)

    def _find_resistance(self, df: pd.DataFrame) -> float | None:
        if len(df) < 20:
            return None
        return round(float(df["High"].iloc[-20:].max()), 2)

    def _generate_summary(
        self, symbol: str, signal: Signal, confidence: float, reasons: list[str]
    ) -> str:
        signal_text = {
            Signal.STRONG_BUY: "强烈买入",
            Signal.BUY: "买入",
            Signal.HOLD: "持有观望",
            Signal.SELL: "卖出",
            Signal.STRONG_SELL: "强烈卖出",
        }
        top_reasons = "；".join(reasons[:3]) if reasons else "信号混合"
        return (
            f"[{symbol}] 综合评级：{signal_text[signal]}"
            f"（置信度 {confidence:.0%}）。"
            f"主要依据：{top_reasons}。"
        )


ai_analyzer = AIAnalyzer()
