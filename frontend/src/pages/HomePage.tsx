import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import type { Market, StockQuote } from "../types";
import { useStockWebSocket } from "../hooks/useWebSocket";
import { getStocks } from "../services/api";
import { StockTable } from "../components/StockTable";

type MarketFilter = "ALL" | Market;

export function HomePage() {
  const [marketFilter, setMarketFilter] = useState<MarketFilter>("ALL");
  const [quotes, setQuotes] = useState<StockQuote[]>([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

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

  const handleSelect = (symbol: string) => {
    navigate(`/stock/${encodeURIComponent(symbol)}`);
  };

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
        <div className="header-right-group">
          <div className="nav-tabs">
            <button className="tab active">監視一覧</button>
            <button className="tab" onClick={() => navigate("/portfolio")}>保有証券</button>
          </div>
          <div className="connection-status">
            <div className={`status-dot ${connected ? "connected" : ""}`} />
            {connected ? "实时连接中" : "连接中..."}
          </div>
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
          selectedSymbol={null}
          onSelect={handleSelect}
        />
      )}
    </div>
  );
}
