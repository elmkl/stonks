import httpx
from fastapi import APIRouter, HTTPException
from utils import find, _float

router = APIRouter(prefix="/cse", tags=["Casablanca"])

# cdgcapitalbourse.ma is CDG Capital Bourse's terminal API so we are using that instead of CSE
BASE = "https://www.cdgcapitalbourse.ma/api/"
http = httpx.AsyncClient(timeout=15, headers={"User-Agent": "Mozilla/5.0"})

def _action(name, params):
    # build a single action block for the POST body
    return {
        "ACTION": {"NAME": name, "TYPE": "SELECT", "VALUE": name},
        "PARAMS": [
            {"NAME": k, "TYPE": "S" if isinstance(v, str) else "I", "VALUE": v}
            for k, v in params.items()
        ]
    }

# for the POST requests
async def _post(*actions):
    try:
        r = await http.post(BASE, json={"ACTIONS": list(actions)})
        r.raise_for_status()
    except Exception as e:
        raise HTTPException(502, str(e))
    return r.json()

def _sparkline(data_chart):
    # DataChart format: "35.50;35.60;...;32.00|R" where R/G/N is trend color
    if not data_chart:
        return []
    try:
        return [float(x) for x in data_chart.split("|")[0].split(";") if x]
    except ValueError:
        return []

def _parse_stocks(data):
    out = []
    for s in data:
        try:
            out.append({
                "symbol": s["Symbol"],
                "name": s["Libelle"],
                "price": _float(s.get("DernierCours")),
                "open": _float(s.get("Ouverture")),
                "high": _float(s.get("PlusHaut")),
                "low": _float(s.get("PlusBas")),
                "change_pct": _float(s.get("Variation")),
                "volume": int(_float(s.get("QteEchangee"))),
                "market_cap": _float(s.get("Capitalisation")),
                "currency": "MAD",
                "country": "Morocco",
                "last_trade": s.get("DateDernierCours"),
                "status": s.get("Statut"),
                "sparkline": _sparkline(s.get("DataChart")),
            })
        except (KeyError, ValueError):
            continue
    return out

# output all the equities
@router.get("/")
async def all_equities():
    res = await _post(_action("PALMARES-STOCKS", {
        "Lang_": "fr", "TypeStocks_": 1, "IdPartener_": 1,
        "TypeOrder_": "volume", "Frequence_": "D", "Nbr_": 1,
    }))
    stocks = _parse_stocks(res[0]["PALMARES-STOCKS"]["Data"])
    return {"exchange": "CSE", "count": len(stocks), "stocks": stocks}

@router.get("/market")
async def market():
    # MASI + market status + volume summary
    # This is all in one request, pretty cool right?
    res = await _post(
        _action("INDICE-SYNTHESE", {"Lang_": "fr", "Espace_": 1, "IdPartener_": 1, "Indice_": "MASI"}),
        _action("MARKET-STATUS", {"Lang_": "fr", "Espace_": 1, "IdPartener_": 1, "NumSeq_": 0}),
        _action("MARKET", {"Lang_": "fr", "Espace_": 1, "Type_": "M"}),
    )
    masi = res[0]["INDICE-SYNTHESE"]["Data"][0]
    status = res[1]["MARKET-STATUS"]["Data"][0]
    summary = res[2]["MARKET"]["Data"][0]
    return {
        "index": "MASI",
        "value": masi["Cours"],
        "change_pct": masi["VariationP"],
        "change_val": masi["VariationV"],
        "open": masi["CoursOuverture"],
        "high": masi["PlusHaut"],
        "low": masi["PlusBas"],
        "52w_high": masi["PlusHautAnnee"],
        "52w_low": masi["PlusBasAnnee"],
        "market_cap": masi["Capitalisation"],
        "advances": masi["NbrHausse"],
        "declines": masi["NbrBaisse"],
        "unchanged": masi["NbrInchange"],
        "volume": summary["Volumes"],
        "status": status["Statut"],
        "as_of": status["Horlogue"],
    }

@router.get("/commodities")
async def commodities():
    res = await _post(_action("COMMODITIES", {"Lang_": "fr", "Espace_": 1, "IdPartener_": 1}))
    return res[0]["COMMODITIES"]["Data"]

@router.get("/metals")
async def metals():
    res = await _post(_action("METALS", {"Lang_": "fr", "Espace_": 1}))
    return res[0]["METALS"]["Data"]

@router.get("/indices")
async def international_indices():
    res = await _post(_action("INDICE-INTERNATIONAL", {"Lang_": "fr", "Espace_": 1}))
    return res[0]["INDICE-INTERNATIONAL"]["Data"]

@router.get("/currencies")
async def currencies():
    res = await _post(_action("CURRENCIES", {"Lang_": "fr", "Espace_": 1, "IdPartener_": 1}))
    return res[0]["CURRENCIES"]["Data"]

@router.get("/agenda")
async def agenda():
    # upcoming events
    res = await _post(_action("AGENDA", {"Lang_": "fr", "Espace_": 1, "IdPartener_": 1, "Top_": 10}))
    return res[0]["AGENDA"]["Data"]

@router.get("/{symbol}")
async def equity(symbol: str):
    res = await _post(_action("PALMARES-STOCKS", {
        "Lang_": "fr", "TypeStocks_": 1, "IdPartener_": 1,
        "TypeOrder_": "volume", "Frequence_": "D", "Nbr_": 1,
    }))
    stocks = _parse_stocks(res[0]["PALMARES-STOCKS"]["Data"])
    match = find(stocks, "symbol", symbol)
    if not match:
        raise HTTPException(404, f"{symbol} not found on CSE")
    return match

@router.get("/{symbol}/history")
async def equity_history(symbol: str):
    res = await _post(_action("VALEUR-GRAPH-APPL", {"Lang_": "fr", "Espace_": 1, "Symbol_": symbol}))
    return res[0]["VALEUR-GRAPH-APPL"]["Data"]

@router.get("/{symbol}/intraday")
async def equity_intraday(symbol: str):
    res = await _post(_action("VALEUR-INTRA", {"Lang_": "XX", "Espace_": 1, "symbol_": symbol}))
    return res[0]["VALEUR-INTRA"]["Data"]