import type { StockQuote, StockDetail, AIAnalysis, TradingStrategy, HistoricalBar, Market } from "../types";

const BASE_URL = "/api";

async function fetchJSON<T>(url: string): Promise<T> {
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export async function getStocks(market?: Market, symbols?: string[]): Promise<StockQuote[]> {
  const params = new URLSearchParams();
  if (market) params.set("market", market);
  if (symbols?.length) params.set("symbols", symbols.join(","));
  const qs = params.toString();
  return fetchJSON(`${BASE_URL}/stocks${qs ? `?${qs}` : ""}`);
}

export async function getStockDetail(symbol: string): Promise<StockDetail> {
  return fetchJSON(`${BASE_URL}/stocks/${symbol}/detail`);
}

export async function getAnalysis(symbol: string): Promise<AIAnalysis> {
  return fetchJSON(`${BASE_URL}/analysis/${symbol}`);
}

export async function getStrategies(symbol: string): Promise<TradingStrategy[]> {
  return fetchJSON(`${BASE_URL}/strategies/${symbol}`);
}

export async function getHistory(symbol: string, period = "6mo"): Promise<HistoricalBar[]> {
  return fetchJSON(`${BASE_URL}/stocks/${symbol}/history?period=${period}`);
}
