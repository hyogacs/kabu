"""Stock data models."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class Market(str, Enum):
    US = "US"
    JP = "JP"


class Signal(str, Enum):
    STRONG_BUY = "STRONG_BUY"
    BUY = "BUY"
    HOLD = "HOLD"
    SELL = "SELL"
    STRONG_SELL = "STRONG_SELL"


class StockQuote(BaseModel):
    symbol: str
    name: str
    market: Market
    currency: str
    current_price: float
    previous_close: float
    open_price: float
    day_high: float
    day_low: float
    volume: int
    change: float
    change_percent: float
    timestamp: datetime


class TechnicalIndicators(BaseModel):
    sma_5: float | None = None
    sma_20: float | None = None
    sma_60: float | None = None
    ema_12: float | None = None
    ema_26: float | None = None
    rsi_14: float | None = None
    macd: float | None = None
    macd_signal: float | None = None
    macd_histogram: float | None = None
    bollinger_upper: float | None = None
    bollinger_middle: float | None = None
    bollinger_lower: float | None = None
    atr_14: float | None = None
    obv: float | None = None
    stoch_k: float | None = None
    stoch_d: float | None = None


class AIAnalysis(BaseModel):
    symbol: str
    signal: Signal
    confidence: float  # 0.0 - 1.0
    summary: str
    reasons: list[str]
    support_price: float | None = None
    resistance_price: float | None = None
    stop_loss: float | None = None
    target_price: float | None = None
    risk_reward_ratio: float | None = None
    indicators: TechnicalIndicators
    analyzed_at: datetime


class StrategyType(str, Enum):
    TREND_FOLLOWING = "TREND_FOLLOWING"
    MEAN_REVERSION = "MEAN_REVERSION"
    MOMENTUM = "MOMENTUM"
    BREAKOUT = "BREAKOUT"
    SWING_TRADE = "SWING_TRADE"


class StrategyAction(BaseModel):
    action: str  # "BUY", "SELL", "HOLD", "WATCH"
    reason: str
    entry_price: float | None = None
    stop_loss: float | None = None
    take_profit: float | None = None
    position_size_pct: float | None = None  # % of portfolio


class TradingStrategy(BaseModel):
    symbol: str
    strategy_type: StrategyType
    name: str
    description: str
    actions: list[StrategyAction]
    risk_level: str  # "LOW", "MEDIUM", "HIGH"
    timeframe: str  # "SHORT", "MEDIUM", "LONG"
    generated_at: datetime


class HistoricalBar(BaseModel):
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int


class Sentiment(str, Enum):
    POSITIVE = "POSITIVE"
    NEGATIVE = "NEGATIVE"
    NEUTRAL = "NEUTRAL"


class NewsItem(BaseModel):
    title: str
    source: str
    published_at: str
    url: str
    sentiment: Sentiment
    score: float  # -1.0 to 1.0


class NewsSentiment(BaseModel):
    symbol: str
    overall_score: float  # -1.0 to 1.0
    overall_sentiment: Sentiment
    positive_count: int
    negative_count: int
    neutral_count: int
    news: list[NewsItem]
    analyzed_at: datetime


class StockDetail(BaseModel):
    quote: StockQuote
    indicators: TechnicalIndicators
    analysis: AIAnalysis
    strategies: list[TradingStrategy]
    history: list[HistoricalBar]
    news_sentiment: NewsSentiment | None = None
