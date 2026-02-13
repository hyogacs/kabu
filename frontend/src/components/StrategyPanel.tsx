import type { TradingStrategy } from "../types";

interface Props {
  strategies: TradingStrategy[];
  currency: string;
}

const strategyNames: Record<string, string> = {
  TREND_FOLLOWING: "趋势跟踪",
  MEAN_REVERSION: "均值回归",
  MOMENTUM: "动量策略",
  BREAKOUT: "突破策略",
  SWING_TRADE: "波段交易",
};

const riskLabels: Record<string, string> = {
  LOW: "低风险",
  MEDIUM: "中风险",
  HIGH: "高风险",
};

const timeLabels: Record<string, string> = {
  SHORT: "短线",
  MEDIUM: "中线",
  LONG: "长线",
};

const actionLabels: Record<string, string> = {
  BUY: "买入",
  SELL: "卖出",
  HOLD: "持有",
  WATCH: "观望",
};

export function StrategyPanel({ strategies, currency }: Props) {
  const prefix = currency === "JPY" ? "¥" : "$";
  const d = currency === "JPY" ? 0 : 2;
  const fmtPrice = (val: number | null): string => {
    if (val == null) return "-";
    return `${prefix}${val.toFixed(d)}`;
  };

  return (
    <div className="card">
      <div className="card-title">交易策略</div>

      {strategies.map((strategy, idx) => (
        <div key={idx} className="strategy-card">
          <div className="strategy-header">
            <span className="strategy-name">
              {strategyNames[strategy.strategy_type] ?? strategy.name}
            </span>
            <div className="strategy-badges">
              <span className={`risk-badge risk-${strategy.risk_level}`}>
                {riskLabels[strategy.risk_level] ?? strategy.risk_level}
              </span>
              <span className="time-badge">
                {timeLabels[strategy.timeframe] ?? strategy.timeframe}
              </span>
            </div>
          </div>

          <div className="strategy-desc">{strategy.description}</div>

          {strategy.actions.map((action, aIdx) => (
            <div key={aIdx} className={`action-item ${action.action}`}>
              <div className="action-label" style={{
                color: action.action === "BUY" ? "var(--green)"
                  : action.action === "SELL" ? "var(--red)"
                  : action.action === "HOLD" ? "var(--yellow)"
                  : "var(--purple)"
              }}>
                {actionLabels[action.action] ?? action.action}
              </div>
              <div className="action-reason">{action.reason}</div>
              {(action.entry_price || action.stop_loss || action.take_profit) && (
                <div className="action-levels">
                  {action.entry_price && <span>入场: {fmtPrice(action.entry_price)}</span>}
                  {action.stop_loss && <span>止损: {fmtPrice(action.stop_loss)}</span>}
                  {action.take_profit && <span>止盈: {fmtPrice(action.take_profit)}</span>}
                  {action.position_size_pct && <span>仓位: {action.position_size_pct}%</span>}
                </div>
              )}
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}
