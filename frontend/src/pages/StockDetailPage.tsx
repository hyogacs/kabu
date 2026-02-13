import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import type { StockDetail } from "../types";
import { getStockDetail } from "../services/api";
import { formatPrice, formatVolume, formatPercent, formatNumber, signalLabel } from "../utils/format";
import { PriceChart } from "../components/PriceChart";
import { StrategyPanel } from "../components/StrategyPanel";
import { NewsSentimentPanel } from "../components/NewsSentiment";

export function StockDetailPage() {
  const { symbol } = useParams<{ symbol: string }>();
  const navigate = useNavigate();
  const [detail, setDetail] = useState<StockDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!symbol) return;
    setLoading(true);
    setError(null);
    getStockDetail(symbol)
      .then(setDetail)
      .catch(() => setError("无法获取股票数据，请检查网络连接后重试"))
      .finally(() => setLoading(false));
  }, [symbol]);

  if (loading) {
    return (
      <div className="detail-page">
        <div className="detail-top-bar">
          <button className="back-btn" onClick={() => navigate("/")}>← 返回列表</button>
        </div>
        <div className="loading">
          <div className="spinner" />
          <p>正在加载 {symbol} 数据...</p>
        </div>
      </div>
    );
  }

  if (error || !detail) {
    return (
      <div className="detail-page">
        <div className="detail-top-bar">
          <button className="back-btn" onClick={() => navigate("/")}>← 返回列表</button>
        </div>
        <div className="card">
          <div className="empty-state">
            <h3>加载失败</h3>
            <p>{error ?? "未找到该股票数据"}</p>
          </div>
        </div>
      </div>
    );
  }

  const { quote, analysis, strategies, history, indicators } = detail;
  const currency = quote.currency;
  const prefix = currency === "JPY" ? "¥" : "$";
  const d = currency === "JPY" ? 0 : 2;
  const isPositive = quote.change >= 0;
  const changeClass = isPositive ? "change-positive" : "change-negative";

  const confidencePct = Math.round(analysis.confidence * 100);
  const fillColor = analysis.signal.includes("BUY")
    ? "var(--green)" : analysis.signal.includes("SELL")
    ? "var(--red)" : "var(--yellow)";

  return (
    <div className="detail-page">
      {/* Top Bar */}
      <div className="detail-top-bar">
        <button className="back-btn" onClick={() => navigate("/")}>← 返回列表</button>
        <div className="detail-top-right">
          <span className={`market-badge ${quote.market}`}>{quote.market}</span>
          <span className="detail-timestamp">
            更新于 {new Date(quote.timestamp).toLocaleString("zh-CN")}
          </span>
        </div>
      </div>

      {/* Stock Header */}
      <div className="detail-header">
        <div className="detail-header-left">
          <h1 className="detail-symbol">{quote.symbol}</h1>
          <span className="detail-name">{quote.name}</span>
          <span className={`signal-badge signal-${analysis.signal}`} style={{ marginLeft: 12 }}>
            {signalLabel(analysis.signal)}
          </span>
        </div>
        <div className="detail-header-right">
          <div className="detail-price">{formatPrice(quote.current_price, currency)}</div>
          <div className={`detail-change ${changeClass}`}>
            {isPositive ? "+" : ""}{currency === "JPY" ? quote.change.toFixed(0) : quote.change.toFixed(2)}
            {" "}({formatPercent(quote.change_percent)})
          </div>
        </div>
      </div>

      {/* Key Metrics Bar */}
      <div className="metrics-bar">
        <div className="metric-item">
          <span className="metric-label">开盘价</span>
          <span className="metric-value">{formatPrice(quote.open_price, currency)}</span>
        </div>
        <div className="metric-item">
          <span className="metric-label">前收盘</span>
          <span className="metric-value">{formatPrice(quote.previous_close, currency)}</span>
        </div>
        <div className="metric-item">
          <span className="metric-label">最高</span>
          <span className="metric-value change-positive">{formatPrice(quote.day_high, currency)}</span>
        </div>
        <div className="metric-item">
          <span className="metric-label">最低</span>
          <span className="metric-value change-negative">{formatPrice(quote.day_low, currency)}</span>
        </div>
        <div className="metric-item">
          <span className="metric-label">成交量</span>
          <span className="metric-value">{formatVolume(quote.volume)}</span>
        </div>
        <div className="metric-item">
          <span className="metric-label">振幅</span>
          <span className="metric-value">
            {quote.previous_close
              ? (((quote.day_high - quote.day_low) / quote.previous_close) * 100).toFixed(2) + "%"
              : "-"}
          </span>
        </div>
      </div>

      {/* Price Chart */}
      <PriceChart quote={quote} history={history} />

      {/* Detail Grid: Analysis + Strategies */}
      <div className="detail-grid">
        {/* Left Column: AI Analysis */}
        <div className="detail-col">
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
          </div>

          {/* Technical Indicators - Full */}
          <div className="card">
            <div className="card-title">技术指标详情</div>

            <div className="indicator-section">
              <div className="indicator-section-title">移动平均线</div>
              <div className="indicators-grid-detail">
                <div className="indicator-item-detail">
                  <div className="indicator-label">SMA(5)</div>
                  <div className="indicator-value">{formatNumber(indicators.sma_5, d)}</div>
                  {indicators.sma_5 && (
                    <div className={`indicator-vs ${quote.current_price >= indicators.sma_5 ? "change-positive" : "change-negative"}`}>
                      {quote.current_price >= indicators.sma_5 ? "价格在上方" : "价格在下方"}
                    </div>
                  )}
                </div>
                <div className="indicator-item-detail">
                  <div className="indicator-label">SMA(20)</div>
                  <div className="indicator-value">{formatNumber(indicators.sma_20, d)}</div>
                  {indicators.sma_20 && (
                    <div className={`indicator-vs ${quote.current_price >= indicators.sma_20 ? "change-positive" : "change-negative"}`}>
                      {quote.current_price >= indicators.sma_20 ? "价格在上方" : "价格在下方"}
                    </div>
                  )}
                </div>
                <div className="indicator-item-detail">
                  <div className="indicator-label">SMA(60)</div>
                  <div className="indicator-value">{formatNumber(indicators.sma_60, d)}</div>
                  {indicators.sma_60 && (
                    <div className={`indicator-vs ${quote.current_price >= indicators.sma_60 ? "change-positive" : "change-negative"}`}>
                      {quote.current_price >= indicators.sma_60 ? "价格在上方" : "价格在下方"}
                    </div>
                  )}
                </div>
                <div className="indicator-item-detail">
                  <div className="indicator-label">EMA(12)</div>
                  <div className="indicator-value">{formatNumber(indicators.ema_12, d)}</div>
                </div>
                <div className="indicator-item-detail">
                  <div className="indicator-label">EMA(26)</div>
                  <div className="indicator-value">{formatNumber(indicators.ema_26, d)}</div>
                </div>
              </div>
            </div>

            <div className="indicator-section">
              <div className="indicator-section-title">震荡指标</div>
              <div className="indicators-grid-detail">
                <div className="indicator-item-detail">
                  <div className="indicator-label">RSI(14)</div>
                  <div className="indicator-value" style={{
                    color: indicators.rsi_14
                      ? indicators.rsi_14 > 70 ? "var(--red)"
                      : indicators.rsi_14 < 30 ? "var(--green)"
                      : "var(--text-primary)"
                      : "var(--text-muted)"
                  }}>
                    {formatNumber(indicators.rsi_14, 1)}
                  </div>
                  {indicators.rsi_14 && (
                    <div className="indicator-vs" style={{
                      color: indicators.rsi_14 > 70 ? "var(--red)"
                        : indicators.rsi_14 < 30 ? "var(--green)"
                        : "var(--text-muted)"
                    }}>
                      {indicators.rsi_14 > 70 ? "超买区域" : indicators.rsi_14 < 30 ? "超卖区域" : "中性区域"}
                    </div>
                  )}
                </div>
                <div className="indicator-item-detail">
                  <div className="indicator-label">MACD</div>
                  <div className="indicator-value" style={{
                    color: indicators.macd_histogram
                      ? indicators.macd_histogram > 0 ? "var(--green)" : "var(--red)"
                      : "var(--text-muted)"
                  }}>
                    {formatNumber(indicators.macd, 4)}
                  </div>
                </div>
                <div className="indicator-item-detail">
                  <div className="indicator-label">MACD 信号线</div>
                  <div className="indicator-value">{formatNumber(indicators.macd_signal, 4)}</div>
                </div>
                <div className="indicator-item-detail">
                  <div className="indicator-label">MACD 柱状图</div>
                  <div className="indicator-value" style={{
                    color: indicators.macd_histogram
                      ? indicators.macd_histogram > 0 ? "var(--green)" : "var(--red)"
                      : "var(--text-muted)"
                  }}>
                    {formatNumber(indicators.macd_histogram, 4)}
                  </div>
                  {indicators.macd_histogram != null && (
                    <div className={`indicator-vs ${indicators.macd_histogram > 0 ? "change-positive" : "change-negative"}`}>
                      {indicators.macd_histogram > 0 ? "多头动能" : "空头动能"}
                    </div>
                  )}
                </div>
                <div className="indicator-item-detail">
                  <div className="indicator-label">KDJ %K</div>
                  <div className="indicator-value">{formatNumber(indicators.stoch_k, 1)}</div>
                </div>
                <div className="indicator-item-detail">
                  <div className="indicator-label">KDJ %D</div>
                  <div className="indicator-value">{formatNumber(indicators.stoch_d, 1)}</div>
                </div>
              </div>
            </div>

            <div className="indicator-section">
              <div className="indicator-section-title">波动率 & 成交量</div>
              <div className="indicators-grid-detail">
                <div className="indicator-item-detail">
                  <div className="indicator-label">布林上轨</div>
                  <div className="indicator-value">{formatNumber(indicators.bollinger_upper, d)}</div>
                </div>
                <div className="indicator-item-detail">
                  <div className="indicator-label">布林中轨</div>
                  <div className="indicator-value">{formatNumber(indicators.bollinger_middle, d)}</div>
                </div>
                <div className="indicator-item-detail">
                  <div className="indicator-label">布林下轨</div>
                  <div className="indicator-value">{formatNumber(indicators.bollinger_lower, d)}</div>
                </div>
                <div className="indicator-item-detail">
                  <div className="indicator-label">ATR(14)</div>
                  <div className="indicator-value">{formatNumber(indicators.atr_14, d)}</div>
                </div>
                <div className="indicator-item-detail">
                  <div className="indicator-label">OBV</div>
                  <div className="indicator-value">{indicators.obv != null ? formatVolume(indicators.obv) : "-"}</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Strategies + News */}
        <div className="detail-col">
          <StrategyPanel strategies={strategies} currency={currency} />
          {detail.news_sentiment && (
            <NewsSentimentPanel sentiment={detail.news_sentiment} />
          )}
        </div>
      </div>
    </div>
  );
}
