from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from routers import brvm, casablanca, ngx
from routers.brvm import all_stocks as brvm_stocks
from routers.casablanca import all_equities as cse_stocks
from routers.ngx import all_equities as ngx_stocks
import pathlib
import asyncio
 
app = FastAPI(title="stonks", description="EOD aggregator for African stock exchanges", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# routers
app.include_router(brvm.router)
app.include_router(casablanca.router)
app.include_router(ngx.router)

# main page
@app.get("/")
async def root():
    return {
        "name": "stonks",
        "version": "0.1.0",
        "exchanges": ["brvm", "cse", "ngx"],
        "humans": "please go on /portal",
        "docs": "/docs",
    }

# portal for human users
@app.get("/portal", response_class=HTMLResponse)
async def portal():
    path = pathlib.Path(__file__).parent / "portal.html"
    return path.read_text()

# search across all exchanges
@app.get("/search")
async def search(q: str):
    q = q.lower().strip()
    brvm_data, cse_data, ngx_data = await asyncio.gather(
        brvm_stocks(),
        cse_stocks(),
        ngx_stocks(),
        return_exceptions=True
    )

    results = []
    exchanges = [
        (brvm_data, "BRVM", "stocks"),
        (cse_data, "CSE", "quotes"),
        (ngx_data, "NGX", "stocks"),
    ]

    for data, exchange, key in exchanges:
        # if theres an error fetching data 
        if isinstance(data, Exception):
            continue
        # fetch stocks and see if they compare (case insesntitive)
        for stock in data.get(key, []):
            symbol = (stock.get("symbol") or stock.get("ticker") or "").lower()
            name = (stock.get("name") or "").lower()
            if q in symbol or q in name:
                results.append({**stock, "exchange": exchange})
    # there can be multiple results...
    return {"query": q, "count": len(results), "results": results}

# in case one directly execute it
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)