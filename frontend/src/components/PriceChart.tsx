import { useEffect, useRef } from "react";
import { createChart, type IChartApi, type ISeriesApi, ColorType } from "lightweight-charts";
import type { HistoricalBar, StockQuote } from "../types";
import { formatPrice, formatPercent } from "../utils/format";

interface Props {
  quote: StockQuote;
  history: HistoricalBar[];
}

export function PriceChart({ quote, history }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    const chart = createChart(containerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: "transparent" },
        textColor: "#64748b",
        fontFamily: "'Inter', sans-serif",
      },
      grid: {
        vertLines: { color: "#1e293b" },
        horzLines: { color: "#1e293b" },
      },
      width: containerRef.current.clientWidth,
      height: 340,
      crosshair: { mode: 0 },
      timeScale: { borderColor: "#1e293b" },
      rightPriceScale: { borderColor: "#1e293b" },
    });

    const series = chart.addCandlestickSeries({
      upColor: "#22c55e",
      downColor: "#ef4444",
      borderUpColor: "#22c55e",
      borderDownColor: "#ef4444",
      wickUpColor: "#22c55e",
      wickDownColor: "#ef4444",
    });

    chartRef.current = chart;
    seriesRef.current = series;

    const handleResize = () => {
      if (containerRef.current) {
        chart.applyOptions({ width: containerRef.current.clientWidth });
      }
    };
    window.addEventListener("resize", handleResize);
    return () => { window.removeEventListener("resize", handleResize); chart.remove(); };
  }, []);

  useEffect(() => {
    if (!seriesRef.current || !history.length) return;
    const data = history.map((bar) => ({
      time: bar.date as string,
      open: bar.open,
      high: bar.high,
      low: bar.low,
      close: bar.close,
    }));
    seriesRef.current.setData(data as any);
    chartRef.current?.timeScale().fitContent();
  }, [history]);

  const isPositive = quote.change >= 0;
  const changeClass = isPositive ? "change-positive" : "change-negative";

  return (
    <div className="chart-container">
      <div className="chart-header">
        <div className="chart-info">
          <span className="chart-symbol">{quote.symbol}</span>
          <span className="chart-name">{quote.name}</span>
        </div>
        <div className="chart-price-group">
          <div className="chart-price">{formatPrice(quote.current_price, quote.currency)}</div>
          <div className={`chart-change ${changeClass}`}>
            {isPositive ? "+" : ""}{quote.currency === "JPY" ? quote.change.toFixed(0) : quote.change.toFixed(2)}
            {" "}({formatPercent(quote.change_percent)})
          </div>
        </div>
      </div>
      <div ref={containerRef} />
    </div>
  );
}
