import httpx
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException
from bs4 import BeautifulSoup

router = APIRouter(prefix="/brvm", tags=["BRVM"])
BASE = "https://www.sikafinance.com"
EPOCH = datetime(1970, 1, 1)
http = httpx.AsyncClient(timeout=15, headers={"User-Agent": "Mozilla/5.0"})

async def _token(symbol):
    r = await http.get(f"{BASE}/marches/cotation_{symbol}")
    r.raise_for_status()
    soup = BeautifulSoup(r.text, 'html.parser')
    guid = soup.find('span', id='guid')
    if not guid:
        raise HTTPException(404, f"no token for {symbol}")
    return guid.text.replace(" ", "").replace("\n", "").strip()

async def _ticks(symbol, length, token):
    r = await http.get(f"{BASE}/api/charting/GetTicksEOD", params={
        "symbol": symbol, "length": length, "period": 0, "guid": token,
    }, headers={
        "Referer": f"{BASE}/marches/cotation_{symbol}",
        "Origin": BASE,
        "X-Requested-With": "XMLHttpRequest",
    })
    r.raise_for_status()
    data = r.json()
    if not data or "QuoteTab" not in data:
        raise HTTPException(502, f"bad response for {symbol}")
    return data

def _parse(data):
    out = []
    for t in data.get("QuoteTab", []):
        try:
            out.append({
                "date": (EPOCH + timedelta(days=int(t["d"]))).strftime("%Y-%m-%d"),
                "open": float(t["o"]),
                "high": float(t["h"]),
                "low": float(t["l"]),
                "close": float(t["c"]),
                "volume": int(t["v"]),
                "currency": "XOF",
            })
        except (KeyError, ValueError):
            continue
    return out

@router.get("/brvm/{symbol}")
async def ticker_history(symbol: str, length: int = 180):
    symbol = symbol.upper()
    try:
        token = await _token(symbol)
        raw = await _ticks(symbol, length, token)
    except Exception as e:
        raise HTTPException(502, str(e))
    quotes = _parse(raw)
    return {
        "symbol": symbol,
        "name": raw.get("Name", symbol).strip(),
        "count": len(quotes),
        "quotes": quotes,
    }