export type Market = "US" | "JP";

export type Signal = "STRONG_BUY" | "BUY" | "HOLD" | "SELL" | "STRONG_SELL";

export interface StockQuote {
  symbol: string;
  name: string;
  market: Market;
  currency: string;
  current_price: number;
  previous_close: number;
  open_price: number;
  day_high: number;
  day_low: number;
  volume: number;
  change: number;
  change_percent: number;
  timestamp: string;
}

export interface TechnicalIndicators {
  sma_5: number | null;
  sma_20: number | null;
  sma_60: number | null;
  ema_12: number | null;
  ema_26: number | null;
  rsi_14: number | null;
  macd: number | null;
  macd_signal: number | null;
  macd_histogram: number | null;
  bollinger_upper: number | null;
  bollinger_middle: number | null;
  bollinger_lower: number | null;
  atr_14: number | null;
  obv: number | null;
  stoch_k: number | null;
  stoch_d: number | null;
}

export interface AIAnalysis {
  symbol: string;
  signal: Signal;
  confidence: number;
  summary: string;
  reasons: string[];
  support_price: number | null;
  resistance_price: number | null;
  stop_loss: number | null;
  target_price: number | null;
  risk_reward_ratio: number | null;
  indicators: TechnicalIndicators;
  analyzed_at: string;
}

export interface StrategyAction {
  action: string;
  reason: string;
  entry_price: number | null;
  stop_loss: number | null;
  take_profit: number | null;
  position_size_pct: number | null;
}

export interface TradingStrategy {
  symbol: string;
  strategy_type: string;
  name: string;
  description: string;
  actions: StrategyAction[];
  risk_level: string;
  timeframe: string;
  generated_at: string;
}

export interface HistoricalBar {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface StockDetail {
  quote: StockQuote;
  indicators: TechnicalIndicators;
  analysis: AIAnalysis;
  strategies: TradingStrategy[];
  history: HistoricalBar[];
}
