import httpx
from fastapi import APIRouter, HTTPException
from utils import find

BASE = "https://doclib.ngxgroup.com/REST/api/statistics"
router = APIRouter(prefix="/ngx", tags=["Nigeria"])
http = httpx.AsyncClient(timeout=15, headers={"User-Agent": "Mozilla/5.0"})

async def _fetch(ticker_type):
    try:
        r = await http.get(f"{BASE}/ticker", params={
            "$filter": f"TickerType eq '{ticker_type}'",
        })
        r.raise_for_status()
    except Exception as e:
        raise HTTPException(502, str(e))
    raw = r.json()
    return [{
        "symbol": t["SYMBOL"].strip(),
        "price": t["Value"],
        "change_pct": t["PercChange"],
        "type": t["TickerType"].lower(),
        "currency": "NGN",
    } for t in raw]

@router.get("/")
async def all_equities():
    stocks = await _fetch("EQUITIES")
    return {"exchange": "NGX", "count": len(stocks), "stocks": stocks}

@router.get("/bonds")
async def all_bonds():
    bonds = await _fetch("BONDS")
    return {"exchange": "NGX", "count": len(bonds), "bonds": bonds}

@router.get("/etfs")
async def all_etfs():
    etfs = await _fetch("ETPS")
    return {"exchange": "NGX", "count": len(etfs), "etfs": etfs}

@router.get("/{symbol}")
async def equity(symbol: str):
    stocks = await _fetch("EQUITIES")
    match = find(stocks, "symbol", symbol)
    if not match:
        raise HTTPException(404, f"{symbol} not found on NGX")
    return match