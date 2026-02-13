import { useState, useEffect, useCallback } from "react";
import type { Market, StockQuote, StockDetail } from "./types";
import { useStockWebSocket } from "./hooks/useWebSocket";
import { getStocks, getStockDetail } from "./services/api";
import { StockTable } from "./components/StockTable";
import { PriceChart } from "./components/PriceChart";
import { AnalysisPanel } from "./components/AnalysisPanel";
import { StrategyPanel } from "./components/StrategyPanel";

type MarketFilter = "ALL" | Market;

export default function App() {
  const [marketFilter, setMarketFilter] = useState<MarketFilter>("ALL");
  const [quotes, setQuotes] = useState<StockQuote[]>([]);
  const [selectedSymbol, setSelectedSymbol] = useState<string | null>(null);
  const [detail, setDetail] = useState<StockDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);

  const { quotes: wsQuotes, connected } = useStockWebSocket();

  useEffect(() => {
    setLoading(true);
    getStocks()
      .then(setQuotes)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (wsQuotes.length > 0) {
      setQuotes(wsQuotes);
    }
  }, [wsQuotes]);

  const handleSelect = useCallback((symbol: string) => {
    setSelectedSymbol(symbol);
    setDetailLoading(true);
    getStockDetail(symbol)
      .then(setDetail)
      .catch(() => setDetail(null))
      .finally(() => setDetailLoading(false));
  }, []);

  const filteredQuotes = marketFilter === "ALL"
    ? quotes
    : quotes.filter((q) => q.market === marketFilter);

  const tabs: { key: MarketFilter; label: string }[] = [
    { key: "ALL", label: "全部市场" },
    { key: "US", label: "美股" },
    { key: "JP", label: "日股" },
  ];

  return (
    <div className="app">
      <header className="header">
        <div className="header-left">
          <div className="logo">K</div>
          <h1>
            Kabu
            <small>智能股票监控平台</small>
          </h1>
        </div>
        <div className="connection-status">
          <div className={`status-dot ${connected ? "connected" : ""}`} />
          {connected ? "实时连接中" : "连接中..."}
        </div>
      </header>

      <div className="toolbar">
        <div className="market-tabs">
          {tabs.map((t) => (
            <button
              key={t.key}
              className={`tab ${marketFilter === t.key ? "active" : ""}`}
              onClick={() => setMarketFilter(t.key)}
            >
              {t.label}
            </button>
          ))}
        </div>
        <span className="stock-count">
          共追踪 {quotes.length} 支股票
        </span>
      </div>

      {selectedSymbol && detail && !detailLoading && (
        <PriceChart quote={detail.quote} history={detail.history} />
      )}

      <div className="main-layout">
        <div>
          {loading ? (
            <div className="stock-table-container">
              <div className="loading">
                <div className="spinner" />
                <p>正在获取股票数据...</p>
              </div>
            </div>
          ) : (
            <StockTable
              quotes={filteredQuotes}
              selectedSymbol={selectedSymbol}
              onSelect={handleSelect}
            />
          )}
        </div>

        <div className="right-panel">
          {!selectedSymbol && !detailLoading && (
            <div className="card">
              <div className="empty-state">
                <h3>选择一支股票</h3>
                <p>点击左侧表格中的股票，查看 AI 分析和交易策略</p>
              </div>
            </div>
          )}

          {detailLoading && (
            <div className="card">
              <div className="loading">
                <div className="spinner" />
                <p>正在分析 {selectedSymbol}...</p>
              </div>
            </div>
          )}

          {selectedSymbol && detail && !detailLoading && (
            <>
              <AnalysisPanel analysis={detail.analysis} currency={detail.quote.currency} />
              <StrategyPanel strategies={detail.strategies} currency={detail.quote.currency} />
            </>
          )}
        </div>
      </div>
    </div>
  );
}
