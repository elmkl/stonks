import httpx
from fastapi import APIRouter, HTTPException
from utils import find, _float

router = APIRouter(prefix="/cse", tags=["Casablanca"])

BASE = "https://www.casablanca-bourse.com"
http = httpx.AsyncClient(
    timeout=15,
    # SSL chain is misconfigured so we remove this for now
    verify=False,
    headers={
        "User-Agent": "Mozilla/5.0",
        "Referer": f"{BASE}/fr/live-market/equities",
    },
)

def _parse(data):
    out = []
    for a in data.get("data", {}).get("values", []):
        try:
            out.append({
                "symbol": a.get("ticker", "?"),
                "name": a.get("label", "?"),
                "sector": a.get("sous_secteur", "?"),
                "price": _float(a.get("field_cours_courant")),
                "open": _float(a.get("field_opening_price")),
                "high": _float(a.get("field_high_price")),
                "low": _float(a.get("field_low_price")),
                "previous_close": _float(a.get("field_closing_price")),
                "volume_shares": int(_float(a.get("field_cumul_titres_echanges"))),
                "volume_value": _float(a.get("field_cumul_volume_echange")),
                "change_pct": _float(a.get("field_var_veille")),
                "last_traded": a.get("field_last_traded_time", ""),
                "status": a.get("field_etat_cot_val", "-"),
                "currency": "MAD",
            })
        except (KeyError, ValueError):
            continue
    return out

async def _fetch():
    try:
        r = await http.get(f"{BASE}/api/proxy/fr/api/bourse/dashboard/ticker", params={
            "marche": 59, "class[0]": 25,
        })
        r.raise_for_status()
    except Exception as e:
        raise HTTPException(502, str(e))
    data = r.json()
    if "data" not in data or "values" not in data.get("data", {}):
        raise HTTPException(502, "bad response from casablanca bourse")
    return _parse(data)

@router.get("/")
async def all_equities():
    quotes = await _fetch()
    return {"exchange": "CSE", "count": len(quotes), "quotes": quotes}

@router.get("/{symbol}")
async def equity(symbol: str):
    quotes = await _fetch()
    match = find(quotes, "symbol", symbol)
    if not match:
        raise HTTPException(404, f"{symbol} not found on CSE")
    return match