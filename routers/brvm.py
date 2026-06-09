import httpx
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException
from bs4 import BeautifulSoup

router = APIRouter(prefix="/brvm", tags=["BRVM"])

SIKA = "https://www.sikafinance.com"
BRVMAX = "https://brvmax.com/api"
EPOCH = datetime(1970, 1, 1)
SUFFIX = {
    "Cote d'Ivoire": "ci",
    # TODO: check if this is "Ivory Coast" or if Cote d'Ivoire is accented
    # seems like it is fine asis
    "Senegal": "sn",
    "Benin": "bj",
    "Burkina Faso": "bf",
    "Mali": "ml",
    "Niger": "ne",
    "Togo": "tg",
    "Guinea-Bissau": "gw",
}
http = httpx.AsyncClient(timeout=15, headers={"User-Agent": "Mozilla/5.0"})

# Helpers for historical data
async def _token(symbol):
    r = await http.get(f"{SIKA}/marches/cotation_{symbol}")
    r.raise_for_status()
    soup = BeautifulSoup(r.text, 'html.parser')
    guid = soup.find('span', id='guid')
    if not guid:
        raise HTTPException(404, f"no token for {symbol}")
    return guid.text.replace(" ", "").replace("\n", "").strip()

async def _ticks(symbol, length, token):
    r = await http.get(f"{SIKA}/api/charting/GetTicksEOD", params={
        "symbol": symbol, "length": length, "period": 0, "guid": token,
    }, headers={
        "Referer": f"{SIKA}/marches/cotation_{symbol}",
        "Origin": SIKA,
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

async def _sika_history(sika_symbol, length):
    # shared helper so /index and /{symbol}/history don't repeat themselves
    try:
        token = await _token(sika_symbol)
        raw = await _ticks(sika_symbol, length, token)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(502, str(e))
    return _parse(raw)

# REST endpoints...
@router.get("/")
async def all_stocks():
    # live prices from brvmax
    try:
        r = await http.get(f"{BRVMAX}/stocks", params={"assetType": "stock"})
        r.raise_for_status()
    except Exception as e:
        raise HTTPException(502, str(e))
    stocks = [{
        "symbol": s["ticker"],
        "name": s.get("name"),
        "price": s.get("price"),
        "change_pct": s.get("changePercent"),
        "volume": s.get("volume"),
        "market_cap": s.get("marketCap"),
        "currency": "XOF",
        "country": s.get("country"),
        "sector": s.get("sector"),
    } for s in r.json()]
    return {"exchange": "BRVM", "count": len(stocks), "stocks": stocks}

@router.get("/market")
async def market_overview():
    # indices, market cap and the open/close status
    try:
        r = await http.get(f"{BRVMAX}/public/market-data")
        r.raise_for_status()
    except Exception as e:
        raise HTTPException(502, str(e))
    return r.json()["data"]

@router.get("/index")
async def brvm_index(length: int = 180):
    # composite index history as BRVMC has no country suffix on sikafinance
    history = await _sika_history("BRVMC", length)
    return {"symbol": "BRVMC", "count": len(history), "history": history}

@router.get("/{symbol}")
async def stock_detail(symbol: str):
    # live price from brvmax, same shape as the list endpoint
    symbol = symbol.upper()
    try:
        r = await http.get(f"{BRVMAX}/stocks", params={"assetType": "stock"})
        r.raise_for_status()
        stocks = r.json()
        stock = next((s for s in stocks if s["ticker"] == symbol), None)
        if not stock:
            raise HTTPException(404, f"{symbol} not found on BRVM")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(502, str(e))
    return {
        "symbol": symbol,
        "name": stock.get("name"),
        "price": stock.get("price"),
        "change_pct": stock.get("changePercent"),
        "volume": stock.get("volume"),
        "market_cap": stock.get("marketCap"),
        "currency": "XOF",
        "country": stock.get("country"),
        "sector": stock.get("sector"),
    }

@router.get("/{symbol}/history")
async def stock_history(symbol: str, length: int = 180):
    # historical OHLCV from sikafinance
    symbol = symbol.upper()

    # need the country to build the correct sikafinance symbol
    try:
        r = await http.get(f"{BRVMAX}/stocks", params={"assetType": "stock"})
        r.raise_for_status()
        stocks = r.json()
        stock = next((s for s in stocks if s["ticker"] == symbol), None)
        if not stock:
            raise HTTPException(404, f"{symbol} not found on BRVM")
        country = stock.get("country", "")
        suffix = SUFFIX.get(country, "ci")
        sika_symbol = f"{symbol}.{suffix}"
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(502, str(e))

    # error handling for fetching tokens and ticks
    history = await _sika_history(sika_symbol, length)
    return {"symbol": symbol, "count": len(history), "history": history}