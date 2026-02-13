import type { AIAnalysis } from "../types";
import { signalLabel, formatNumber } from "../utils/format";

interface Props {
  analysis: AIAnalysis;
  currency: string;
}

export function AnalysisPanel({ analysis, currency }: Props) {
  const prefix = currency === "JPY" ? "¥" : "$";
  const d = currency === "JPY" ? 0 : 2;

  const confidencePct = Math.round(analysis.confidence * 100);
  const fillColor = analysis.signal.includes("BUY")
    ? "var(--green)" : analysis.signal.includes("SELL")
    ? "var(--red)" : "var(--yellow)";

  return (
    <div className="card">
      <div className="card-title">AI 智能分析</div>

      <div className="signal-row">
        <span className={`signal-badge signal-${analysis.signal}`}>
          {signalLabel(analysis.signal)}
        </span>
        <div className="confidence-bar">
          <div className="confidence-fill" style={{ width: `${confidencePct}%`, background: fillColor }} />
        </div>
        <span className="confidence-text">置信度 {confidencePct}%</span>
      </div>

      <div className="analysis-summary">{analysis.summary}</div>

      <div className="analysis-meta">
        <div className="meta-item">
          <span className="meta-label">目标价</span>
          <span className="meta-value change-positive">
            {analysis.target_price ? `${prefix}${formatNumber(analysis.target_price, d)}` : "-"}
          </span>
        </div>
        <div className="meta-item">
          <span className="meta-label">止损价</span>
          <span className="meta-value change-negative">
            {analysis.stop_loss ? `${prefix}${formatNumber(analysis.stop_loss, d)}` : "-"}
          </span>
        </div>
        <div className="meta-item">
          <span className="meta-label">支撑位</span>
          <span className="meta-value">
            {analysis.support_price ? `${prefix}${formatNumber(analysis.support_price, d)}` : "-"}
          </span>
        </div>
        <div className="meta-item">
          <span className="meta-label">阻力位</span>
          <span className="meta-value">
            {analysis.resistance_price ? `${prefix}${formatNumber(analysis.resistance_price, d)}` : "-"}
          </span>
        </div>
      </div>

      {analysis.risk_reward_ratio && (
        <div style={{ fontSize: 13, color: "var(--text-secondary)", marginBottom: 12 }}>
          风险收益比: <strong style={{ color: "var(--text-primary)" }}>{analysis.risk_reward_ratio.toFixed(2)}</strong>
        </div>
      )}

      <div className="card-title" style={{ marginTop: 4 }}>关键因素</div>
      <ul className="reasons-list">
        {analysis.reasons.map((reason, i) => (
          <li key={i}>{reason}</li>
        ))}
      </ul>

      <div className="card-title" style={{ marginTop: 16 }}>技术指标</div>
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
          <div className="indicator-value">{formatNumber(analysis.indicators.sma_20, d)}</div>
        </div>
        <div className="indicator-item">
          <div className="indicator-label">EMA(12)</div>
          <div className="indicator-value">{formatNumber(analysis.indicators.ema_12, d)}</div>
        </div>
        <div className="indicator-item">
          <div className="indicator-label">布林上轨</div>
          <div className="indicator-value">{formatNumber(analysis.indicators.bollinger_upper, d)}</div>
        </div>
        <div className="indicator-item">
          <div className="indicator-label">布林下轨</div>
          <div className="indicator-value">{formatNumber(analysis.indicators.bollinger_lower, d)}</div>
        </div>
        <div className="indicator-item">
          <div className="indicator-label">ATR(14)</div>
          <div className="indicator-value">{formatNumber(analysis.indicators.atr_14, d)}</div>
        </div>
        <div className="indicator-item">
          <div className="indicator-label">KDJ %K</div>
          <div className="indicator-value">{formatNumber(analysis.indicators.stoch_k, 1)}</div>
        </div>
        <div className="indicator-item">
          <div className="indicator-label">KDJ %D</div>
          <div className="indicator-value">{formatNumber(analysis.indicators.stoch_d, 1)}</div>
        </div>
      </div>
    </div>
  );
}
