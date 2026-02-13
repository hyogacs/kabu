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
        <div className="empty-state" style={{ padding: 40 }}>
          <h3>暂无数据</h3>
          <p>未能获取到股票数据，请检查网络连接</p>
        </div>
      </div>
    );
  }

  return (
    <div className="stock-table-container">
      <table className="stock-table">
        <thead>
          <tr>
            <th>市场</th>
            <th>股票代码</th>
            <th>最新价</th>
            <th>涨跌额</th>
            <th>涨跌幅</th>
            <th>成交量</th>
            <th>最高</th>
            <th>最低</th>
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
                <td className={`price-cell ${changeClass}`}>
                  {isPositive ? "+" : ""}
                  {q.currency === "JPY" ? q.change.toFixed(0) : q.change.toFixed(2)}
                </td>
                <td className={`price-cell ${changeClass}`}>{formatPercent(q.change_percent)}</td>
                <td className="volume-cell">{formatVolume(q.volume)}</td>
                <td className="volume-cell">{formatPrice(q.day_high, q.currency)}</td>
                <td className="volume-cell">{formatPrice(q.day_low, q.currency)}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
