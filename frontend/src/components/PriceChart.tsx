import { useEffect, useRef } from "react";
import { createChart, type IChartApi, type ISeriesApi, ColorType } from "lightweight-charts";
import type { HistoricalBar, StockQuote } from "../types";
import { formatPrice, formatPercent } from "../utils/format";

interface Props {
  quote: StockQuote;
  history: HistoricalBar[];
}

export function PriceChart({ quote, history }: Props) {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);

  useEffect(() => {
    if (!chartContainerRef.current) return;

    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: "transparent" },
        textColor: "#9ca3af",
      },
      grid: {
        vertLines: { color: "#1e293b" },
        horzLines: { color: "#1e293b" },
      },
      width: chartContainerRef.current.clientWidth,
      height: 320,
      crosshair: {
        mode: 0,
      },
      timeScale: {
        borderColor: "#2d3748",
      },
      rightPriceScale: {
        borderColor: "#2d3748",
      },
    });

    const series = chart.addCandlestickSeries({
      upColor: "#10b981",
      downColor: "#ef4444",
      borderUpColor: "#10b981",
      borderDownColor: "#ef4444",
      wickUpColor: "#10b981",
      wickDownColor: "#ef4444",
    });

    chartRef.current = chart;
    seriesRef.current = series;

    const handleResize = () => {
      if (chartContainerRef.current) {
        chart.applyOptions({ width: chartContainerRef.current.clientWidth });
      }
    };

    window.addEventListener("resize", handleResize);

    return () => {
      window.removeEventListener("resize", handleResize);
      chart.remove();
    };
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
        <div>
          <span className="chart-symbol">{quote.symbol}</span>
          <span style={{ marginLeft: 8, color: "var(--text-muted)", fontSize: 14 }}>
            {quote.name}
          </span>
        </div>
        <div>
          <span className="chart-price">{formatPrice(quote.current_price, quote.currency)}</span>
          <span className={`chart-change ${changeClass}`}>
            {formatPercent(quote.change_percent)}
          </span>
        </div>
      </div>
      <div ref={chartContainerRef} />
    </div>
  );
}
