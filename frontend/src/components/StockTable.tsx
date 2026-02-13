import type { StockQuote } from "../types";
import { formatPrice, formatVolume, formatPercent } from "../utils/format";

interface Props {
  quotes: StockQuote[];
  selectedSymbol: string | null;
  onSelect: (symbol: string) => void;
}

export function StockTable({ quotes, selectedSymbol, onSelect }: Props) {
  if (!quotes.length) {
    return (
      <div className="stock-table-container">
        <div className="loading">
          <div className="spinner" />
          <p style={{ marginTop: 12 }}>Loading stock data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="stock-table-container">
      <table className="stock-table">
        <thead>
          <tr>
            <th>Market</th>
            <th>Symbol</th>
            <th>Price</th>
            <th>Change</th>
            <th>Change %</th>
            <th>Volume</th>
            <th>High</th>
            <th>Low</th>
          </tr>
        </thead>
        <tbody>
          {quotes.map((q) => {
            const isPositive = q.change >= 0;
            const changeClass = isPositive ? "change-positive" : "change-negative";
            return (
              <tr
                key={q.symbol}
                className={q.symbol === selectedSymbol ? "selected" : ""}
                onClick={() => onSelect(q.symbol)}
              >
                <td>
                  <span className={`market-badge ${q.market}`}>{q.market}</span>
                </td>
                <td>
                  <div className="symbol-cell">{q.symbol}</div>
                  <div className="name-cell">{q.name}</div>
                </td>
                <td className="price-cell">{formatPrice(q.current_price, q.currency)}</td>
                <td className={changeClass}>
                  {isPositive ? "+" : ""}
                  {q.currency === "JPY" ? q.change.toFixed(0) : q.change.toFixed(2)}
                </td>
                <td className={changeClass}>{formatPercent(q.change_percent)}</td>
                <td className="volume-cell">{formatVolume(q.volume)}</td>
                <td className="price-cell" style={{ fontSize: 12, color: "var(--text-secondary)" }}>
                  {formatPrice(q.day_high, q.currency)}
                </td>
                <td className="price-cell" style={{ fontSize: 12, color: "var(--text-secondary)" }}>
                  {formatPrice(q.day_low, q.currency)}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
