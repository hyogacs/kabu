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
  const [loading, setLoading] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);

  const { quotes: wsQuotes, connected } = useStockWebSocket();

  // Initial fetch
  useEffect(() => {
    setLoading(true);
    getStocks()
      .then(setQuotes)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  // Update from WebSocket
  useEffect(() => {
    if (wsQuotes.length > 0) {
      setQuotes(wsQuotes);
    }
  }, [wsQuotes]);

  // Load detail when symbol selected
  const handleSelect = useCallback((symbol: string) => {
    setSelectedSymbol(symbol);
    setDetailLoading(true);
    getStockDetail(symbol)
      .then(setDetail)
      .catch(() => setDetail(null))
      .finally(() => setDetailLoading(false));
  }, []);

  // Filter quotes by market
  const filteredQuotes = marketFilter === "ALL"
    ? quotes
    : quotes.filter((q) => q.market === marketFilter);

  return (
    <div className="app">
      <header className="header">
        <h1>
          <span>Kabu</span> Stock Monitor
        </h1>
        <div className="connection-status">
          <div className={`status-dot ${connected ? "connected" : ""}`} />
          {connected ? "Live" : "Connecting..."}
        </div>
      </header>

      <div className="market-tabs">
        {(["ALL", "US", "JP"] as MarketFilter[]).map((m) => (
          <button
            key={m}
            className={`tab ${marketFilter === m ? "active" : ""}`}
            onClick={() => setMarketFilter(m)}
          >
            {m === "ALL" ? "All Markets" : m === "US" ? "US Stocks" : "JP Stocks"}
          </button>
        ))}
        <div style={{ marginLeft: "auto", fontSize: 12, color: "var(--text-muted)", alignSelf: "center" }}>
          {quotes.length} stocks tracked
        </div>
      </div>

      {selectedSymbol && detail && !detailLoading && (
        <PriceChart quote={detail.quote} history={detail.history} />
      )}

      <div className="main-layout">
        <div>
          <StockTable
            quotes={filteredQuotes}
            selectedSymbol={selectedSymbol}
            onSelect={handleSelect}
          />
        </div>

        <div className="right-panel">
          {!selectedSymbol && (
            <div className="empty-state">
              <h3>Select a Stock</h3>
              <p>Click on any stock in the table to view AI analysis and trading strategies.</p>
            </div>
          )}

          {detailLoading && (
            <div className="loading">
              <div className="spinner" />
              <p style={{ marginTop: 12 }}>Analyzing {selectedSymbol}...</p>
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
