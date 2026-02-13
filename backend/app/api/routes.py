"""API routes for the stock monitoring application."""

import logging

from fastapi import APIRouter, HTTPException, Query

from app.core.config import settings
from app.models.stock import (
    AIAnalysis,
    HistoricalBar,
    Market,
    StockDetail,
    StockQuote,
    TradingStrategy,
)
from app.services.ai_analyzer import ai_analyzer
from app.services.stock_data import fetch_history, fetch_quote, fetch_quotes
from app.strategies.strategy_engine import strategy_engine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")


@router.get("/health")
async def health_check():
    return {"status": "ok", "version": settings.APP_VERSION}


@router.get("/stocks", response_model=list[StockQuote])
async def get_stocks(
    market: Market | None = None,
    symbols: str | None = Query(None, description="Comma-separated symbols"),
):
    """Get real-time quotes for stocks."""
    if symbols:
        symbol_list = [s.strip().upper() for s in symbols.split(",")]
    elif market == Market.US:
        symbol_list = settings.DEFAULT_US_STOCKS
    elif market == Market.JP:
        symbol_list = settings.DEFAULT_JP_STOCKS
    else:
        symbol_list = settings.DEFAULT_US_STOCKS + settings.DEFAULT_JP_STOCKS

    quotes = fetch_quotes(symbol_list)
    if not quotes:
        raise HTTPException(status_code=503, detail="Unable to fetch stock data")
    return quotes


@router.get("/stocks/{symbol}", response_model=StockQuote)
async def get_stock(symbol: str):
    """Get real-time quote for a single stock."""
    quote = fetch_quote(symbol.upper())
    if not quote:
        raise HTTPException(status_code=404, detail=f"Stock {symbol} not found")
    return quote


@router.get("/stocks/{symbol}/history", response_model=list[HistoricalBar])
async def get_stock_history(
    symbol: str,
    period: str = Query("6mo", description="1mo, 3mo, 6mo, 1y, 2y, 5y"),
    interval: str = Query("1d", description="1d, 1wk, 1mo"),
):
    """Get historical OHLCV data."""
    history = fetch_history(symbol.upper(), period=period, interval=interval)
    if not history:
        raise HTTPException(
            status_code=404, detail=f"No history found for {symbol}"
        )
    return history


@router.get("/analysis/{symbol}", response_model=AIAnalysis)
async def get_analysis(symbol: str):
    """Get AI-powered buy/sell analysis for a stock."""
    analysis = ai_analyzer.analyze(symbol.upper())
    if not analysis:
        raise HTTPException(
            status_code=404, detail=f"Unable to analyze {symbol}"
        )
    return analysis


@router.get("/strategies/{symbol}", response_model=list[TradingStrategy])
async def get_strategies(symbol: str):
    """Get trading strategies for a stock."""
    strategies = strategy_engine.generate_strategies(symbol.upper())
    if not strategies:
        raise HTTPException(
            status_code=404, detail=f"Unable to generate strategies for {symbol}"
        )
    return strategies


@router.get("/stocks/{symbol}/detail", response_model=StockDetail)
async def get_stock_detail(symbol: str):
    """Get comprehensive stock detail including quote, analysis, and strategies."""
    symbol = symbol.upper()

    quote = fetch_quote(symbol)
    if not quote:
        raise HTTPException(status_code=404, detail=f"Stock {symbol} not found")

    analysis = ai_analyzer.analyze(symbol)
    if not analysis:
        raise HTTPException(
            status_code=404, detail=f"Unable to analyze {symbol}"
        )

    strategies = strategy_engine.generate_strategies(symbol)
    history = fetch_history(symbol, period="6mo")

    return StockDetail(
        quote=quote,
        indicators=analysis.indicators,
        analysis=analysis,
        strategies=strategies,
        history=history,
    )


@router.get("/watchlist/default")
async def get_default_watchlist():
    """Get default watchlist symbols."""
    return {
        "us": settings.DEFAULT_US_STOCKS,
        "jp": settings.DEFAULT_JP_STOCKS,
    }
