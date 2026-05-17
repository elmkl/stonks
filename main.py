from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

# models
class Stock(BaseModel):
    ticker: str = Field(..., description="stock ticker symbol")
    exchange: str = Field(..., description="exchange acronym (e.g., JSE, BRVM, CSE)")
    price: float
    currency: str
    timestamp: datetime
    volume: Optional[int] = None

class ErrorResponse(BaseModel):
    detail: str

# fastapi scaffolding
app = FastAPI(
    title="stonks API",
    description="EOD aggregator for African stock exchanges",
    version="0.1.0"
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)