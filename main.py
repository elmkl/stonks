from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import brvm

app = FastAPI(title="stonks", description="EOD aggregator for African stock exchanges", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(brvm.router)

@app.get("/")
async def root():
    return {"name": "stonks", "version": "0.1.0", "exchanges": ["brvm", "casablanca", "ngx"], "humans": "please go on /portal"}

# TODO: add /portal