from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from routers import brvm, casablanca, ngx
import pathlib
 
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

# in case one directly execute it
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)