import type { AIAnalysis } from "../types";
import { signalLabel, formatNumber } from "../utils/format";

interface Props {
  analysis: AIAnalysis;
  currency: string;
}

export function AnalysisPanel({ analysis, currency }: Props) {
  const pricePrefix = currency === "JPY" ? "¥" : "$";
  const decimals = currency === "JPY" ? 0 : 2;

  return (
    <div className="card">
      <div className="card-title">AI Analysis</div>

      <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
        <span className={`signal-badge signal-${analysis.signal}`}>
          {signalLabel(analysis.signal)}
        </span>
        <span style={{ fontSize: 13, color: "var(--text-muted)" }}>
          Confidence: {(analysis.confidence * 100).toFixed(0)}%
        </span>
      </div>

      <p className="analysis-summary">{analysis.summary}</p>

      <div className="analysis-meta">
        <div className="meta-item">
          <span className="meta-label">Target</span>
          <span className="meta-value change-positive">
            {analysis.target_price ? `${pricePrefix}${formatNumber(analysis.target_price, decimals)}` : "-"}
          </span>
        </div>
        <div className="meta-item">
          <span className="meta-label">Stop Loss</span>
          <span className="meta-value change-negative">
            {analysis.stop_loss ? `${pricePrefix}${formatNumber(analysis.stop_loss, decimals)}` : "-"}
          </span>
        </div>
        <div className="meta-item">
          <span className="meta-label">Support</span>
          <span className="meta-value">
            {analysis.support_price ? `${pricePrefix}${formatNumber(analysis.support_price, decimals)}` : "-"}
          </span>
        </div>
        <div className="meta-item">
          <span className="meta-label">Resistance</span>
          <span className="meta-value">
            {analysis.resistance_price ? `${pricePrefix}${formatNumber(analysis.resistance_price, decimals)}` : "-"}
          </span>
        </div>
      </div>

      {analysis.risk_reward_ratio && (
        <div style={{ fontSize: 13, color: "var(--text-secondary)", marginBottom: 8 }}>
          Risk/Reward Ratio: <strong>{analysis.risk_reward_ratio.toFixed(2)}</strong>
        </div>
      )}

      <div className="card-title" style={{ marginTop: 12 }}>Key Factors</div>
      <ul className="reasons-list">
        {analysis.reasons.map((reason, i) => (
          <li key={i}>{reason}</li>
        ))}
      </ul>

      <div className="card-title" style={{ marginTop: 16 }}>Technical Indicators</div>
      <div className="indicators-grid">
        <div className="indicator-item">
          <div className="indicator-label">RSI(14)</div>
          <div className="indicator-value" style={{
            color: analysis.indicators.rsi_14
              ? analysis.indicators.rsi_14 > 70 ? "var(--red)"
              : analysis.indicators.rsi_14 < 30 ? "var(--green)"
              : "var(--text-primary)"
              : "var(--text-muted)"
          }}>
            {formatNumber(analysis.indicators.rsi_14, 1)}
          </div>
        </div>
        <div className="indicator-item">
          <div className="indicator-label">MACD</div>
          <div className="indicator-value" style={{
            color: analysis.indicators.macd_histogram
              ? analysis.indicators.macd_histogram > 0 ? "var(--green)" : "var(--red)"
              : "var(--text-muted)"
          }}>
            {formatNumber(analysis.indicators.macd, 4)}
          </div>
        </div>
        <div className="indicator-item">
          <div className="indicator-label">SMA(20)</div>
          <div className="indicator-value">{formatNumber(analysis.indicators.sma_20, decimals)}</div>
        </div>
        <div className="indicator-item">
          <div className="indicator-label">EMA(12)</div>
          <div className="indicator-value">{formatNumber(analysis.indicators.ema_12, decimals)}</div>
        </div>
        <div className="indicator-item">
          <div className="indicator-label">BB Upper</div>
          <div className="indicator-value">{formatNumber(analysis.indicators.bollinger_upper, decimals)}</div>
        </div>
        <div className="indicator-item">
          <div className="indicator-label">BB Lower</div>
          <div className="indicator-value">{formatNumber(analysis.indicators.bollinger_lower, decimals)}</div>
        </div>
        <div className="indicator-item">
          <div className="indicator-label">ATR(14)</div>
          <div className="indicator-value">{formatNumber(analysis.indicators.atr_14, decimals)}</div>
        </div>
        <div className="indicator-item">
          <div className="indicator-label">Stoch %K</div>
          <div className="indicator-value">{formatNumber(analysis.indicators.stoch_k, 1)}</div>
        </div>
        <div className="indicator-item">
          <div className="indicator-label">Stoch %D</div>
          <div className="indicator-value">{formatNumber(analysis.indicators.stoch_d, 1)}</div>
        </div>
      </div>
    </div>
  );
}
