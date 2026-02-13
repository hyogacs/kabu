export function formatPrice(price: number, currency: string): string {
  if (currency === "JPY") {
    return `¥${price.toLocaleString("ja-JP", { maximumFractionDigits: 0 })}`;
  }
  return `$${price.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

export function formatVolume(volume: number): string {
  if (volume >= 1_000_000_000) return `${(volume / 1_000_000_000).toFixed(1)}B`;
  if (volume >= 1_000_000) return `${(volume / 1_000_000).toFixed(1)}M`;
  if (volume >= 1_000) return `${(volume / 1_000).toFixed(1)}K`;
  return volume.toString();
}

export function formatPercent(value: number): string {
  const sign = value >= 0 ? "+" : "";
  return `${sign}${value.toFixed(2)}%`;
}

export function formatNumber(value: number | null | undefined, decimals = 2): string {
  if (value == null) return "-";
  return value.toFixed(decimals);
}

export function signalLabel(signal: string): string {
  const labels: Record<string, string> = {
    STRONG_BUY: "Strong Buy",
    BUY: "Buy",
    HOLD: "Hold",
    SELL: "Sell",
    STRONG_SELL: "Strong Sell",
  };
  return labels[signal] ?? signal;
}

export function signalLabelJa(signal: string): string {
  const labels: Record<string, string> = {
    STRONG_BUY: "Strong Buy",
    BUY: "Buy",
    HOLD: "Hold",
    SELL: "Sell",
    STRONG_SELL: "Strong Sell",
  };
  return labels[signal] ?? signal;
}
