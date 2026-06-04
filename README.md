# stonks
EOD (end of day) aggregator for African stock exchanges. Because everyone deserves the right to (basically) gamble!!

## exchanges
 
| exchange | country | endpoint |
|---|---|---|---|
| BRVM | West Africa (XOF) | `/brvm` |
| CSE | Morocco (MAD) | `/cse` |
| NGX | Nigeria (NGN) | `/ngx` |

## setup
 
```bash
pip install -r requirements.txt
uvicorn main:app --reload
```
 
Documentation via swagger will be available at `http://localhost:8000/docs`  
whilst a portal at `http://localhost:8000/portal`

## endpoints
 
```
- BRVM (West African market)
GET /brvm/              all BRVM stocks, live prices
GET /brvm/market        composite index, market cap, and open/close status
GET /brvm/index         BRVM composite 180-day history
GET /brvm/{symbol}      single ticker OHLCV history
 
- CSE (Casablanca Stock Exchange)
GET /cse/               all the Casablanca Stock Exchange (CSE) equities, live
GET /cse/{symbol}       single stock

- NGX (Nigeria Stock EXchange)
GET /ngx/               all NGX equities, live
GET /ngx/bonds          all NGX bonds
GET /ngx/etfs           all NGX ETFs
GET /ngx/{symbol}       single stock
```
 
## adding an exchange?
 
1. create `routers/yourexchange.py` with an `APIRouter`
2. add `app.include_router(yourexchange.router)` in `main.py`
3. add to the `exchanges` list in your root endpoint

# Things for the future
Add graphs/visualizer and more exchanges