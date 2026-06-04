from typing import Optional
from pydantic import BaseModel

class Quote(BaseModel):
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    currency: str = "XOF" # perhaps default should be MAD :D

class Stock(BaseModel):
    symbol: str
    name: Optional[str]
    price: float
    change_pct: float
    volume: Optional[int]
    market_cap: Optional[float]
    currency: str
    country: Optional[str]
    sector: Optional[str]