"""Portfolio holding models."""

from pydantic import BaseModel


class StockHolding(BaseModel):
    code: str
    name: str
    quantity: int
    order_pending: int | None = None
    cost_price: float
    current_price: float
    cost_total: float
    market_value: float
    unrealized_pnl: float


class FundHolding(BaseModel):
    name: str
    units: str  # e.g. "30704口"
    order_pending: int | None = None
    cost_price: float
    nav: float  # 基準価額
    cost_total: float
    market_value: float
    unrealized_pnl: float
    distribution_method: str  # 分配金受取方法


class BondHolding(BaseModel):
    name: str
    coupon_rate: float
    maturity_date: str
    coupon_dates: str
    face_value: float
    cost_price: float
    market_value: float


class HoldingCategory(BaseModel):
    category_name: str
    total_market_value: float
    total_pnl: float | None = None
    stocks: list[StockHolding] | None = None
    funds: list[FundHolding] | None = None
    bonds: list[BondHolding] | None = None


class Portfolio(BaseModel):
    categories: list[HoldingCategory]
    total_market_value: float
    total_cost: float
    total_pnl: float
