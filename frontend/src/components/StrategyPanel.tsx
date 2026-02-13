import type { TradingStrategy } from "../types";

interface Props {
  strategies: TradingStrategy[];
  currency: string;
}

const strategyTypeLabels: Record<string, string> = {
  TREND_FOLLOWING: "Trend Following",
  MEAN_REVERSION: "Mean Reversion",
  MOMENTUM: "Momentum",
  BREAKOUT: "Breakout",
  SWING_TRADE: "Swing Trade",
};

export function StrategyPanel({ strategies, currency }: Props) {
  const pricePrefix = currency === "JPY" ? "¥" : "$";
  const decimals = currency === "JPY" ? 0 : 2;

  const fmtPrice = (val: number | null): string => {
    if (val == null) return "-";
    return `${pricePrefix}${val.toFixed(decimals)}`;
  };

  return (
    <div className="card">
      <div className="card-title">Trading Strategies</div>

      {strategies.map((strategy, idx) => (
        <div key={idx} className="strategy-card">
          <div className="strategy-header">
            <span className="strategy-name">
              {strategyTypeLabels[strategy.strategy_type] ?? strategy.name}
            </span>
            <div style={{ display: "flex", gap: 6 }}>
              <span className={`risk-badge risk-${strategy.risk_level}`}>
                {strategy.risk_level}
              </span>
              <span style={{
                fontSize: 11,
                padding: "2px 8px",
                borderRadius: 4,
                background: "rgba(139, 92, 246, 0.15)",
                color: "var(--purple)",
                fontWeight: 600,
              }}>
                {strategy.timeframe}
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
                {action.action}
              </div>
              <div className="action-reason">{action.reason}</div>
              {(action.entry_price || action.stop_loss || action.take_profit) && (
                <div className="action-levels">
                  {action.entry_price && <span>Entry: {fmtPrice(action.entry_price)}</span>}
                  {action.stop_loss && <span>SL: {fmtPrice(action.stop_loss)}</span>}
                  {action.take_profit && <span>TP: {fmtPrice(action.take_profit)}</span>}
                  {action.position_size_pct && <span>Size: {action.position_size_pct}%</span>}
                </div>
              )}
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}
